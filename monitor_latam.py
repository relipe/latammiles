import os
import requests
import time
from playwright.sync_api import sync_playwright

def get_latam_flights():
    with sync_playwright() as p:
        # Lança o navegador com argumentos para parecer menos um bot
        browser = p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox'
        ])
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )

        page = context.new_page()
        
        # URL BSB -> POA | 14/10 a 24/10 de 2026
        url = "https://www.latamairlines.com/br/pt/ofertas-voos?origin=BSB&destination=POA&outbound=2026-10-14&inbound=2026-10-24&adt=1&chd=0&inf=0&trip=RT&cabin=Economy&redemption=false&sort=RECOMMENDED"
        
        try:
            # Acessa a página
            page.goto(url, wait_until="domcontentloaded", timeout=90000)
            
            # Simula um scroll leve para "acordar" os elementos dinâmicos
            page.mouse.wheel(0, 500)
            time.sleep(20) # A LATAM demora para processar os voos no servidor do GitHub

            # Tenta encontrar qualquer elemento que contenha "R$" (Moeda)
            # Este seletor é mais estável que nomes de classes CSS que mudam
            price_selector = "span:has-text('R$')"
            page.wait_for_selector(price_selector, timeout=60000)

            # Captura os textos de todos os cards de voo encontrados
            # Usamos um seletor que pega o container pai do preço
            cards = page.query_selector_all("li[class*='Card']") or page.query_selector_all("[id^='itinerary-card-']")
            
            results = []
            for card in cards:
                text = card.inner_text().replace('\n', ' ')
                # Filtra apenas linhas que contenham preços para limpar o log
                if "R$" in text:
                    results.append(f"✈️ {text[:100]}...") # Pega o início da descrição do voo

            browser.close()
            
            if not results:
                return "Página carregou, mas nenhum voo foi extraído (possível alteração no layout)."
                
            return "\n\n".join(results[:10]) # Limita aos 10 primeiros para não estourar o Telegram

        except Exception as e:
            # Se der erro, tenta tirar o print do que o robô está vendo
            browser.close()
            return f"Erro na captura: O site da LATAM bloqueou o acesso ou demorou demais.\nDetalhe: {str(e)[:100]}"

def send_telegram(message):
    token = os.environ.get('TG_TOKEN')
    chat_id = os.environ.get('TG_CHAT')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id, 
            "text": f"📊 **Relatório LATAM BSB-POA**\n{message}",
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload)

if __name__ == "__main__":
    dados = get_latam_flights()
    send_telegram(dados)
