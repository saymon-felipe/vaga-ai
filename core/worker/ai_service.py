import os
import json
import re
from bs4 import BeautifulSoup
from openai import AsyncOpenAI

ai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

def otimizar_texto_para_ia(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for element in soup(["script", "style", "header", "footer", "nav", "aside", "form"]):
        element.extract()
    
    texto = soup.get_text(separator=" ")
    texto_limpo = re.sub(r'\s+', ' ', texto).strip()
    
    if len(texto_limpo) > 4000:
        meio = len(texto_limpo) // 2
        inicio = max(0, meio - 2000)
        fim = min(len(texto_limpo), meio + 2000)
        texto_limpo = texto_limpo[inicio:fim]
        
    return texto_limpo

async def analisar_vaga_com_ia(vaga_texto, perfil_usuario):
    prompt = f"""
    Atue como Tech Recruiter. Analise a vaga e o perfil.
    Retorne APENAS um JSON válido com o schema:
    {{"match_score": int (0-100), "status": "Analisando" ou "Ignorado", "argumentos": ["motivo 1", "motivo 2"]}}
    
    Vaga: {vaga_texto}
    Perfil: {json.dumps(perfil_usuario)}
    """
    try:
        response = await ai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"-> [WORKER-ERRO] Falha na IA: {e}")
        return {"match_score": 0, "status": "Erro", "argumentos": []}