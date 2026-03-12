import asyncio
import urllib.parse
import re
import os
import json
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from database import SessionLocal
from models import JobApplication
from state import state
from api_client import obter_perfil_usuario
from ai_service import otimizar_texto_para_ia, triagem_eliminatoria_local, destrinchar_vaga_local, analise_profunda_nuvem
from logger import logger

DEV_MODE = True

def pre_filtro_local(titulo_vaga: str, texto_vaga: str, perfil: dict, skills: list) -> bool:
    titulo_lower = titulo_vaga.lower()
    texto_lower = texto_vaga.lower()
    modalidade_desejada = perfil.get("modalidade", "remoto").lower()
    nomes_skills = [s.get("nome", "").lower() for s in skills]

    termos_encerrada = ["não aceita mais candidaturas", "vaga encerrada", "inscrições encerradas", "vaga inativa", "no longer accepting"]
    if any(termo in texto_lower or termo in titulo_lower for termo in termos_encerrada):
        return False

    if modalidade_desejada == "remoto":
        if any(t in texto_lower or t in titulo_lower for t in ["presencial", "on-site", "híbrido", "hibrido", "hybrid"]):
            return False
    elif modalidade_desejada == "presencial":
        if any(t in texto_lower or t in titulo_lower for t in ["remoto", "home office", "remote"]):
            return False

    termos_proibidos_senioridade = [
        r"\bsênior\b", r"\bsenior\b", r"\bsr\b", r"\bsr\.\b", r"\btech lead\b", r"\blead\b",
        r"\blíder\b", r"\blider\b", r"\bespecialista\b", r"\bspecialist\b", r"\barquiteto\b", r"\barchitect\b",
        r"\bjúnior\b", r"\bjunior\b", r"\bjr\b", r"\bjr\.\b", r"\bestágio\b", r"\bestagio\b", 
        r"\btrainee\b", r"\bintern\b", r"\binternship\b"
    ]
    
    for padrao in termos_proibidos_senioridade:
        if re.search(padrao, titulo_lower):
            return False

    tecnologias_exclusivas = ["ruby", "java", "php", "golang", "go", "python", "ios", "android", "c++", "c#"]
    for tech in tecnologias_exclusivas:
        if re.search(r'\b' + re.escape(tech) + r'\b', titulo_lower):
            if not any(tech == s for s in nomes_skills):
                return False

    return True

def gerar_buscas_naturais(cargo, perfil, skills):
    sites = ["site:linkedin.com/jobs", "site:gupy.io", "site:programathor.com.br", "site:br.indeed.com"]
    techs_principais = [s.get("nome", "") for s in skills[:3]] 
    modalidade = perfil.get("modalidade", "remoto").lower()
    queries = []
    
    for site in sites:
        for tech in techs_principais:
            if tech: 
                if modalidade == "remoto":
                    queries.append(f'{cargo} {tech} pleno remoto {site}')
                else:
                    queries.append(f'{cargo} {tech} pleno {site}')
                    
        if modalidade != "remoto":
            queries.append(f'{cargo} londrina cambé {site}')
        
    return list(dict.fromkeys(queries))

def padronizar_link_vaga(url: str) -> str:
    url_limpa = url.split('?utm_')[0].split('&utm_')[0].split('?trk=')[0]
    url_lower = url_limpa.lower()
    if "linkedin.com" in url_lower and "currentjobid=" in url_lower:
        match = re.search(r'currentjobid=(\d+)', url_lower)
        if match: return f"https://www.linkedin.com/jobs/view/{match.group(1)}/"
    return url_limpa

def is_vaga_direta(url: str) -> bool:
    url_lower = url.lower()
    if "linkedin.com" in url_lower: return "/view/" in url_lower 
    if "gupy.io" in url_lower: return "/job/" in url_lower or "/vaga/" in url_lower
    if "indeed.com" in url_lower: return "viewjob" in url_lower or "vjk=" in url_lower
    if "programathor.com.br" in url_lower: return "/jobs/" in url_lower and not url_lower.endswith("/jobs/")
    return True

def extrair_plataforma(link: str) -> str:
    if "linkedin.com" in link: return "LinkedIn"
    if "gupy.io" in link: return "Gupy"
    if "programathor" in link: return "ProgramaThor"
    if "indeed" in link: return "Indeed"
    return "Outros"

