import asyncio
import urllib.parse
import re
import os
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from database import SessionLocal
from models import JobApplication
from state import state
from api_client import obter_perfil_usuario
from ai_service import otimizar_texto_para_ia, analisar_vaga_com_ia
from apply_service import iniciar_aplicacao 

PLATAFORMAS_AUTO_APPLY = ["LinkedIn", "Nerdin"]

def pre_filtro_local(titulo_vaga: str, texto_vaga: str, perfil: dict, skills: list) -> bool:
    titulo_lower = titulo_vaga.lower()
    texto_lower = texto_vaga.lower()
    nivel_usuario = perfil.get("senioridade", "pleno").lower()
    nomes_skills = [s.get("nome", "").lower() for s in skills]

    termos_encerrada = [
        "não aceita mais candidaturas", 
        "vaga encerrada", 
        "inscrições encerradas", 
        "vaga inativa", 
        "no longer accepting", 
        "esta vaga foi fechada", 
        "oportunidade encerrada"
    ]
    if any(termo in texto_lower or termo in titulo_lower for termo in termos_encerrada):
        return False

    if nivel_usuario in ["pleno", "mid"]:
        termos_senior = ["sênior", "senior", "sr", "especialista", "tech lead", "arquiteto", "architect"]
        termos_junior = ["júnior", "junior", "jr", "estágio", "estagio", "trainee"]
        
        if any(termo in titulo_lower for termo in termos_senior):
            return False
        if any(termo in titulo_lower for termo in termos_junior):
            return False

    tecnologias_exclusivas = ["ruby", "java ", "php", "golang", "go ", "python", "ios", "android", "flutter", "kotlin", "swift"]
    for tech in tecnologias_exclusivas:
        if tech in titulo_lower and not any(tech in s for s in nomes_skills):
            return False

    return True

def gerar_buscas_naturais(cargo, perfil, skills):
    sites = [
        "site:linkedin.com/jobs",
        "site:gupy.io",
        "site:programathor.com.br",
        "site:br.indeed.com",
        "site:nerdin.com.br"
    ]
    
    techs_principais = [s.get("nome", "") for s in skills[:6]]
    queries = []
    
    for site in sites:
        for tech in techs_principais:
            if tech:
                queries.append(f'vaga {cargo} {tech} remoto {site}')
        
        queries.append(f'vaga {cargo} londrina cambé {site}')
        
    return list(dict.fromkeys(queries))[:1] #TODO mudar para 35

def padronizar_link_vaga(url: str) -> str:
    url_limpa = url.split('?utm_')[0].split('&utm_')[0].split('?trk=')[0].split('&trk=')[0].split('?ref=')[0]
    
    url_lower = url_limpa.lower()
    if "linkedin.com" in url_lower and "currentjobid=" in url_lower:
        match = re.search(r'currentjobid=(\d+)', url_lower)
        if match:
            job_id = match.group(1)
            return f"https://www.linkedin.com/jobs/view/{job_id}/"
            
    return url_limpa

def is_vaga_direta(url: str) -> bool:
    url_lower = url.lower()
    if "linkedin.com" in url_lower:
        return "/view/" in url_lower 
    if "gupy.io" in url_lower:
        return "/job/" in url_lower or "/vaga/" in url_lower
    if "indeed.com" in url_lower:
        return "viewjob" in url_lower or "vjk=" in url_lower
    if "programathor.com.br" in url_lower:
        return "/jobs/" in url_lower and not url_lower.endswith("/jobs/")
    if "vagas.com.br" in url_lower:
        return "/vagas/v" in url_lower
    return True

