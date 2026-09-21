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
        self.geometry("900x600")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # PAINEL ESQUERDO: Personagens
        self.frame_config = ctk.CTkFrame(self)
        self.frame_config.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.frame_config, text="⚙️ Personagens (Nome, Voz, Tom)", font=("Arial", 16, "bold")).pack(pady=10)
        
        cfg_padrao = (
            "DAVI, pt-BR-AntonioNeural, +15Hz\n"
            "LUCAS, pt-BR-AntonioNeural, +0Hz\n"
            "PEDRO, pt-BR-AntonioNeural, -15Hz\n"
            "SOFIA, pt-BR-FranciscaNeural, +0Hz\n"
            "DIRETOR CARLOS, pt-BR-AntonioNeural, -25Hz\n"
            "POLICIAL, pt-BR-AntonioNeural, -40Hz"
        )
        self.caixa_config = ctk.CTkTextbox(self.frame_config, height=400)
        self.caixa_config.pack(padx=10, pady=10, fill="both", expand=True)
        self.caixa_config.insert("0.0", cfg_padrao)

        # PAINEL DIREITO: Roteiro
        self.frame_roteiro = ctk.CTkFrame(self)
        self.frame_roteiro.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        ctk.CTkLabel(self.frame_roteiro, text="📝 Roteiro (NOME: Fala contínua)", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.caixa_roteiro = ctk.CTkTextbox(self.frame_roteiro, height=350)
        self.caixa_roteiro.pack(padx=10, pady=10, fill="both", expand=True)
        self.caixa_roteiro.insert("0.0", "DAVI: A comunicação entre a interface de PC e a nossa API está perfeita!\nLUCAS: Exatamente, o servidor envia o arquivo e o app salva automaticamente.")

        self.btn_gerar = ctk.CTkButton(self.frame_roteiro, text="🎙️ Solicitar Áudio à API", command=self.iniciar_requisicao, height=40)
        self.btn_gerar.pack(pady=10)

        self.label_status = ctk.CTkLabel(self.frame_roteiro, text="Servidor aguardando instruções...", text_color="gray")
        self.label_status.pack(pady=5)

    def iniciar_requisicao(self):
        self.btn_gerar.configure(state="disabled", text="Comunicando com servidor...")
        self.label_status.configure(text="Enviando JSON e processando vozes...", text_color="yellow")
        threading.Thread(target=self.enviar_para_api).start()

    def enviar_para_api(self):
        try:
            # Parse dos personagens
            personagens = []
            for linha in self.caixa_config.get("0.0", "end").strip().split('\n'):
                if ',' in linha:
                    partes = [p.strip() for p in linha.split(',')]
                    personagens.append({"nome": partes[0], "voz": partes[1], "pitch": partes[2], "rate": "+15%"})

            # Parse do roteiro
            roteiro = []
            for linha in self.caixa_roteiro.get("0.0", "end").strip().split('\n'):
                if ':' in linha:
                    nome, fala = linha.split(':', 1)
                    roteiro.append({"personagem": nome.strip(), "fala": fala.strip()})

            payload = {"personagens": personagens, "roteiro": roteiro}

            # Chama a API RESTful que construímos no backend
            resposta = requests.post("https://tts-studio-api.onrender.com/gerar", json=payload)

            if resposta.status_code == 200:
                caminho_salvar = os.path.join(os.getcwd(), "audio_gerado_pela_api.mp3")
                with open(caminho_salvar, "wb") as f:
                    f.write(resposta.content)
                self.label_status.configure(text=f"✅ Sucesso! Áudio salvo na pasta atual.", text_color="green")
            else:
                self.label_status.configure(text=f"❌ Erro na API: Código {resposta.status_code}", text_color="red")

        except requests.exceptions.ConnectionError:
            self.label_status.configure(text="❌ Falha: A API (backend) está rodando no terminal?", text_color="red")
        except Exception as e:
            self.label_status.configure(text=f"❌ Erro inesperado: {str(e)}", text_color="red")
        finally:
            self.btn_gerar.configure(state="normal", text="🎙️ Solicitar Áudio à API")

if __name__ == "__main__":
    app = TTSClientApp()
    app.mainloop()