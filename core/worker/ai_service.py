import os
import json
import re
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
import httpx
from dotenv import load_dotenv
from logger import logger

load_dotenv()

IP_DO_DESKTOP = os.getenv("IP_DO_DESKTOP", "100.115.53.95")
nuvem_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

local_http_client = httpx.AsyncClient(timeout=120.0)
local_client = AsyncOpenAI(
    base_url=f"http://{IP_DO_DESKTOP}:11434/v1",
    api_key="ollama",
    http_client=local_http_client
)

def otimizar_texto_para_ia(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for element in soup(["script", "style", "header", "footer", "nav", "aside", "svg", "img", "button"]):
        element.extract()
    return re.sub(r'\s+', ' ', soup.get_text(separator=" ", strip=True))[:4500]

def enxugar_perfil(dados_completos):
    perfil = dados_completos.get("perfil", {})
    return {
        "cargo": perfil.get("cargo", ""),
        "senioridade": perfil.get("senioridade", ""),
        "modalidade": perfil.get("modalidade", ""),
        "skills": [
            {"nome": s.get("nome"), "nivel": s.get("nivel")} 
            for s in dados_completos.get("skills", [])
        ]
    }

async def extrair_json_seguro(texto_ia, fallback_vazio):
    try:
        match = re.search(r'\{.*\}', texto_ia.replace('\n', ''), re.DOTALL)
        if match: return json.loads(match.group())
        return json.loads(texto_ia)
    except:
        return fallback_vazio

async def triagem_eliminatoria_local(texto_vaga, skills_usuario):
    nomes_skills = [s.get("nome", "").lower() for s in skills_usuario]
    prompt = f"""
    Responda APENAS com 'SIM' ou 'NAO'.
    O texto da vaga EXIGE OBRIGATORIAMENTE experiência em uma linguagem principal ou framework backend que NÃO está nesta lista: {nomes_skills}?
    Texto da vaga: {texto_vaga[:2500]}
    """
    try:
        resposta = await local_client.chat.completions.create(
            model="qwen2.5:3b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        return "NAO" in resposta.choices[0].message.content.strip().upper()
    except Exception as e:
        logger.warning(f"Erro no Guardião Local: {e}")
        return True 

async def destrinchar_vaga_local(texto_vaga, titulo):
    prompt = f"""
    Extraia as informações da vaga "{titulo}" e retorne EXATAMENTE este formato JSON:
    {{
      "empresa": "Nome da empresa (ou 'Confidencial')",
      "salario": "Valor numérico, faixa ou 'A Combinar'",
      "senioridade_exigida": "Qual o nível exigido? (Ex: Júnior, Pleno, Sênior, Especialista, Não especificado)",
      "resumo": "Uma frase resumindo a vaga",
      "obrigatorios": ["item 1", "item 2"],
      "desejaveis": ["item 1", "item 2"],
      "beneficios": ["item 1", "item 2"]
    }}
    Procure bem pelo salário e empresa no início ou fim do texto.
    Texto: {texto_vaga}
    """
    fallback = {
        "empresa": "Confidencial", "salario": "A Combinar", "senioridade_exigida": "Não especificado", 
        "resumo": "Vaga na área de tecnologia.", "obrigatorios": [], "desejaveis": [], "beneficios": []
    }
    try:
        resposta = await local_client.chat.completions.create(
            model="qwen2.5:3b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        return await extrair_json_seguro(resposta.choices[0].message.content, fallback)
    except Exception as e:
        logger.warning(f"Erro no Compactador Local: {e}")
        return fallback

async def analise_profunda_nuvem(vaga_destrinchada, dados_usuario):
    perfil_clean = enxugar_perfil(dados_usuario)
    prompt = f"""
Você é um Headhunter Sênior implacável.
Calcule a Previsão de Sucesso (0 a 100) baseando-se no cruzamento exato de habilidades e NÍVEL DE SENIORIDADE.

VAGA COMPACTADA: {json.dumps(vaga_destrinchada)}
PERFIL DO CANDIDATO: {json.dumps(perfil_clean)}

REGRAS DE RANKING:
1. SCORE TÉCNICO (50 pts): Peso 1.5 se o requisito obrigatório bater com uma Skill "Avançada" do candidato. Peso 1.0 para "Intermediária".
2. SENIORIDADE (20 pts): 
   - O candidato é estritamente {perfil_clean.get('senioridade')}.
   - REGRA ELIMINATÓRIA: Analise o contexto da vaga. Se ela exigir ou der indícios claros de nível Júnior, Sênior, Especialista, Tech Lead, Trainee ou Estágio, zere esta categoria E acione o "corte_senioridade".
   - Ganha 20 pontos apenas se a vaga for claramente para Pleno/Mid-level ou se não especificar senioridade mas o escopo bater com um nível Pleno.
3. EXTRAS (30 pts): Some pontos se a vaga oferecer bons benefícios e bater com os requisitos desejáveis.
4. PENALIDADE: Subtraia 30 pontos para cada requisito obrigatório crítico que o candidato NÃO possui.

Retorne APENAS o JSON EXATAMENTE neste formato:
{{
  "previsao_sucesso": 85,
  "corte_senioridade": false, // MUITO IMPORTANTE: Retorne true APENAS se a vaga for de nível incompatível (ex: Sênior ou Júnior). Retorne false se for Pleno ou compatível.
  "argumentos": ["Motivo 1", "Risco detectado"]
}}
"""
    fallback = {"previsao_sucesso": 50, "corte_senioridade": True, "argumentos": ["Falha na análise da IA Nuvem"]}
    try:
        response = await nuvem_client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" },
            temperature=0.1
        )
        return await extrair_json_seguro(response.choices[0].message.content, fallback)
    except Exception as e:
        logger.error(f"Erro na IA Nuvem: {e}")
        return fallback