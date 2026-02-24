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
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"\n✈️ Monitor LATAM — GRAPHQL DUMP")
    print(f"🕒 {timestamp}\n")

    graphql_calls = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
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

        # Intercepta TODAS as respostas
        page.on("response", lambda r: asyncio.create_task(handle_response(r, graphql_calls)))

        for item in URLS:
            print(f"🔍 Acessando {item['label']}")
            print(item["url"])
            await page.goto(item["url"], wait_until="networkidle")
            await asyncio.sleep(10)  # tempo real para XHR/GraphQL

        # Dump cookies reais
        cookies = await context.cookies()
        print("\n🍪 COOKIES DE SESSÃO:")
        for c in cookies:
            print(f"{c['name']}={c['value'][:80]}...")

        await browser.close()

    # Dump GraphQL
    print("\n📦 GRAPHQL / XHR CAPTURADOS:")
    if not graphql_calls:
        print("⚠️ Nenhuma chamada GraphQL/XHR JSON capturada")
    else:
        for i, call in enumerate(graphql_calls, 1):
            print(f"\n--- REQUEST #{i} ---")
            print("URL:", call["url"])
            print("STATUS:", call["status"])
            print("METHOD:", call["method"])
            print("HEADERS:", json.dumps(call["headers"], indent=2))
            print("BODY:", json.dumps(call["body"], indent=2) if call["body"] else "N/A")
            print("RESPONSE:", json.dumps(call["response"], indent=2)[:5000])

async def handle_response(response, store):
    try:
        url = response.url.lower()
        headers = response.request.headers
        method = response.request.method

        # Captura qualquer JSON (sem filtro)
        if "application/json" in response.headers.get("content-type", ""):
            try:
                body = response.request.post_data_json
            except:
                body = response.request.post_data

            data = await response.json()

            store.append({
                "url": response.url,
                "status": response.status,
                "method": method,
                "headers": headers,
                "body": body,
                "response": data
            })
    except:
        pass

if __name__ == "__main__":
    asyncio.run(main())
