# 🎙️ TTS Creator Studio

Um sistema Full-Stack para geração autônoma e contínua de áudios com vozes neurais (Text-to-Speech), otimizado para criadores de conteúdo que desejam utilizar vozes artificiais para diálogos que envolvem 1 personagem ou mais.

## 🏗️ Arquitetura do Sistema

O projeto foi construído seguindo o padrão Cliente-Servidor para isolar o processamento de mídia pesado da interface de usuário:

* **Backend (API RESTful):** Desenvolvido em Python com **FastAPI**. Responsável por receber o roteiro em JSON, conectar-se ao serviço Edge TTS assincronamente, processar os arquivos binários (removendo metadados de gap) e concatenar o diálogo final.
* **Frontend (Desktop Client):** Desenvolvido em Python utilizando **CustomTkinter** para uma interface de usuário moderna (Dark Mode). Atua como um "Heavy Client" que compila as instruções e consome a API remota via protocolo HTTP.

## 🚀 Como Utilizar

A forma mais fácil de utilizar o TTS Creator Studio é baixando o executável compilado, que já se conecta automaticamente à nossa API hospedada na nuvem.

1. Acesse a aba [Releases](../../releases) deste repositório.
2. Baixe o arquivo `app.exe`.
3. Execute o programa, configure as vozes e digite seu roteiro.
4. Clique em "Gerar Áudio Final". O arquivo `.mp3` será salvo na mesma pasta do executável.

## 💻 Rodando Localmente (Para Desenvolvedores)

Se você deseja clonar o projeto e rodar o ambiente de desenvolvimento:

### 1. Subindo a API (Backend)
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py