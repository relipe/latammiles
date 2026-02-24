import json
import zlib
from playwright.sync_api import sync_playwright

URLS = [
    {
        "nome": "IDA BSB → POA",
        "url": "https://www.latamairlines.com/br/pt/oferta-voos?origin=BSB&destination=POA&outbound=2026-10-14&adt=1&chd=0&inf=0&cabin=Economy&redemption=false"
    },
    {
        "nome": "VOLTA POA → BSB",
        "url": "https://www.latamairlines.com/br/pt/oferta-voos?origin=POA&destination=BSB&outbound=2026-10-24&adt=1&chd=0&inf=0&cabin=Economy&redemption=false"
    }
]

def try_decode_response(resp):
    """
    Tenta obter o corpo da resposta como texto:
    - tenta text()
    - se falhar, tenta buffer() e descompactar
    """
    try:
        return resp.text()
    except Exception:
        try:
            buf = resp.body()
            # tenta zlib (caso gzip/deflate)
            try:
                return zlib.decompress(buf, zlib.MAX_WBITS | 32).decode("utf-8", errors="ignore")
            except Exception:
                return buf[:4000].decode("utf-8", errors="ignore")
        except Exception:
            return "<não foi possível ler o corpo>"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        page = context.new_page()

        # --------- CAPTURA DE REQUESTS ----------
        def on_request(req):
            try:
                if req.method != "POST":
                    return

                headers = req.headers
                ct = headers.get("content-type", "").lower()

                # Logamos TODO POST (GraphQL, binário, etc.)
                print("\n================ REQUEST POST =================")
                print(f"URL: {req.url}")
                print(f"Content-Type: {ct}")
                print("Headers:")
                for k, v in headers.items():
                    print(f"  {k}: {v}")

                body = req.post_data
                if body:
                    print("\n--- BODY (request) ---")
                    print(body[:4000])
                else:
                    print("\n--- BODY (request) --- vazio")

            except Exception as e:
                print("Erro ao capturar request:", e)

        # --------- CAPTURA DE RESPONSES ----------
        def on_response(resp):
            try:
                req = resp.request
                if req.method != "POST":
                    return

                headers = resp.headers
                ct = headers.get("content-type", "").lower()

                print("\n================ RESPONSE =====================")
                print(f"URL: {resp.url}")
                print(f"STATUS: {resp.status}")
                print(f"Content-Type: {ct}")
                print("Headers:")
                for k, v in headers.items():
                    print(f"  {k}: {v}")

                body_txt = try_decode_response(resp)
                print("\n--- BODY (response) ---")
                print(body_txt[:6000])

            except Exception as e:
                print("Erro ao capturar response:", e)

        page.on("request", on_request)
        page.on("response", on_response)

        for item in URLS:
            print(f"\n\n🔍 Acessando {item['nome']}")
            print(item["url"])
            page.goto(item["url"], timeout=60000)
            page.wait_for_timeout(25000)  # aguarda chamadas de rede

        browser.close()

if __name__ == "__main__":
    main()
