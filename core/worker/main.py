from fastapi import FastAPI, BackgroundTasks
import uvicorn
from state import state
from scraper import run_scraper_agent

app = FastAPI(title="VagaAI Worker")

@app.post("/api/start")
async def start_worker(payload: dict, background_tasks: BackgroundTasks):
    if state.is_running:
        return {"status": "erro", "mensagem": "O Worker já está rodando."}
        
    cargo = payload.get("cargo", "Desenvolvedor")
    localizacao = payload.get("localizacao", "Remoto")
    
    background_tasks.add_task(run_scraper_agent, cargo, localizacao)
    return {"status": "sucesso", "mensagem": "Worker acordado e rodando."}

@app.post("/api/stop")
async def stop_worker():
    if not state.is_running:
        return {"status": "info", "mensagem": "O Worker já está parado."}
        
    state.is_running = False
    return {"status": "sucesso", "mensagem": "Automação interrompida."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)