import os
import re
import datetime
import requests
from playwright.sync_api import sync_playwright

BOT_TOKEN = os.environ["TG_TOKEN"]
CHAT_ID = os.environ["TG_CHAT"]

VOOS = [
    {
        "nome": "IDA BSB → POA",
        "url": "https://www.latamairlines.com/br/pt/oferta-voos?origin=BSB&destination=POA&outbound=2026-10-14&adt=1&chd=0&inf=0&cabin=Economy",
        "horario": "09:30"
    },
    {
        "nome": "VOLTA POA → BSB",
        "url": "https://www.latamairlines.com/br/pt/oferta-voos?origin=POA&destination=BSB&outbound=2026-10-24&adt=1&chd=0&inf=0&cabin=Economy",
        "horario": "17:25"
    }
]

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": msg
    })

def extrair_preco(texto):
    match = re.search(r"brl\s*\d{1,3}(\.\d{3})*,\d{2}", texto.lower())
    return match.group() if match else "não encontrado"

def main():
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    mensagens = [f"✈️ Monitor LATAM\n🕒 {agora}\n"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(locale="pt-BR")

        for voo in VOOS:
            page.goto(voo["url"], timeout=60000)
            page.wait_for_timeout(15000)  # tempo para JS carregar

            texto = page.inner_text("body")

            if voo["horario"] not in texto:
                mensagens.append(
                    f"{voo['nome']}\nHorário {voo['horario']} não encontrado\n"
                )
                continue

            preco = extrair_preco(texto)

            mensagens.append(
                f"{voo['nome']}\n"
                f"Horário: {voo['horario']}\n"
                f"Preço: {preco}\n"
            )

        browser.close()

    enviar_telegram("\n".join(mensagens))

if __name__ == "__main__":
    main()
