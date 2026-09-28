import sys
import asyncio
import edge_tts
import os
import shutil
import urllib.parse
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI(title="TTS Creator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PersonagemConfig(BaseModel):
    nome: str
    voz: str
    pitch: str
    rate: str = "+15%"

class LinhaRoteiro(BaseModel):
    personagem: str
    fala: str

class TTSRequest(BaseModel):
    personagens: List[PersonagemConfig]
    roteiro: List[LinhaRoteiro]

def limpar_metadados_mp3(caminho):
    with open(caminho, 'rb') as f:
        data = f.read()
    inicio = 0
    if data.startswith(b'ID3'):
        tamanho = (data[6] << 21) | (data[7] << 14) | (data[8] << 7) | data[9]
        inicio = 10 + tamanho
    fim = len(data)
    if len(data) >= 128 and data[-128:-125] == b'TAG':
        fim -= 128
    return data[inicio:fim]

@app.post("/gerar")
async def gerar_audio(req: TTSRequest):
    vozes_map = {p.nome.upper(): (p.voz, p.pitch, p.rate) for p in req.personagens}
    
    os.makedirs("temp_audios", exist_ok=True)
    arquivos_temp = []
    avisos_frontend = [] 
    
    print("\n--- INICIANDO NOVA GERAÇÃO DE ÁUDIO ---")
    
    for idx, linha in enumerate(req.roteiro):
        fala_limpa = linha.fala.strip()
        if not fala_limpa:
            continue
            
        nome_personagem = linha.personagem.strip().upper()
        
        if nome_personagem in vozes_map:
            voz, tom, vel = vozes_map[nome_personagem]
        else:
            voz, tom, vel = ("pt-BR-AntonioNeural", "+0Hz", "+15%")

        temp_file = f"temp_audios/temp_{idx}.mp3"
        
        try:
            communicate = edge_tts.Communicate(fala_limpa, voz, pitch=tom, rate=vel)
            await communicate.save(temp_file)
            arquivos_temp.append(temp_file)
            
        except Exception as e:
            # ERRO CAPTURADO! Registra o aviso para o Frontend
            msg_aviso = f"Fala {idx+1} ({nome_personagem}): A voz '{voz}' falhou e foi substituída pelo Antonio."
            avisos_frontend.append(msg_aviso)
            print(f"⚠️ Erro técnico com '{voz}': {e}. Fallback acionado!")
            
            try:
                voz_fallback = "pt-BR-AntonioNeural"
                communicate_fallback = edge_tts.Communicate(fala_limpa, voz_fallback, pitch=tom, rate=vel)
                await communicate_fallback.save(temp_file)
                arquivos_temp.append(temp_file)
            except Exception as e_fallback:
                print(f"❌ Erro fatal na linha {idx}: {e_fallback}")
            
    if not arquivos_temp:
        shutil.rmtree("temp_audios", ignore_errors=True)
        return {"erro": "Falha total na geração do áudio."}
            
    arquivo_final = "dialogo_final.mp3"
    with open(arquivo_final, "wb") as outfile:
        for f in arquivos_temp:
            outfile.write(limpar_metadados_mp3(f))
            
    shutil.rmtree("temp_audios", ignore_errors=True)
    
    # === PREPARA O CABEÇALHO COM OS AVISOS ===
    headers = {}
    if avisos_frontend:
        # Junta todos os erros com "||" e codifica para enviar na rede
        texto_avisos = "||".join(avisos_frontend)
        headers["X-Avisos"] = urllib.parse.quote(texto_avisos)
    
    print("✅ Áudio final gerado com sucesso!")
    # Envia o arquivo e embute os headers
    return FileResponse(arquivo_final, media_type="audio/mpeg", filename="audio_roteiro.mp3", headers=headers)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)