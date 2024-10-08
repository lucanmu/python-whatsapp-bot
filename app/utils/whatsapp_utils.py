import logging
from flask import current_app, jsonify
import json
import requests
import re


def log_http_response(response):
    """
    Função para registrar detalhes de uma resposta HTTP no log.
    """
    logging.info(f"Status: {response.status_code}")  # Registra o status da resposta
    logging.info(f"Content-type: {response.headers.get('content-type')}")  # Registra o tipo de conteúdo
    logging.info(f"Body: {response.text}")  # Registra o corpo da resposta


def get_text_message_input(recipient, text):
    """
    Monta o corpo da mensagem de texto para ser enviado via WhatsApp API.
    """
    return json.dumps(
        {
            "messaging_product": "whatsapp",  # Define que o produto de mensagem é o WhatsApp
            "recipient_type": "individual",  # Tipo de destinatário (individual)
            "to": recipient,  # Número de telefone do destinatário
            "type": "text",  # Tipo de mensagem é texto
            "text": {"preview_url": False, "body": text},  # Corpo da mensagem de texto sem pré-visualização de URLs
        }
    )


def generate_response(response):
    """
    Gera uma resposta processada. No exemplo, retorna o texto em letras maiúsculas.
    """
    return response.upper()


def send_message(data):
    """
    Envia uma mensagem através da API do WhatsApp, usando o token de autenticação e o número de telefone configurados.
    """
    headers = {
        "Content-type": "application/json",  # Define o tipo de conteúdo como JSON
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",  # Usa o token de acesso da aplicação
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"  # Monta a URL da API do WhatsApp

    try:
        # Faz a requisição POST para a API com timeout de 10 segundos
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )
        # Verifica se a resposta HTTP foi bem-sucedida
        response.raise_for_status()  
    except requests.Timeout:
        # Caso ocorra um timeout, registra o erro no log e retorna uma resposta de erro (408)
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except requests.RequestException as e:
        # Captura qualquer outra exceção relacionada à requisição e registra o erro
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Se a requisição foi bem-sucedida, registra a resposta no log
        log_http_response(response)
        return response


def process_text_for_whatsapp(text):
    """
    Processa o texto recebido para formatá-lo de acordo com o estilo do WhatsApp.
    Remove certos padrões e formata palavras em negrito.
    """
    # Remove o conteúdo entre colchetes
    pattern = r"\【.*?\】"
    text = re.sub(pattern, "", text).strip()  # Substitui o padrão por uma string vazia e remove espaços em branco

    # Padrão para encontrar negrito representado por asteriscos duplos
    pattern = r"\*\*(.*?)\*\*"
    replacement = r"*\1*"  # Substitui por negrito no estilo do WhatsApp (um asterisco)

    # Substitui as ocorrências do padrão no texto
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text


def process_whatsapp_message(body):
    """
    Processa uma mensagem recebida do WhatsApp.
    """
    # Extrai o ID do WhatsApp (wa_id) e o nome do contato da mensagem recebida
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    # Extrai o corpo da mensagem recebida
    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_body = message["text"]["body"]

    # TODO: implementar função personalizada aqui
    response = generate_response(message_body)  # Gera uma resposta personalizada

    # Integração com OpenAI (comentado no momento)
    # response = generate_response(message_body, wa_id, name)
    # response = process_text_for_whatsapp(response)

    # Monta a mensagem de resposta e a envia
    data = get_text_message_input(current_app.config["RECIPIENT_WAID"], response)
    send_message(data)


def is_valid_whatsapp_message(body):
    """
    Verifica se a mensagem recebida do webhook tem uma estrutura válida de mensagem do WhatsApp.
    """
    return (
        body.get("object")  # Verifica se a chave "object" existe
        and body.get("entry")  # Verifica se a chave "entry" existe
        and body["entry"][0].get("changes")  # Verifica se "changes" existe
        and body["entry"][0]["changes"][0].get("value")  # Verifica se "value" existe
        and body["entry"][0]["changes"][0]["value"].get("messages")  # Verifica se "messages" existe
        and body["entry"][0]["changes"][0]["value"]["messages"][0]  # Verifica se a mensagem está presente
    )
