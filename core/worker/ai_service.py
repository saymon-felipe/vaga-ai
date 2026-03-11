import os
import json
import re
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
import httpx

IP_DO_DESKTOP = "100.115.53.95"

nuvem_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

# [MUDANÇA 1] Aumentamos o timeout para 120s (Garante que a GPU tenha tempo de trabalhar)
local_http_client = httpx.AsyncClient(timeout=120.0)
local_client = AsyncOpenAI(
    base_url=f"http://{IP_DO_DESKTOP}:11434/v1",
    api_key="ollama",
    http_client=local_http_client
)

def otimizar_texto_para_ia(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    
    for element in soup(["script", "style", "header", "footer", "nav", "aside", "form", "meta", "noscript", "svg", "img", "button"]):
        element.extract()
    
    palavras_lixo = [
        "vagas relacionadas", "vagas similares", "política de privacidade", 
        "termos de uso", "direitos reservados", "clique aqui", "inscreva-se", 
        "candidatar", "compartilhar", "outras vagas", "faça login", "esqueci minha senha"
    ]
    
    palavras_chave = [
        "requisito", "experiência", "conhecimento", "salário", "r$", "benefício", 
        "remoto", "híbrido", "stack", "tecnologia", "diferencial", "atribuições", 
        "responsabilidades", "modelo de contratação", "pj", "clt", "vaga", "sobre a posição"
    ]
    
    tags_uteis = soup.find_all(['p', 'li', 'h2', 'h3', 'h4', 'span'])
    textos_relevantes = []
    
    for i, tag in enumerate(tags_uteis):
        text = tag.get_text(separator=" ", strip=True)
        text_lower = text.lower()
        
        if 30 < len(text) < 1500 and not any(lixo in text_lower for lixo in palavras_lixo):
            if i < 5 or any(chave in text_lower for chave in palavras_chave):
                textos_relevantes.append(text)
            
    textos_unicos = list(dict.fromkeys(textos_relevantes))
    return "\n".join(textos_unicos)

async def extrair_miolo_local(texto_completo):
    prompt = f"""
    Extraia do texto abaixo APENAS:
    - Nome da Empresa
    - Salário
    - Requisitos
    - Responsabilidades
    
    NÃO responda com saudações. Seja direto.
    
    Texto:
    {texto_completo}
    """
    try:
        response = await local_client.chat.completions.create(
            model="qwen2.5:3b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            # [MUDANÇA 2] keep_alive: -1 força a GPU a manter o modelo sempre pronto (sem atrasos)
            extra_body={"keep_alive": -1}
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"   - [AVISO] GPU Local ocupada ou Ollama offline. Bypass ativado. ({e})")
        # Se cair no bypass, manda um texto bem menor para não estourar a OpenAI
        return texto_completo[:1500] 

# [MUDANÇA 3] Função que corta o envio de dados inúteis para a OpenAI (Economiza milhares de tokens)
def enxugar_perfil_para_openai(perfil_usuario):
    try:
        skills = [s.get("nome") for s in perfil_usuario.get("skills", [])]
        perfil = perfil_usuario.get("perfil", {})
        
        perfil_enxuto = {
            "senioridade": perfil.get("senioridade", "Não informado"),
            "cargo_desejado": perfil.get("cargo", "Desenvolvedor"),
            "skills_principais": skills
        }
        return perfil_enxuto
    except Exception:
        return {"aviso": "Usar conhecimentos gerais de desenvolvimento."}

async def analisar_vaga_com_ia(vaga_texto, perfil_usuario):
    texto_filtrado = await extrair_miolo_local(vaga_texto)
    
    # Aplica a limpeza do perfil antes de gastar tokens
    perfil_limpo = enxugar_perfil_para_openai(perfil_usuario)
    
    prompt = f"""
    Atue como Tech Recruiter. Analise a vaga e o perfil.
    
    Vaga:
    {texto_filtrado}
    
    Perfil: 
    {json.dumps(perfil_limpo)}
    
    Retorne APENAS um JSON válido com o exato schema abaixo:
    {{
      "empresa_nome": "Nome real da empresa",
      "faixa_salarial": "Valor extraído (ex: R$ 5.000) ou 'A Combinar'",
      "descricao_formatada": "Crie um resumo claro. Use quebras de linha (\\n\\n) para separar blocos.",
      "match_score": int (0-100), 
      "status": "Recomendada" (se score > 85) ou "Ignorado", 
      "argumentos": ["motivo 1", "motivo 2"]
    }}
    """
    try:
        response = await nuvem_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"-> [WORKER-ERRO] Falha na IA em nuvem: {e}")
        return {
            "empresa_nome": "Desconhecida", 
            "faixa_salarial": "A Combinar", 
            "descricao_formatada": "Falha ao formatar texto.", 
            "match_score": 0, 
            "status": "Erro", 
            "argumentos": []
        }