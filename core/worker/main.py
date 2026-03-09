import os
import asyncio
from fastapi import FastAPI, BackgroundTasks
import uvicorn
from database import SessionLocal
from models import JobApplication

app = FastAPI(title="VagaAI Worker")

# Função que fará o trabalho pesado (Scraping + IA)
async def run_scraper_agent(cargo: str, localizacao: str):
    print(f"-> [WORKER] Acordou! Iniciando busca para: {cargo} em {localizacao}...")
    
    # Aqui entrará o código do Playwright depois
    await asyncio.sleep(3) # Simulando o tempo de abrir o navegador
    
    # Exemplo simulando salvamento no banco de dados
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

# Rota para "acordar" o robô
@app.post("/api/start")
async def start_worker(payload: dict, background_tasks: BackgroundTasks):
    cargo = payload.get("cargo", "Desenvolvedor")
    localizacao = payload.get("localizacao", "Remoto")
    
    # Dispara a função em background e retorna a resposta pro Node.js na hora
    background_tasks.add_task(run_scraper_agent, cargo, localizacao)
    
    return {"status": "sucesso", "mensagem": "Worker acordado e rodando em segundo plano."}

if __name__ == "__main__":
    # Roda o servidor interno na porta 8001
    uvicorn.run(app, host="0.0.0.0", port=8001)