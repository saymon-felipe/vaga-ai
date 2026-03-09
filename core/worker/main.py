import os
import asyncio
from fastapi import FastAPI, BackgroundTasks
import uvicorn
from database import SessionLocal
from models import JobApplication

app = FastAPI(title="VagaAI Worker")

is_running = False

async def run_scraper_agent(cargo: str, localizacao: str):
    global is_running
    is_running = True
    print(f"-> [WORKER] Acordou! Iniciando busca para: {cargo} em {localizacao}...")
    
    for i in range(3):
        if not is_running:
            print("-> [WORKER] Busca interrompida no meio do processo.")
            return
        await asyncio.sleep(1)
    
    if not is_running:
        print("-> [WORKER] Busca interrompida antes de salvar no banco.")
        return

    try:
        db = SessionLocal()
        nova_vaga = JobApplication(
            plataforma="Exemplo (LinkedIn/Gupy)",
            empresa_nome="Empresa Teste LTDA",
            vaga_titulo=f"Vaga de {cargo}",
            vaga_url="https://exemplo.com",
            status="Analisando"
        )
        db.add(nova_vaga)
        db.commit()
        db.close()
        print("-> [WORKER] Vaga salva no banco com sucesso. Trabalho finalizado.")
    except Exception as e:
        print(f"-> [WORKER] Erro ao salvar no banco: {e}")
    finally:
        is_running = False

@app.post("/api/start")
async def start_worker(payload: dict, background_tasks: BackgroundTasks):
    global is_running
    
    if is_running:
        return {"status": "erro", "mensagem": "O Worker já está rodando uma busca no momento."}
        
    cargo = payload.get("cargo", "Desenvolvedor")
    localizacao = payload.get("localizacao", "Remoto")
    
    background_tasks.add_task(run_scraper_agent, cargo, localizacao)
    
    return {"status": "sucesso", "mensagem": "Worker acordado e rodando em segundo plano."}

@app.post("/api/stop")
async def stop_worker():
    global is_running
    
    if not is_running:
        return {"status": "info", "mensagem": "O Worker já está parado."}
        
    is_running = False
    print("-> [WORKER] Sinal de interrupção recebido!")
    return {"status": "sucesso", "mensagem": "Automação interrompida com sucesso."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)