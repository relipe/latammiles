import os
import requests
from playwright.sync_api import sync_playwright

def get_latam_price():
    with sync_playwright() as p:
        # Launch browser (headless=True para rodar no GitHub)
        browser = p.chromium.launch(headless=True)
        # Configura um User-Agent real para evitar bloqueios simples
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # URL Direta BSB -> POA (14/10 a 24/10)
        url = "https://www.latamairlines.com/br/pt/ofertas-voos?origin=BSB&destination=POA&outbound=2025-10-14&inbound=2025-10-24&adt=1&chd=0&inf=0&trip=RT&cabin=Economy&redemption=false&sort=RECOMMENDED"
        
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            # Espera o seletor de preço carregar (ajustado para o padrão da LATAM)
            page.wait_for_selector('.display-price-amount', timeout=30000)
            
            # Pega todos os preços da página e encontra o menor
            prices = page.locator('.display-price-amount').all_inner_texts()
            # Limpa a string (remove pontos e vírgulas para converter se necessário)
            clean_prices = [p.replace('.', '').replace(',', '.') for p in prices]
            menor_preco = min([float(p) for p in clean_prices if p])
            
            browser.close()
            return f"R$ {menor_preco:.2f}".replace('.', ',')
        except Exception as e:
            browser.close()
            return f"Erro ao capturar preço: {str(e)}"

def send_telegram(message):
    token = os.environ['TG_TOKEN']
    chat_id = os.environ['TG_CHAT']
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, json=payload)

if __name__ == "__main__":
    preco = get_latam_price()
    msg = f"✈️ Monitor LATAM (BSB-POA)\n📅 14/10 a 24/10\n💰 Menor preço hoje: {preco}"
    send_telegram(msg)
