import customtkinter as ctk
from tkinter import filedialog, messagebox
import requests
import threading
import os
import re
import urllib.parse

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
            "en-CA-ClaraNeural",
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
        self.pasta_destino = None  # <--- NOVA VARIÁVEL AQUI

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

        # Botões de Ação Mágica
        self.btn_auto_config = ctk.CTkButton(self.frame_roteiro, text="🪄 Extrair Personagens do Roteiro", command=self.auto_configurar_personagens, fg_color="#2b8a3e", hover_color="#2f9e44", height=35)
        self.btn_auto_config.pack(pady=(0, 10))

        # ================= NOVA SEÇÃO DE EXPORTAÇÃO =================
        self.frame_exportacao = ctk.CTkFrame(self.frame_roteiro, fg_color="transparent")
        self.frame_exportacao.pack(pady=5, fill="x")

        # Botão 1: Escolhe a Pasta
        self.btn_escolher_pasta = ctk.CTkButton(self.frame_exportacao, text="📁 1. Escolher Pasta Destino", command=self.escolher_pasta, fg_color="#1971c2", hover_color="#1864ab", width=180)
        self.btn_escolher_pasta.pack(pady=(0, 10))

        self.lbl_pasta = ctk.CTkLabel(self.frame_exportacao, text="Nenhuma pasta selecionada...", text_color="gray")
        self.lbl_pasta.pack(pady=(0, 10))

        # Campo 2: Nome do Arquivo
        self.frame_nome = ctk.CTkFrame(self.frame_exportacao, fg_color="transparent")
        self.frame_nome.pack(pady=(0, 10), fill="x")
        
        self.lbl_nome = ctk.CTkLabel(self.frame_nome, text="Nome do Arquivo:")
        self.lbl_nome.pack(side="left", padx=(0, 10))
        
        self.entry_nome_arquivo = ctk.CTkEntry(self.frame_nome, width=150)
        self.entry_nome_arquivo.insert(0, "parte1") # Já vem preenchido por padrão!
        self.entry_nome_arquivo.pack(side="left", fill="x", expand=True)
        # ============================================================

        # Botão de Gerar
        self.btn_gerar = ctk.CTkButton(self.frame_roteiro, text="🎙️ 2. Solicitar Áudio à API", command=self.iniciar_requisicao, height=40, state="disabled")
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
                # 1. Pega o nome digitado e garante que termine em .mp3
                nome_arq = self.entry_nome_arquivo.get().strip()
                if not nome_arq.lower().endswith(".mp3"):
                    nome_arq += ".mp3"
                    
                # 2. Junta a pasta selecionada com o nome do arquivo
                caminho_completo = os.path.join(self.pasta_destino, nome_arq)
                
                # 3. Salva o arquivo no HD
                with open(caminho_completo, "wb") as f:
                    f.write(resposta.content)
                    
                # === INTERCEPTA E DECODIFICA OS AVISOS DO BACKEND ===
                avisos_header = resposta.headers.get("X-Avisos")
                alertas = ""
                if avisos_header:
                    avisos_decodificados = urllib.parse.unquote(avisos_header)
                    # Quebra o texto de volta para lista e junta com quebra de linha (\n)
                    alertas = "\n\n".join(avisos_decodificados.split("||"))
                    
                def sucesso_ui():
                    self.label_status.configure(text=f"✅ Salvo como {nome_arq}", text_color="green")
                    self.btn_gerar.configure(state="normal", text="🎙️ 2. Solicitar Áudio à API")
                    self.auto_incrementar_nome()
                    
                    # SE TIVER ALERTA, MOSTRA O POP-UP!
                    if alertas:
                        messagebox.showwarning(
                            title="⚠️ Atenção: Substituição de Vozes",
                            message=f"O áudio foi salvo, mas algumas vozes falharam e o sistema usou o fallback de segurança:\n\n{alertas}"
                        )
                    
                self.after(0, sucesso_ui)
                
            else:
                self.after(0, lambda: self.label_status.configure(text=f"❌ Erro na API: {resposta.status_code}", text_color="red"))
                self.after(0, lambda: self.btn_gerar.configure(state="normal", text="🎙️ 2. Solicitar Áudio à API"))

        except Exception as e:
            self.after(0, lambda: self.label_status.configure(text=f"❌ Erro: {str(e)}", text_color="red"))
            self.after(0, lambda: self.btn_gerar.configure(state="normal", text="🎙️ 2. Solicitar Áudio à API"))
            
    def escolher_pasta(self):
        caminho = filedialog.askdirectory(title="Escolha a pasta para salvar os áudios")
        
        if caminho:
            self.pasta_destino = caminho
            
            # Corta o texto se o caminho for muito grande
            texto_exibicao = caminho if len(caminho) < 45 else "..." + caminho[-42:]
            self.lbl_pasta.configure(text=texto_exibicao, text_color="white")
            
            # Libera o botão de gerar
            self.btn_gerar.configure(state="normal")
            self.label_status.configure(text="Destino configurado. Clique em Solicitar Áudio.", text_color="green")

    def auto_incrementar_nome(self):
        nome_atual = self.entry_nome_arquivo.get().strip()
        
        # Procura qualquer texto + "parte" + números + (qualquer coisa no final)
        # Ex: "video_parte1" -> match.group(1)="video_parte", match.group(2)="1"
        match = re.search(r'(.*parte)(\d+)(.*)', nome_atual, flags=re.IGNORECASE)
        
        if match:
            prefixo = match.group(1)
            numero_atual = int(match.group(2))
            sufixo = match.group(3)
            
            # Soma +1 e remonta a string
            novo_nome = f"{prefixo}{numero_atual + 1}{sufixo}"
            
            # Atualiza o campo de texto na interface
            self.entry_nome_arquivo.delete(0, "end")
            self.entry_nome_arquivo.insert(0, novo_nome)
    
if __name__ == "__main__":
    app = TTSClientApp()
    app.mainloop()