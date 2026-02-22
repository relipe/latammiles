import os
import requests
import time
from playwright.sync_api import sync_playwright

def get_latam_flights():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # URL BSB -> POA | 14/10 a 24/10 de 2026
        url = "https://www.latamairlines.com/br/pt/ofertas-voos?origin=BSB&destination=POA&outbound=2026-10-14&inbound=2026-10-24&adt=1&chd=0&inf=0&trip=RT&cabin=Economy&redemption=false&sort=RECOMMENDED"
        
        try:
            page.goto(url, wait_until="networkidle", timeout=90000)
            time.sleep(15) # Tempo extra para carregar todos os cards de voo
            
            # Espera o container de voos aparecer
            page.wait_for_selector("[class*='FlightInfo']", timeout=45000)

            # Captura os blocos de voos (cards)
            flights = page.query_selector_all("[id^='itinerary-card-outbound-']")
            
            flight_data = []
            for flight in flights:
                try:
                    # Tenta pegar o horário e o preço dentro de cada card
                    time_info = flight.query_selector("[class*='time']").inner_text() if flight.query_selector("[class*='time']") else "N/A"
                    price_info = flight.query_selector(".display-price-amount").inner_text() if flight.query_selector(".display-price-amount") else "N/A"
                    
                    if price_info != "N/A":
                        flight_data.append(f"🕒 {time_info.split()[0]} - 💰 R$ {price_info}")
                except:
                    continue

            browser.close()
            return "\n".join(flight_data) if flight_data else "Nenhum voo listado ou erro de carregamento."

        except Exception as e:
            browser.close()
            return f"Erro na captura: {str(e)}"

def send_telegram(message):
    # Nomes das variáveis alterados conforme pedido
    token = os.environ.get('TG_TOKEN')
    chat_id = os.environ.get('TG_CHAT')
    
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        text = f"✈️ **LATAM: BSB -> POA**\n📅 14/10 a 24/10/2026\n\n{message}"
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

if __name__ == "__main__":
    relatorio_voos = get_latam_flights()
    send_telegram(relatorio_voos)
