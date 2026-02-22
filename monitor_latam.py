import requests
import hashlib
import smtplib
from email.message import EmailMessage
import os
from bs4 import BeautifulSoup

VOOS = [
    {
        "nome": "IDA LA3432",
        "url": "https://www.latamairlines.com/br/pt/oferta-voos?origin=BSB&destination=POA&outbound=2026-10-14&adt=1&chd=0&inf=0&cabin=Economy&redemption=true"
    },
    {
        "nome": "VOLTA LA3225",
        "url": "https://www.latamairlines.com/br/pt/oferta-voos?origin=POA&destination=BSB&outbound=2026-10-24&adt=1&chd=0&inf=0&cabin=Economy&redemption=true"
    }
]

def extrair_milhas(html):
    soup = BeautifulSoup(html, "html.parser")
    texto = soup.get_text(" ", strip=True)
    for palavra in texto.split():
        if palavra.replace(".", "").isdigit() and len(palavra) >= 4:
            return palavra
    return "N/A"

def enviar_email(mensagem):
    email = EmailMessage()
    email["Subject"] = "🚨 Alteração de milhas LATAM"
    email["From"] = os.environ["EMAIL_FROM"]
    email["To"] = os.environ["EMAIL_TO"]
    email.set_content(mensagem)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.environ["EMAIL_FROM"], os.environ["EMAIL_PASS"])
        smtp.send_message(email)

mensagem_alerta = ""
mudou = False

for voo in VOOS:
    r = requests.get(voo["url"], timeout=30)
    milhas = extrair_milhas(r.text)
    hash_atual = hashlib.md5(milhas.encode()).hexdigest()

    arquivo = f"{voo['nome']}.txt"

    try:
        with open(arquivo, "r") as f:
            hash_antigo = f.read()
    except:
        hash_antigo = ""

    if hash_atual != hash_antigo:
        mudou = True
        mensagem_alerta += f"{voo['nome']} mudou para {milhas} milhas\n"
        with open(arquivo, "w") as f:
            f.write(hash_atual)

if mudou:
    enviar_email(mensagem_alerta)
