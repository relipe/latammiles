import requests
import hashlib
import os
import re
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["TG_TOKEN"]
CHAT_ID = os.environ["TG_CHAT"]

VOOS = [
    {
        "nome": "✈️ IDA LA3432 (14/10/2026 BSB → POA)",
        "url": "https://www.latamairlines.com/br/pt/oferta-voos?origin=BSB&destination=POA&outbound=2026-10-14&adt=1&chd=0&inf=0&cabin=Economy&redemption=false"
    },
    {
        "nome": "↩️ VOLTA LA3225 (24/10/2026 POA → BSB)",
        "url": "https://www.latamairlines.com/br/pt/oferta-voos?origin=POA&destination=BSB&outbound=2026-10-24&adt=1&chd=0&inf=0&cabin=Economy&redemption=false"
    }
]

def extrair_preco_reais(html):
    """
    Extrai o preço FINAL em BRL (por passageiro, com taxas e impostos)
    Exemplo esperado no HTML:
    BRL 595,77
    Por passageiro
    Inclui taxas e impostos
    """
    texto = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    texto = re.sub(r"\s+", " ", texto)

    padrao = re.compile(
        r"(BRL\s?\d{1,3}(\.\d{3})*,\d{2}).{0,80}?Por passageiro.{0,80}?Inclui taxas e impostos",
        re.IGNORECASE
    )

    match = padrao.search(texto)
    if not match:
        return None

    valor_txt = match.group(1)
    valor = (
        valor_txt.replace("BRL", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )

    return float(valor)

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": msg
        },
        timeout=10
    )

mensagem = "✈️ VALORES ATUAIS — LATAM (REAI$)\n\n"

for voo in VOOS:
    r = requests.get(voo["url"], timeout=30)
    preco = extrair_preco_reais(r.text)

    if preco is None:
        mensagem += f"{voo['nome']}\n❌ Preço não encontrado\n\n"
        continue

    hash_atual = hashlib.md5(str(preco).encode()).hexdigest()
    arquivo = f"{voo['nome']}.txt"

    try:
        with open(arquivo, "r") as f:
            hash_antigo = f.read()
    except:
        hash_antigo = ""

    status = "🔺 ALTEROU" if hash_atual != hash_antigo else "— sem alteração"

    mensagem += (
        f"{voo['nome']}\n"
        f"💰 BRL {preco:,.2f} ({status})\n\n"
    )

    if hash_atual != hash_antigo:
        with open(arquivo, "w") as f:
            f.write(hash_atual)

# SEMPRE envia
enviar_telegram(mensagem)
