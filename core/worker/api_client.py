import httpx

async def obter_perfil_usuario():
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp_perfil = await client.get("http://localhost:8000/api/profile")
            resp_skills = await client.get("http://localhost:8000/api/skills")
            
            perfil = resp_perfil.json() if resp_perfil.status_code == 200 else {}
            skills = resp_skills.json() if resp_skills.status_code == 200 else []
            
            if "nivel" in perfil:
                perfil["senioridade"] = perfil["nivel"]
                
            return {"perfil": perfil, "skills": skills}
        except Exception as e:
            print(f"-> [WORKER-AVISO] Falha ao obter perfil: {e}")
            return {"perfil": {}, "skills": []}