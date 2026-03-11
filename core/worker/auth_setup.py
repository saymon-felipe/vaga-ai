import asyncio
from playwright.async_api import async_playwright

async def salvar_sessao():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("\n[LOGIN] Acesse sua conta no LinkedIn e na Gupy na janela que abriu.")
        print("[LOGIN] Navegue para https://www.linkedin.com e faça login.")
        print("[LOGIN] Depois, navegue para https://portal.gupy.io e faça login.")
        print("[LOGIN] Quando terminar AMBOS, volte aqui e aperte ENTER.")
        
        input() # Pausa a execução aguardando você terminar
        
        # Salva todos os cookies e tokens em um arquivo
        await context.storage_state(path="auth_state.json")
        print("\nSessão salva com sucesso em 'auth_state.json'! O robô agora está logado.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(salvar_sessao())