async def run_scraper_agent(cargo: str, localizacao: str):
    state.is_running = True
    print(f"\n-> [WORKER] Iniciando varredura natural multiplataforma...")
    
    db = None
    try:
        dados_usuario = await obter_perfil_usuario()
        perfil_usuario = dados_usuario.get("perfil", {})
        skills_usuario = dados_usuario.get("skills", [])
        
        queries = gerar_buscas_naturais(cargo, perfil_usuario, skills_usuario)
        
        db = SessionLocal()
        links_brutos = {}
        
        storage_file = "auth_state.json"
        has_auth = os.path.exists(storage_file)
        if not has_auth:
            print("-> [AVISO] auth_state.json não encontrado. Automação de candidatura desativada.")
            
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            
            context_args = {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "viewport": {"width": 1366, "height": 768},
                "locale": "pt-BR"
            }
            if has_auth:
                context_args["storage_state"] = storage_file
                
            context = await browser.new_context(**context_args)
            page = await context.new_page()
            page.set_default_timeout(30000)
            
            for idx, query in enumerate(queries):
                if not state.is_running: break
                print(f"-> [WORKER] Buscando ({idx+1}/{len(queries)}): {query}")
                
                query_encoded = urllib.parse.quote(query)
                url_busca = f"https://duckduckgo.com/?q={query_encoded}&kl=br-pt&ia=web"
                
                await page.goto(url_busca)
                await asyncio.sleep(2)
                
                try:
                    await page.wait_for_selector('a[data-testid="result-title-a"]', timeout=10000)
                except PlaywrightTimeoutError:
                    continue
                    
                elementos = await page.locator('a[data-testid="result-title-a"]').all()
                for el in elementos:
                    link_raw = await el.get_attribute("href")
                    titulo = await el.inner_text()
                    
                    if link_raw and not "duckduckgo" in link_raw:
                        link_processado = padronizar_link_vaga(link_raw)
                        links_brutos[link_processado] = titulo

            links_limpos_finais = {}
            print(f"\n-> [WORKER] Triando {len(links_brutos)} links encontrados...")
            
            for link_alvo, titulo in links_brutos.items():
                if not state.is_running: break
                
                if is_vaga_direta(link_alvo):
                    links_limpos_finais[link_alvo] = titulo
                else:
                    print(f"   - [HUB DETECTADO] Entrando para extrair vagas de: {link_alvo[:50]}...")
                    try:
                        await page.goto(link_alvo)
                        await asyncio.sleep(3)
                        
                        await page.evaluate("window.scrollBy(0, 1500)")
                        await asyncio.sleep(2)
                        
                        hrefs = await page.evaluate("""() => {
                            return Array.from(document.querySelectorAll('a')).map(a => ({href: a.href, text: a.innerText.trim()}));
                        }""")
                        
                        for item in hrefs:
                            if not item['href']: continue
                            
                            sub_link = padronizar_link_vaga(item['href'])
                            
                            if is_vaga_direta(sub_link) and any(d in sub_link for d in ["linkedin.com", "gupy.io", "programathor.com.br", "indeed.com", "vagas.com.br"]):
                                nome_vaga = item['text'] if len(item['text']) > 5 else "Vaga extraída do Hub"
                                links_limpos_finais[sub_link] = nome_vaga
                    except Exception as e:
                        print(f"      Erro ao ler o Hub: {e}")

            print(f"\n-> [WORKER] Desempacotamento concluído. Temos {len(links_limpos_finais)} vagas DIRETAS prontas para análise!")
            
            for link, titulo in links_limpos_finais.items():
                if not state.is_running: 
                    print("\n-> [WORKER] Automação interrompida.")
                    break 
                
                if db.query(JobApplication).filter(JobApplication.vaga_url == link).first():
                    continue
                
                vaga_titulo_repetido = db.query(JobApplication).filter(
                    JobApplication.vaga_titulo == titulo,
                    JobApplication.vaga_url.like(f"%{link.split('/')[2]}%") 
                ).first()
                if vaga_titulo_repetido:
                    continue

                print(f"\n-> [WORKER] Analisando: {titulo[:60]}...")
                
                try:
                    await page.goto(link)
                    await asyncio.sleep(2)
                    
                    html_content = await page.content()
                    texto_bruto = otimizar_texto_para_ia(html_content)
                    
                    if not pre_filtro_local(titulo, texto_bruto, perfil_usuario, skills_usuario):
                        print("   - [DESCARTADA LOCAL] Requisitos, senioridade incompatível ou vaga encerrada.")
                        continue
                    
                    print("   - Validada no pré-filtro. Avaliando com Inteligência Artificial...")
                    analise_ia = await analisar_vaga_com_ia(texto_bruto, dados_usuario)
                    
                    score = analise_ia.get("match_score", 0)
                    status_vaga = "Ignorado" if score < 85 else "Recomendada"
                    
                    plataforma = "Outros"
                    if "linkedin.com" in link: plataforma = "LinkedIn"
                    elif "gupy.io" in link: plataforma = "Gupy"
                    elif "programathor.com.br" in link: plataforma = "ProgramaThor"
                    elif "indeed.com" in link: plataforma = "Indeed"
                    elif "nerdin.com.br" in link: plataforma = "Nerdin"
                    elif "vagas.com.br" in link: plataforma = "Vagas.com"

                    # Alterado para fluxo contínuo sem limites numéricos
                    if score >= 85 and has_auth:
                        if plataforma in PLATAFORMAS_AUTO_APPLY:
                            print(f"   - [MATCH ALTO: {score}%] Iniciando aplicação automática para {plataforma}...")
                            
                            resultado_aplicacao = await iniciar_aplicacao(page, link, plataforma, dados_usuario)
                            
                            if resultado_aplicacao == "Aplicado":
                                status_vaga = "Aplicado"
                                print("   - [SUCESSO] Candidatura enviada e registrada!")
                            else:
                                print(f"   - [INFO] Requer atenção manual: {resultado_aplicacao}")
                        else:
                            print(f"   - [MATCH ALTO: {score}%] Automação desativada para {plataforma}. Salva para aplicação manual.")

                    nova_vaga = JobApplication(
                        plataforma=plataforma,
                        empresa_nome=analise_ia.get("empresa_nome", "Confidencial"),
                        vaga_titulo=titulo,
                        vaga_url=link,
                        status=status_vaga,
                        match_score=score,
                        faixa_salarial=analise_ia.get("faixa_salarial", "A Combinar"),
                        job_description_raw=analise_ia.get("descricao_formatada", "Descrição indisponível."),
                        argumentos_match_raw=analise_ia.get("argumentos", [])
                    )
                    db.add(nova_vaga)
                    db.commit()
                    print(f"   - [SALVA] Score {score}% | {plataforma} | Salário: {nova_vaga.faixa_salarial}")
                    
                except PlaywrightTimeoutError:
                    print("   - [AVISO] Timeout ao tentar carregar a página da vaga.")
                except Exception as e_vaga:
                    db.rollback()
                    print(f"   - [ERRO] Falha interna ao processar página: {e_vaga}")
                    
    except Exception as general_error:
        print(f"-> [WORKER] ERRO FATAL: {general_error}")
    finally:
        if db: db.close()
        state.is_running = False
        print("\n-> [WORKER] Automação concluída com sucesso.")