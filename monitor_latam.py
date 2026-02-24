

from playwright.sync_api import sync_playwright
from datetime import datetime
import sys

# ==============================
# CONFIGURAÇÃO DOS VOOS
# ==============================

URL_IDA = (
    "https://www.latamairlines.com/br/pt/oferta-voos"
    "?origin=BSB&destination=POA"
    "&outbound=2026-10-14"
    "&adt=1&chd=0&inf=0"
    "&cabin=Economy"
    "&redemption=false"
)

URL_VOLTA = (
    "https://www.latamairlines.com/br/pt/oferta-voos"
    "?origin=POA&destination=BSB"
    "&outbound=2026-10-24"
    "&adt=1&chd=0&inf=0"
    "&cabin=Economy"
    "&redemption=false"
)


# ==============================
# FUNÇÃO PRINCIPAL
# ==============================

def capturar_voos(url, titulo):
    print(f"\n🔍 Acessando {titulo}")
    print(url)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        page = browser.new_page(
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            )
        )

        response = page.goto(url, wait_until="networkidle")
        print(f"HTTP STATUS: {response.status if response else 'N/A'}")

        # Aguarda carregamento dinâmico da LATAM
        page.wait_for_timeout(6000)

        try:
            page.wait_for_selector("article", timeout=20000)
        except:
            print("⚠️ Nenhum <article> encontrado no DOM")
            browser.close()
            return []

        # CAPTURA CRUA DO TEXTO
        voos = page.evaluate("""
        () => {
            const cards = Array.from(document.querySelectorAll('article'));
            return cards.map(card => card.innerText);
        }
        """)

        print("\n===== INÍCIO DOS VOOS CAPTURADOS =====\n")

        for i, voo in enumerate(voos, 1):
            print(f"--- VOO {i} ---")
            print(voo)
            print("---------------\n")

        print("===== FIM DOS VOOS CAPTURADOS =====\n")

        browser.close()
        return voos


# ==============================
# EXECUÇÃO
# ==============================

def main():
    print("✈️ Monitor LATAM (DUMP COMPLETO)")
    print(f"🕒 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    capturar_voos(URL_IDA, "IDA BSB → POA")
    capturar_voos(URL_VOLTA, "VOLTA POA → BSB")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("❌ ERRO GERAL:")
        print(e)
        sys.exit(1)
      