async def run_scraper_agent(cargo: str, localizacao: str):
    if getattr(state, '_lock', False):
        logger.warning("Scraper já em execução (lock ativo). Abortando nova chamada.")
        return
    state._lock = True
    state.is_running = True
    
    logger.info(f"Iniciando varredura multiplataforma (Modo Radar)...")
    
    db = None
    try:
        dados_usuario = await obter_perfil_usuario()
        perfil_usuario = dados_usuario.get("perfil", {})
        perfil_usuario["cargo"] = cargo
        perfil_usuario["modalidade"] = localizacao
        skills_usuario = dados_usuario.get("skills", [])
        
        queries = gerar_buscas_naturais(cargo, perfil_usuario, skills_usuario)
        if DEV_MODE: queries = queries[:2]
            
        db = SessionLocal()
        links_brutos = {}
        has_auth = os.path.exists("auth_state.json")
            
        async with async_playwright() as p:
            rodando_no_docker = os.name != 'nt' 
            browser = await p.chromium.launch(headless=rodando_no_docker)
            context_args = {"viewport": {"width": 1366, "height": 768}, "locale": "pt-BR"}
            
            if has_auth: context_args["storage_state"] = "auth_state.json"
                
            context = await browser.new_context(**context_args)
            page = await context.new_page()
            page.set_default_timeout(30000)
            
            for idx, query in enumerate(queries):
                if not state.is_running: break
                url_busca = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}&kl=br-pt&ia=web"
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
                    if link_raw and "duckduckgo" not in link_raw:
                        links_brutos[padronizar_link_vaga(link_raw)] = titulo

            links_limpos_finais = {}
            hub_processado = False
            
            for link_alvo, titulo in links_brutos.items():
                if not state.is_running: break
                if is_vaga_direta(link_alvo):
                    links_limpos_finais[link_alvo] = titulo
                else:
                    if DEV_MODE and hub_processado: continue
                    try:
                        await page.goto(link_alvo)
                        await asyncio.sleep(3)
                        await page.evaluate("window.scrollBy(0, 1500)")
                        await asyncio.sleep(2)
                        hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a => ({href: a.href, text: a.innerText.trim()}))")
                        for item in hrefs:
                            if not item['href']: continue
                            sub_link = padronizar_link_vaga(item['href'])
                            if is_vaga_direta(sub_link):
                                links_limpos_finais[sub_link] = item['text'] if len(item['text']) > 5 else "Vaga extraída"
                        hub_processado = True
                    except Exception: pass
            
            if DEV_MODE: links_limpos_finais = dict(list(links_limpos_finais.items())[:10])

            for link, titulo in links_limpos_finais.items():
                if not state.is_running: break 
                if db.query(JobApplication).filter(JobApplication.vaga_url == link).first(): continue

                try:
                    logger.info(f"Acessando: {titulo}")
                    await page.goto(link)
                    await asyncio.sleep(2)
                    texto_bruto = otimizar_texto_para_ia(await page.content())
                    
                    if not pre_filtro_local(titulo, texto_bruto, perfil_usuario, skills_usuario):
                        logger.info("   [Camada 1] Reprovada: Filtro lógico de senioridade/modalidade/tecnologia.")
                        continue
                    
                    if not await triagem_eliminatoria_local(texto_bruto, skills_usuario):
                        logger.info("   [Camada 2] Reprovada: Exige tecnologia incompatível.")
                        continue
                        
                    vaga_compacta = await destrinchar_vaga_local(texto_bruto, titulo)
                    
                    analise_final = await analise_profunda_nuvem(vaga_compacta, dados_usuario)
                    score = analise_final.get("previsao_sucesso", 0)
                    corte_senioridade = analise_final.get("corte_senioridade", False)
                    
                    if corte_senioridade:
                        logger.info("   [Camada 4] Reprovada: A IA detectou conflito de senioridade (Vaga não é Pleno).")
                        continue 
                    
                    if not isinstance(score, int):
                        try: score = int(score)
                        except: score = 0

                    plataforma = extrair_plataforma(link)

                    if score >= 85:
                        logger.info(f"🚀 [ALTA AFINIDADE] Salvando Vaga Recomendada: {titulo} (Score: {score})")
                        status_vaga = "Recomendada"
                    elif score >= 70:
                        logger.info(f"📂 [REVISÃO MANUAL] Salvando Vaga: {titulo} (Score: {score})")
                        status_vaga = "Salva"
                    else:
                        logger.info(f"🗑️ [DESCARTADA] Score muito baixo: {titulo} (Score: {score}). Ignorando salvamento no banco.")
                        continue

                    def formatar_lista(lista):
                        if not lista or len(lista) == 0:
                            return "  • Não especificado."
                        lista_unica = list(dict.fromkeys(lista))
                        return "\n".join([f"  • {item}" for item in lista_unica])

                    desc_formatada = (
                        f"RESUMO DA VAGA:\n{vaga_compacta.get('resumo', 'Não informado.')}\n\n"
                        f"🎯 REQUISITOS OBRIGATÓRIOS:\n{formatar_lista(vaga_compacta.get('obrigatorios', []))}\n\n"
                        f"✨ DIFERENCIAIS / DESEJÁVEIS:\n{formatar_lista(vaga_compacta.get('desejaveis', []))}\n\n"
                        f"🎁 BENEFÍCIOS:\n{formatar_lista(vaga_compacta.get('beneficios', []))}"
                    )
                    
                    argumentos_db = analise_final.get('argumentos', [])
                    if isinstance(argumentos_db, str):
                        try: argumentos_db = json.loads(argumentos_db)
                        except: argumentos_db = [argumentos_db]

                    nova_vaga = JobApplication(
                        plataforma=plataforma, 
                        empresa_nome=str(vaga_compacta.get("empresa", "Confidencial")),
                        vaga_titulo=titulo, 
                        vaga_url=link, 
                        status=status_vaga,
                        match_score=score, 
                        faixa_salarial=str(vaga_compacta.get("salario", "A Combinar")),
                        job_description_raw=desc_formatada,
                        argumentos_match_raw=argumentos_db,
                        requer_confirmacao_email=False
                    )
                    
                    db.add(nova_vaga)
                    db.commit()

                except Exception as e:
                    logger.error(f"Erro ao processar fluxo da vaga {link}: {e}")
                    db.rollback()

    except Exception as general_error:
        logger.error(f"ERRO FATAL NO SCRAPER: {general_error}")
    finally:
        if db: db.close()
        state.is_running = False
        state._lock = False