import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

URLS = [
    {
        "label": "IDA BSB → POA",
        "url": "https://www.latamairlines.com/br/pt/oferta-voos?origin=BSB&destination=POA&outbound=2026-10-14&adt=1&chd=0&inf=0&cabin=Economy&redemption=false"
    },
    {
        "label": "VOLTA POA → BSB",
        "url": "https://www.latamairlines.com/br/pt/oferta-voos?origin=POA&destination=BSB&outbound=2026-10-24&adt=1&chd=0&inf=0&cabin=Economy&redemption=false"
    }
]

async def main():
    print("\n✈️ Monitor LATAM — GRAPHQL DUMP")
    print("🕒", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    captured = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ]
        )

        context = await browser.new_context(
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            )
        )

        page = await context.new_page()

        async def on_response(response):
            try:
                ct = response.headers.get("content-type", "")
                if "application/json" in ct:
                    data = await response.json()
                    captured.append({
                        "url": response.url,
                        "status": response.status,
                        "data": data
                    })
            except:
                pass

        page.on("response", on_response)

        for item in URLS:
            print(f"\n🔍 Acessando {item['label']}")
            print(item["url"])

            await page.goto(item["url"], wait_until="networkidle")

            # Interação neutra para acordar o React
            await page.mouse.wheel(0, 800)
            await page.wait_for_timeout(10000)

        cookies = await context.cookies()
        print("\n🍪 COOKIES DE SESSÃO:")
        for c in cookies:
            print(f"{c['name']}={c['value'][:80]}...")

        await browser.close()

    print("\n📦 JSON CAPTURADOS:")
    if not captured:
        print("❌ Nenhuma resposta JSON capturada")
    else:
        for i, c in enumerate(captured, 1):
            print(f"\n--- JSON #{i} ---")
            print("URL:", c["url"])
            print("STATUS:", c["status"])
            print(json.dumps(c["data"], indent=2)[:5000])

if __name__ == "__main__":
    asyncio.run(main())
