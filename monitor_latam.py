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
# VOOS
# =========================
VOOS = [
    {
        "nome": "IDA BSB → POA",
        "url": "https://www.latamairlines.com/br/pt/oferta-voos?origin=BSB&destination=POA&outbound=2026-10-14&adt=1&chd=0&inf=0&cabin=Economy&redemption=false",
        "horario": "09:30"
    },
    {
        "nome": "VOLTA POA → BSB",
        "url": "https://www.latamairlines.com/br/pt/oferta-voos?origin=POA&destination=BSB&outbound=2026-10-24&adt=1&chd=0&inf=0&cabin=Economy&redemption=false",
        "horario": "17:25"
    }
]

# =========================
# TELEGRAM
# =========================
def enviar_telegram(msg: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=30)

# =========================
# UTIL
# =========================
def normalizar_hora(iso_dt: str):
    # ex: 2026-10-14T09:30:00-03:00 -> 09:30
    if not iso_dt or "T" not in iso_dt:
        return None
    return iso_dt.split("T")[1][:5]

def print_json_preview(obj, limit=1500):
    txt = json.dumps(obj, ensure_ascii=False)
    print(txt[:limit] + ("..." if len(txt) > limit else ""))

# =========================
# CAPTURA VIA XHR
# =========================
def capturar_voos_por_xhr(url, horario_desejado):
    resultados = []

    def on_response(resp):
        try:
            if resp.request.resource_type not in ("xhr", "fetch"):
                return
            if resp.status != 200:
                return

            data = resp.json()  # pode lançar exceção
            print("\n📦 XHR JSON detectado:")
            print(f"➡️ {resp.url}")
            print_json_preview(data)

            # Heurística flexível para encontrar ofertas/segmentos
            # Tentamos caminhos comuns sem depender de um schema rígido
            def walk(obj):
                if isinstance(obj, dict):
                    # possíveis campos de preço
                    price = None
                    currency = None
                    if "price" in obj and isinstance(obj["price"], (int, float, dict)):
                        price = obj["price"]
                    if "currency" in obj:
                        currency = obj["currency"]

                    # possíveis segmentos
                    if "segments" in obj and isinstance(obj["segments"], list):
                        for seg in obj["segments"]:
                            dep = seg.get("departure") or seg.get("departureDateTime") or seg.get("departureDate")
                            h = normalizar_hora(dep) if isinstance(dep, str) else None
                            if h == horario_desejado:
                                resultados.append({
                                    "horario": h,
                                    "price": price,
                                    "currency": currency,
                                    "raw": obj
                                })

                    for v in obj.values():
                        walk(v)

                elif isinstance(obj, list):
                    for i in obj:
                        walk(i)

            walk(data)

        except Exception:
            pass  # silencioso: nem toda XHR é JSON de oferta

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

        print(f"\n🔍 Acessando (browser real): {url}")
        page.goto(url, timeout=60000)
        page.wait_for_timeout(20000)  # aguarda XHRs

        browser.close()

    return resultados

# =========================
# MAIN
# =========================
def main():
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

    linhas = [
        "✈️ Monitor LATAM (XHR)",
        f"🕒 {agora}",
        ""
    ]

    for voo in VOOS:
        print(f"\n==== {voo['nome']} | Horário alvo: {voo['horario']} ====")
        encontrados = capturar_voos_por_xhr(voo["url"], voo["horario"])

        if not encontrados:
            linhas.append(f"{voo['nome']}")
            linhas.append(f"Horário {voo['horario']} não encontrado")
            linhas.append("")
            continue

        # agrega o primeiro encontrado (normalmente há duplicatas)
        item = encontrados[0]
        preco = item.get("price")
        moeda = item.get("currency")

        linhas.append(f"{voo['nome']}")
        linhas.append(f"Horário: {item['horario']}")
        if isinstance(preco, dict):
            linhas.append(f"Preço: {json.dumps(preco, ensure_ascii=False)}")
        else:
            linhas.append(f"Preço: {preco} {moeda or ''}".strip())
        linhas.append("")

    msg = "\n".join(linhas)
    print("\n===== RESUMO =====\n")
    print(msg)
    enviar_telegram(msg)

if __name__ == "__main__":
    main()
