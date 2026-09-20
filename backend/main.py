import sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import asyncio
import edge_tts
import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sys


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
    vozes_map = {p.nome: (p.voz, p.pitch, p.rate) for p in req.personagens}
    
    os.makedirs("temp_audios", exist_ok=True)
    arquivos_temp = []
    
    for idx, linha in enumerate(req.roteiro):
        if linha.personagem in vozes_map:
            voz, tom, vel = vozes_map[linha.personagem]
            temp_file = f"temp_audios/temp_{idx}.mp3"
            communicate = edge_tts.Communicate(linha.fala, voz, pitch=tom, rate=vel)
            await communicate.save(temp_file)
            arquivos_temp.append(temp_file)
            
    arquivo_final = "dialogo_final.mp3"
    with open(arquivo_final, "wb") as outfile:
        for f in arquivos_temp:
            outfile.write(limpar_metadados_mp3(f))
            
    for file in arquivos_temp:
        os.remove(file)
    os.rmdir("temp_audios")
    
    return FileResponse(arquivo_final, media_type="audio/mpeg", filename="audio_roteiro.mp3")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)