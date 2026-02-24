import os
import json
import datetime
import requests
from playwright.sync_api import sync_playwright

# =========================
# TELEGRAM (NÃO ALTERAR)
# =========================
BOT_TOKEN = os.environ["TG_TOKEN"]
CHAT_ID = os.environ["TG_CHAT"]

# =========================
# URLS
# =========================
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

# =========================
# TELEGRAM
# =========================
def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=30
    )

# =========================
# DUMP XHR SEM FILTRO
# =========================
def dump_xhr(url, nome):
    capturados = []

    def on_response(resp):
        try:
            if resp.request.resource_type not in ("xhr", "fetch"):
                return

            print("\n==============================")
            print(f"📦 XHR CAPTURADO ({nome})")
            print(f"URL: {resp.url}")
            print(f"STATUS: {resp.status}")

            try:
                data = resp.json()
                texto = json.dumps(data, ensure_ascii=False)
                print(texto[:3000])
                capturados.append(
                    f"URL: {resp.url}\n{texto[:1500]}"
                )
            except Exception:
                print("⚠️ Resposta não é JSON")

        except Exception as e:
            print("Erro ao processar XHR:", e)

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
        page.on("response", on_response)

        print(f"\n🔍 Acessando {nome}")
        page.goto(url, timeout=60000)
        page.wait_for_timeout(20000)

        browser.close()

    return capturados

# =========================
# MAIN
# =========================
def main():
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    resumo = [
        "✈️ Monitor LATAM — DUMP XHR",
        f"🕒 {agora}",
        ""
    ]

    for item in URLS:
        dumps = dump_xhr(item["url"], item["nome"])

        resumo.append(f"🔍 {item['nome']}")
        if not dumps:
            resumo.append("Nenhum XHR JSON capturado")
        else:
            resumo.append(f"{len(dumps)} XHR JSON capturados")
            resumo.append(dumps[0][:1200])  # só o primeiro no Telegram
        resumo.append("-" * 30)

    mensagem = "\n".join(resumo)

    print("\n===== RESUMO TELEGRAM =====\n")
    print(mensagem)

    enviar_telegram(mensagem)

if __name__ == "__main__":
    main()
