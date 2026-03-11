import asyncio
import json
import re
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from ai_service import nuvem_client

async def preencher_campos_da_tela(page: Page, dados_usuario: dict):
    campos_browser = await page.evaluate("""
        () => {
            return Array.from(document.querySelectorAll('input, textarea, select'))
                .filter(el => el.offsetWidth > 0 && el.offsetHeight > 0 && !el.value)
                .map(el => {
                    const label = document.querySelector(`label[for="${el.id}"]`)?.innerText || 
                                 el.closest('label')?.innerText || 
                                 el.placeholder || el.ariaLabel || '';
                    return { id: el.id, name: el.name, label: label.trim(), tipo: el.type };
                }).filter(c => c.label.length > 0 && c.id);
        }
    """)

    if not campos_browser: 
        return

    perfil = dados_usuario.get("perfil", {})
    
    prompt = f"""
    Responda APENAS com um JSON válido no formato {{"id_do_campo": "valor a preencher"}}.
    Preencha os campos baseando-se nestes dados do candidato: {json.dumps(perfil)}
    Campos encontrados na tela: {json.dumps(campos_browser)}
    """
    
    try:
        response = await nuvem_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" },
            temperature=0.1
        )
        respostas = json.loads(response.choices[0].message.content)

        for cid, valor in respostas.items():
            if valor:
                elemento = page.locator(f"#{cid}").first
                if await elemento.is_visible():
                    tag_name = await elemento.evaluate("el => el.tagName.toLowerCase()")
                    if tag_name in ["input", "textarea"]:
                        await elemento.fill(str(valor))
                    elif tag_name == "select":
                        await elemento.select_option(label=str(valor))
                    await asyncio.sleep(0.3)
                    
    except Exception as e:
        print(f"      [AVISO] Falha no preenchimento inteligente: {e}")

async def aplicar_linkedin_simplificado(page: Page, dados_usuario: dict) -> str:
    print("   - [APLICAÇÃO] Modal aberto. Executando preenchimento e navegação...")
    
    for etapa in range(8):
        try:
            await asyncio.sleep(2)
            
            await preencher_campos_da_tela(page, dados_usuario)

            botoes = {
                "enviar": page.get_by_role("button", name=re.compile(r"Enviar candidatura|Submit application", re.I)),
                "avancar": page.get_by_role("button", name=re.compile(r"Avançar|Próximo|Next|Continue", re.I)),
                "revisar": page.get_by_role("button", name=re.compile(r"Revisar|Review", re.I))
            }

            if await botoes["enviar"].count() > 0 and await botoes["enviar"].first.is_visible():
                await botoes["enviar"].first.click()
                await asyncio.sleep(3)
                
                btn_fechar = page.get_by_role("button", name=re.compile(r"Descartar|Fechar|Close", re.I))
                if await btn_fechar.count() > 0 and await btn_fechar.first.is_visible():
                    await btn_fechar.first.click()
                    
                return "Aplicado"
            
            elif await botoes["avancar"].count() > 0 and await botoes["avancar"].first.is_visible():
                await botoes["avancar"].first.click()
                
            elif await botoes["revisar"].count() > 0 and await botoes["revisar"].first.is_visible():
                await botoes["revisar"].first.click()
                
            else:
                if await page.get_by_text(re.compile(r"Candidatura enviada|Application submitted", re.I)).count() > 0:
                    return "Aplicado"
                break
                
        except Exception as e:
            print(f"      [AVISO] Erro na etapa {etapa} do formulário: {e}")
            break
            
    return "Requer atenção manual (Formulário complexo ou erro de validação)"

async def iniciar_aplicacao(page: Page, url_vaga: str, plataforma: str, dados_usuario: dict) -> str:
    try:
        if plataforma == "LinkedIn":
            await asyncio.sleep(4) # Tempo extra para o LinkedIn processar tudo

            # [FORÇA BRUTA JS] Injeta um script que tenta clicar no botão de todas as formas possíveis
            sucesso_clique = await page.evaluate("""
                () => {
                    // 1. Tenta pelo ID que você encontrou
                    let btn = document.querySelector('#jobs-apply-button-id');
                    
                    // 2. Se não achou, tenta por seletores de classe comuns
                    if (!btn) btn = document.querySelector('.jobs-apply-button button');
                    
                    // 3. Se ainda não achou, varre todos os botões por texto
                    if (!btn) {
                        let botoes = Array.from(document.querySelectorAll('button'));
                        btn = botoes.find(b => {
                            let t = b.innerText.toLowerCase();
                            return t.includes('simplificada') || t.includes('easy apply');
                        });
                    }

                    if (btn && btn.offsetParent !== null) {
                        btn.scrollIntoView();
                        btn.click();
                        return true;
                    }
                    return false;
                }
            """)

            if sucesso_clique:
                print("   - [APLICAÇÃO] Clique disparado via injeção de script!")
                await asyncio.sleep(2)
                return await aplicar_linkedin_simplificado(page, dados_usuario)
            else:
                # Se falhar, talvez o botão esteja em um iframe (comum em vagas de terceiros)
                return "Falha: Botão não detectado na camada principal. Vaga pode ser externa."

        return "Plataforma não suportada."
    except Exception as e:
        return f"Erro: {str(e)}"
    try:
        if plataforma == "LinkedIn":
            await asyncio.sleep(3) 

            # [MUDANÇA] Busca explícita pelo ID exato fornecido, iterando para encontrar o visível
            botoes_aplicar = await page.locator("#jobs-apply-button-id").all()
            botao_visivel = None
            
            for btn in botoes_aplicar:
                if await btn.is_visible():
                    botao_visivel = btn
                    break

            if botao_visivel:
                print("   - [APLICAÇÃO] Botão detectado por ID!")
                await botao_visivel.click()
                await asyncio.sleep(2) 
                return await aplicar_linkedin_simplificado(page, dados_usuario)
            
            return "Falha: O botão de candidatura não foi encontrado ou é redirecionamento externo."
            
        return "Plataforma não suportada para auto-apply"
        
    except Exception as e:
        return f"Erro na orquestração: {str(e)}"