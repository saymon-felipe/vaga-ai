import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from database import SessionLocal
from models import JobApplication
from state import state
from api_client import obter_perfil_usuario
from ai_service import otimizar_texto_para_ia, analisar_vaga_com_ia

async def run_scraper_agent(cargo: str, localizacao: str):
    state.is_running = True
    print(f"-> [WORKER] Iniciando busca avançada para: {cargo} em {localizacao}...")
    
    try:
        perfil_usuario = await obter_perfil_usuario()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )
            page = await browser.new_page()
            page.set_default_timeout(15000) 
            
            db = SessionLocal()
            
            query = f'site:gupy.io "{cargo}" "{localizacao}"'
            url_busca = f"https://www.google.com/search?q={query}"
            
            await page.goto(url_busca)
            await asyncio.sleep(3)
            
            links = await page.locator("a h3").evaluate_all(
                "elements => elements.map(el => el.closest('a').href)"
            )
            titulos = await page.locator("a h3").all_inner_texts()
            
            for i in range(min(5, len(links))):
                if not state.is_running:
                    print("-> [WORKER] Busca interrompida manualmente.")
                    break
                    
                link = links[i]
                titulo = titulos[i]
                
                vaga_existente = db.query(JobApplication).filter(JobApplication.vaga_url == link).first()
                if vaga_existente:
                    continue
                
                try:
                    await page.goto(link)
                    await asyncio.sleep(2)
                    
                    html_content = await page.content()
                    texto_otimizado = otimizar_texto_para_ia(html_content)
                    analise_ia = await analisar_vaga_com_ia(texto_otimizado, perfil_usuario)
                    
                    status_vaga = "Ignorado" if analise_ia.get("match_score", 0) < 50 else analise_ia.get("status", "Analisando")

                    nova_vaga = JobApplication(
                        plataforma="Gupy via Google",
                        empresa_nome="Extraída da Vaga",
                        vaga_titulo=titulo,
                        vaga_url=link,
                        status=status_vaga,
                        match_score=analise_ia.get("match_score", 0),
                        job_description_raw=texto_otimizado,
                        argumentos_match_raw=analise_ia.get("argumentos", [])
                    )
                    db.add(nova_vaga)
                    db.commit()
                    print(f"-> [WORKER] Vaga salva: {titulo} | Score: {analise_ia.get('match_score')}")
                    
                except PlaywrightTimeoutError:
                    print(f"-> [WORKER] Timeout ignorado na vaga {i+1}.")
                except Exception as ex_vaga:
                    print(f"-> [WORKER] Erro na vaga {i+1}: {ex_vaga}")
                    
    except Exception as general_error:
        print(f"-> [WORKER] Erro fatal no scraper: {general_error}")
    finally:
        try:
            db.close()
        except: pass
        state.is_running = False
        print("-> [WORKER] Ciclo finalizado.")