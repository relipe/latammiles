import requests
from bs4 import BeautifulSoup
import os
import datetime
import re
# =========================
# CONFIGURAÇÕES
# =========================
BOT_TOKEN = os.environ["TG_TOKEN"]
CHAT_ID = os.environ["TG_CHAT"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

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
# FUNÇÕES
# =========================
def buscar_preco(url):
    print(f"\n🔍 Acessando: {url}")

    r = requests.get(url, headers=HEADERS, timeout=30)

    print("HTTP STATUS:", r.status_code)

    html = r.text.lower()

    # 🚨 Detecta bloqueio explícito
    if "access denied" in html or "for security reasons" in html:
        print("🚫 BLOQUEIO DE SEGURANÇA DA LATAM")
        return "BLOQUEADO (Access Denied)"

    soup = BeautifulSoup(r.text, "html.parser")

    # 🔍 Extrai TODO o texto visível da página
    texto_completo = soup.get_text(separator="\n", strip=True)

    print("\n===== INÍCIO DO CONTEÚDO DA PÁGINA =====\n")
    print(texto_completo[:5000])  # limita para não explodir o console
    print("\n===== FIM DO CONTEÚDO DA PÁGINA =====\n")

    # Retorna um resumo para o Telegram
    return "Conteúdo capturado (ver console)"


def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem
    }
    r = requests.post(url, json=payload)
    r.raise_for_status()


# =========================
# EXECUÇÃO
# =========================
def main():
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

    mensagens = [f"✈️ Monitor LATAM\n🕒 {agora}\n"]

    for voo in VOOS:
        preco = buscar_preco(voo["url"])

        mensagens.append(
            f"{voo['nome']}\n"
            f"Horário: {voo['horario']}\n"
            f"Preço: {preco}\n"
        )

    mensagem_final = "\n".join(mensagens)

    print("\n📤 Enviando mensagem para o Telegram:")
    print(mensagem_final)

    enviar_telegram(mensagem_final)


if __name__ == "__main__":
    main()
