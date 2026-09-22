import customtkinter as ctk
import requests
import threading
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class TTSClientApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TTS Creator Studio - PC Client")
        self.geometry("1000x650") 

        self.grid_columnconfigure(0, weight=5) 
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(0, weight=1)

       
        # Listas Globais de Vozes - Nativas e Multilíngues (Compatíveis com PT)
        self.vozes_fem = [
            # Nativas
            "pt-BR-FranciscaNeural", 
            "pt-BR-ThalitaMultilingualNeural",
            "pt-PT-RaquelNeural", # Sotaque de Portugal
            # Multilíngues Globais
            "de-DE-SeraphinaMultilingualNeural", # Alemã
            "en-US-AvaMultilingualNeural",       # Americana
            "en-US-EmmaMultilingualNeural",      # Americana
            "fr-FR-VivienneMultilingualNeural"   # Francesa
        ]
        
        self.vozes_masc = [
            # Nativos
            "pt-BR-AntonioNeural",
            "pt-PT-DuarteNeural", # Sotaque de Portugal
            # Multilíngues Globais
            "de-DE-FlorianMultilingualNeural",   # Alemão
            "en-AU-WilliamMultilingualNeural",   # Australiano
            "en-US-AndrewMultilingualNeural",    # Americano
            "en-US-BrianMultilingualNeural",     # Americano
            "fr-FR-RemyMultilingualNeural",      # Francês
            "it-IT-GiuseppeMultilingualNeural",  # Italiano
            "ko-KR-HyunsuMultilingualNeural"     # Coreano
        ]
        
        self.todas_vozes = self.vozes_fem + self.vozes_masc
        self.opcoes_pitch = ["+0Hz", "+15Hz", "-15Hz", "+25Hz", "-25Hz", "+40Hz", "-40Hz"]

        # Dicionário para guardar as referências dos formulários: {"DAVI": {"voz": widget, "pitch": widget}}
        self.personagens_widgets = {}

        # ================= PAINEL ESQUERDO: Personagens (Dinâmico) =================
        self.frame_config = ctk.CTkFrame(self)
        self.frame_config.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.frame_config, text="⚙️ Elenco (Vozes e Tons)", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Painel rolável que vai receber os formulários
        self.frame_lista_vozes = ctk.CTkScrollableFrame(self.frame_config)
        self.frame_lista_vozes.pack(padx=10, pady=10, fill="both", expand=True)

        # ================= PAINEL DIREITO: Roteiro =================
        self.frame_roteiro = ctk.CTkFrame(self)
        self.frame_roteiro.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(self.frame_roteiro, text="📝 Roteiro (NOME: Fala)", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.caixa_roteiro = ctk.CTkTextbox(self.frame_roteiro, height=300)
        self.caixa_roteiro.pack(padx=10, pady=10, fill="both", expand=True)
        self.caixa_roteiro.insert("0.0", "DAVI: Oi, testando a interface nova!\nJULIANA: Olha que incrível esse formulário visual.\nPOLICIAL: Mãos ao alto, parados!")

        # Botões de Ação
        self.btn_auto_config = ctk.CTkButton(self.frame_roteiro, text="🪄 Extrair Personagens do Roteiro", command=self.auto_configurar_personagens, fg_color="#2b8a3e", hover_color="#2f9e44", height=35)
        self.btn_auto_config.pack(pady=(0, 10))

        self.btn_gerar = ctk.CTkButton(self.frame_roteiro, text="🎙️ Solicitar Áudio à API", command=self.iniciar_requisicao, height=40)
        self.btn_gerar.pack(pady=10)

        self.label_status = ctk.CTkLabel(self.frame_roteiro, text="Pronto para edição.", text_color="gray")
        self.label_status.pack(pady=5)

    def adicionar_personagem_ui(self, nome, voz_padrao, pitch_padrao):
        """Cria uma nova linha de formulário visual para um personagem"""
        if nome in self.personagens_widgets:
            return # Já existe na tela

        row_frame = ctk.CTkFrame(self.frame_lista_vozes)
        row_frame.pack(fill="x", pady=5, padx=2)
        
        # Nome do Personagem
        lbl_nome = ctk.CTkLabel(row_frame, text=nome, width=80, anchor="w", font=("Arial", 12, "bold"))
        lbl_nome.pack(side="left", padx=10)
        
        # Dropdown de Voz
        cmb_voz = ctk.CTkOptionMenu(row_frame, values=self.todas_vozes, width=170)
        cmb_voz.set(voz_padrao)
        cmb_voz.pack(side="left", padx=5)
        
        # Dropdown de Pitch
        cmb_pitch = ctk.CTkOptionMenu(row_frame, values=self.opcoes_pitch, width=80)
        cmb_pitch.set(pitch_padrao)
        cmb_pitch.pack(side="left", padx=5)

        # Botão Remover
        btn_remover = ctk.CTkButton(row_frame, text="X", width=30, fg_color="#c92a2a", hover_color="#e03131",
                                    command=lambda: self.remover_personagem(nome, row_frame))
        btn_remover.pack(side="right", padx=10)
        
        # Salva as referências para lermos depois
        self.personagens_widgets[nome] = {"voz": cmb_voz, "pitch": cmb_pitch}

    def remover_personagem(self, nome, row_frame):
        """Destrói o elemento visual e remove do dicionário"""
        row_frame.destroy()
        if nome in self.personagens_widgets:
            del self.personagens_widgets[nome]

    def auto_configurar_personagens(self):
        texto_roteiro = self.caixa_roteiro.get("0.0", "end").strip().split('\n')
        
        # Busca quem está no texto
        personagens_roteiro = []
        for linha in texto_roteiro:
            if ':' in linha:
                nome = linha.split(':')[0].strip().upper()
                if nome not in personagens_roteiro:
                    personagens_roteiro.append(nome)
                    
        # Conta as vozes já escolhidas na interface para continuar a lógica heurística
        qtd_fem = sum(1 for w in self.personagens_widgets.values() if w["voz"].get() in self.vozes_fem)
        qtd_masc = sum(1 for w in self.personagens_widgets.values() if w["voz"].get() in self.vozes_masc)
        excecoes_fem = ["ALICE", "BEATRIZ", "MULHER", "MAE", "MÃE", "RAQUEL", "CARMEN", "SUELI", "GABI"]
        
        novos = 0
        for nome in personagens_roteiro:
            if nome not in self.personagens_widgets:
                primeiro_nome = nome.split()[0]
                
                # Heurística de Gênero
                if primeiro_nome.endswith('A') or primeiro_nome in excecoes_fem:
                    voz = self.vozes_fem[qtd_fem % len(self.vozes_fem)]
                    pitch = self.opcoes_pitch[(qtd_fem // len(self.vozes_fem)) % len(self.opcoes_pitch)]
                    qtd_fem += 1
                else:
                    voz = self.vozes_masc[qtd_masc % len(self.vozes_masc)]
                    pitch = self.opcoes_pitch[(qtd_masc // len(self.vozes_masc)) % len(self.opcoes_pitch)]
                    qtd_masc += 1
                
                # Renderiza o formulário visual
                self.adicionar_personagem_ui(nome, voz, pitch)
                novos += 1

        if novos > 0:
            self.label_status.configure(text=f"✨ {novos} personagens detectados e adicionados ao painel!", text_color="green")
        else:
            self.label_status.configure(text="Todos os personagens do roteiro já estão no painel.", text_color="yellow")

    def iniciar_requisicao(self):
        self.btn_gerar.configure(state="disabled", text="Comunicando com servidor...")
        self.label_status.configure(text="Enviando JSON e processando vozes...", text_color="yellow")
        threading.Thread(target=self.enviar_para_api).start()

    def enviar_para_api(self):
        try:
            # Agora extraímos os dados direto dos Dropdowns visuais!
            personagens_payload = []
            for nome, widgets in self.personagens_widgets.items():
                personagens_payload.append({
                    "nome": nome,
                    "voz": widgets["voz"].get(),
                    "pitch": widgets["pitch"].get(),
                    "rate": "+15%"
                })

            # Parse do roteiro
            roteiro_payload = []
            for linha in self.caixa_roteiro.get("0.0", "end").strip().split('\n'):
                if ':' in linha:
                    nome, fala = linha.split(':', 1)
                    roteiro_payload.append({"personagem": nome.strip().upper(), "fala": fala.strip()})

            payload = {"personagens": personagens_payload, "roteiro": roteiro_payload}

            
            resposta = requests.post("http://localhost:8000/gerar", json=payload)

            if resposta.status_code == 200:
                caminho_salvar = os.path.join(os.getcwd(), "audio_gerado_pela_api.mp3")
                with open(caminho_salvar, "wb") as f:
                    f.write(resposta.content)
                self.label_status.configure(text=f"✅ Sucesso! Áudio salvo na pasta atual.", text_color="green")
            else:
                self.label_status.configure(text=f"❌ Erro na API: Código {resposta.status_code}", text_color="red")

        except Exception as e:
            self.label_status.configure(text=f"❌ Erro: {str(e)}", text_color="red")
        finally:
            self.btn_gerar.configure(state="normal", text="🎙️ Solicitar Áudio à API")

if __name__ == "__main__":
    app = TTSClientApp()
    app.mainloop()