import requests
import hashlib
import os
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["TG_TOKEN"]
CHAT_ID = os.environ["TG_CHAT"]

VOOS = [
    {
        "nome": "✈️ IDA LA3432 (14/10/2026 BSB → POA)",
        "url": "https://www.latamairlines.com/br/pt/oferta-voos?origin=BSB&destination=POA&outbound=2026-10-14&adt=1&chd=0&inf=0&cabin=Economy&redemption=true"
    },
    {
        "nome": "↩️ VOLTA LA3225 (24/10/2026 POA → BSB)",
        "url": "https://www.latamairlines.com/br/pt/oferta-voos?origin=POA&destination=BSB&outbound=2026-10-24&adt=1&chd=0&inf=0&cabin=Economy&redemption=true"
    }
]

def extrair_milhas(html):
    soup = BeautifulSoup(html, "html.parser")
    texto = soup.get_text(" ", strip=True)
    candidatos = []
    for palavra in texto.split():
        p = palavra.replace(".", "").replace(",", "")
        if p.isdigit() and len(p) >= 4:
            candidatos.append(int(p))
    return min(candidatos) if candidatos else None

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

mensagem = ""
mudou = False

for voo in VOOS:
    r = requests.get(voo["url"], timeout=30)
    milhas = extrair_milhas(r.text)

    if milhas is None:
        continue

    hash_atual = hashlib.md5(str(milhas).encode()).hexdigest()
    arquivo = f"{voo['nome']}.txt"

    try:
        with open(arquivo, "r") as f:
            hash_antigo = f.read()
    except:
        hash_antigo = ""

    if hash_atual != hash_antigo:
        mudou = True
        mensagem += f"{voo['nome']}\n💺 {milhas:,} milhas\n\n"
        with open(arquivo, "w") as f:
            f.write(hash_atual)

if mudou:
    enviar_telegram("🚨 ALTERAÇÃO DE MILHAS LATAM\n\n" + mensagem)
