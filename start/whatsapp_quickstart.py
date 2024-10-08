import json
from dotenv import load_dotenv
import os
import requests
import aiohttp
import asyncio

# --------------------------------------------------------------
# Carrega variáveis de ambiente
# --------------------------------------------------------------

load_dotenv()  # Carrega as variáveis de ambiente a partir do arquivo .env

# Define as variáveis de ambiente necessárias para autenticação e envio de mensagens
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
RECIPIENT_WAID = os.getenv("RECIPIENT_WAID")  # ID do destinatário no WhatsApp
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")  # ID do número de telefone vinculado à API
VERSION = os.getenv("VERSION")  # Versão da API

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")

# --------------------------------------------------------------
# Enviar uma mensagem de template no WhatsApp
# --------------------------------------------------------------


def send_whatsapp_message():
    """
    Função para enviar uma mensagem de template no WhatsApp usando a API do Facebook.
    Utiliza o template "hello_world" que deve estar previamente configurado no WhatsApp Business.
    """
    # URL da API para envio de mensagens no WhatsApp
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    
    # Cabeçalhos da requisição, incluindo o token de acesso para autenticação
    headers = {
        "Authorization": "Bearer " + ACCESS_TOKEN,
        "Content-Type": "application/json",
    }
    
    # Dados da mensagem, incluindo o template "hello_world" e o idioma "en_US"
    data = {
        "messaging_product": "whatsapp",
        "to": RECIPIENT_WAID,  # Número do destinatário
        "type": "template",  # Tipo da mensagem (template)
        "template": {"name": "hello_world", "language": {"code": "en_US"}},  # Nome do template e idioma
    }
    
    # Envia a requisição POST para a API
    response = requests.post(url, headers=headers, json=data)
    return response


# Chama a função para enviar a mensagem de template e imprime o status da resposta
response = send_whatsapp_message()
print(response.status_code)
print(response.json())

# --------------------------------------------------------------
# Enviar uma mensagem de texto personalizada no WhatsApp
# --------------------------------------------------------------

# OBS: O destinatário deve ter respondido a uma mensagem antes de poder receber uma personalizada!


def get_text_message_input(recipient, text):
    """
    Gera o corpo da mensagem de texto personalizada no formato esperado pela API do WhatsApp.
    """
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",  # Enviar para um destinatário individual
            "to": recipient,  # Número do destinatário
            "type": "text",  # Tipo da mensagem (texto)
            "text": {"preview_url": False, "body": text},  # Texto da mensagem sem pré-visualização de URL
        }
    )


def send_message(data):
    """
    Função para enviar uma mensagem de texto personalizada ao WhatsApp usando a API.
    """
    # Cabeçalhos da requisição com o token de acesso e tipo de conteúdo JSON
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }

    # URL da API para envio de mensagens
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"

    # Envia a requisição POST para a API com os dados da mensagem
    response = requests.post(url, data=data, headers=headers)
    
    # Verifica o status da resposta e imprime o resultado
    if response.status_code == 200:
        print("Status:", response.status_code)
        print("Content-type:", response.headers["content-type"])
        print("Body:", response.text)
        return response
    else:
        print(response.status_code)
        print(response.text)
        return response


# Prepara os dados da mensagem de texto e envia a mensagem
data = get_text_message_input(
    recipient=RECIPIENT_WAID, text="Hello, this is a test message."
)

response = send_message(data)

# --------------------------------------------------------------
# Enviar uma mensagem de texto personalizada no WhatsApp de forma assíncrona
# --------------------------------------------------------------


# OBS: Não funciona no Jupyter!

async def send_message(data):
    """
    Função assíncrona para enviar uma mensagem de texto personalizada ao WhatsApp usando a API.
    """
    # Cabeçalhos da requisição com o token de acesso e tipo de conteúdo JSON
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }

    # Cria uma sessão assíncrona HTTP
    async with aiohttp.ClientSession() as session:
        # Monta a URL da API
        url = "https://graph.facebook.com" + f"/{VERSION}/{PHONE_NUMBER_ID}/messages"
        
        try:
            # Envia a requisição POST de forma assíncrona
            async with session.post(url, data=data, headers=headers) as response:
                # Verifica se a resposta foi bem-sucedida
                if response.status == 200:
                    print("Status:", response.status)
                    print("Content-type:", response.headers["content-type"])

                    # Obtém o corpo da resposta de forma assíncrona
                    html = await response.text()
                    print("Body:", html)
                else:
                    print(response.status)
                    print(response)
        except aiohttp.ClientConnectorError as e:
            # Trata erros de conexão com a API
            print("Connection Error", str(e))


# Gera o corpo da mensagem de texto personalizada
def get_text_message_input(recipient, text):
    """
    Gera o corpo da mensagem de texto personalizada no formato esperado pela API do WhatsApp.
    """
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )


# Prepara os dados da mensagem de texto personalizada
data = get_text_message_input(
    recipient=RECIPIENT_WAID, text="Hello, this is a test message."
)

# Cria um loop de eventos para enviar a mensagem de forma assíncrona
loop = asyncio.get_event_loop()
loop.run_until_complete(send_message(data))
loop.close()
