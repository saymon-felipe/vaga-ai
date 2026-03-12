import sys
import traceback

try:
    from fastapi import FastAPI, BackgroundTasks
    from fastapi.responses import PlainTextResponse
    import uvicorn
    import os
    from state import state
    from scraper import run_scraper_agent
    from logger import logger

    app = FastAPI(title="VagaAI Worker")

    @app.post("/api/start")
    async def start_worker(payload: dict, background_tasks: BackgroundTasks):
        if state.is_running:
            logger.warning("Tentativa de iniciar Worker que já está rodando.")
            return {"status": "erro", "mensagem": "O Worker já está rodando."}
            
        cargo = payload.get("cargo", "Desenvolvedor")
        localizacao = payload.get("localizacao", "Remoto")
        
        background_tasks.add_task(run_scraper_agent, cargo, localizacao)
        logger.info(f"Worker iniciado via API. Cargo: {cargo}, Localização: {localizacao}")
        return {"status": "sucesso", "mensagem": "Worker acordado e rodando."}

    @app.post("/api/stop")
    async def stop_worker():
        if not state.is_running:
            return {"status": "info", "mensagem": "O Worker já está parado."}
            
        state.is_running = False
        logger.info("Sinal de parada enviado ao Worker.")
        return {"status": "sucesso", "mensagem": "Automação interrompida."}

    @app.get("/api/status")
    async def get_status():
        return {"is_running": state.is_running}

    @app.get("/api/logs", response_class=PlainTextResponse)
    async def get_logs():
        log_file = "worker_execucao.log"
        if not os.path.exists(log_file):
            return "Nenhum log gerado ainda."
        with open(log_file, "r", encoding="utf-8") as f:
            return "".join(f.readlines()[-150:])

    if __name__ == "__main__":
        logger.info("=== SERVIDOR WORKER INICIADO ===")
        
        uvicorn.run(app, host="0.0.0.0", port=8001)

except Exception as e:
    with open("CRASH_LOG.txt", "w", encoding="utf-8") as f:
        f.write(traceback.format_exc())
    print(f"\n[ERRO FATAL DE INICIALIZAÇÃO] Verifique o arquivo CRASH_LOG.txt\nErro: {str(e)}\n")
    sys.exit(1)