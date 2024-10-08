import logging
import json

from flask import Blueprint, request, jsonify, current_app

# Importa o decorador de segurança e utilitários do WhatsApp
from .decorators.security import signature_required
from .utils.whatsapp_utils import (
    process_whatsapp_message,  # Função para processar mensagens do WhatsApp
    is_valid_whatsapp_message,  # Função para validar se a mensagem tem uma estrutura válida do WhatsApp
)

# Cria um Blueprint para o webhook, que agrupa as rotas relacionadas ao webhook
webhook_blueprint = Blueprint("webhook", __name__)


def handle_message():
    """
    Lida com os eventos recebidos pelo webhook da API do WhatsApp.

    Esta função processa as mensagens recebidas e outros eventos, como status de entrega.
    Se o evento for uma mensagem válida, ele será processado. Se o payload recebido
    não for um evento reconhecido da API do WhatsApp, um erro será retornado.

    Toda mensagem enviada acionará 4 requisições HTTP ao seu webhook: mensagem, enviada, entregue e lida.

    Retorna:
        response: Uma tupla contendo uma resposta JSON e um código de status HTTP.
    """
    body = request.get_json()  # Obtém o corpo da requisição em formato JSON
    # logging.info(f"request body: {body}")

    # Verifica se o evento é uma atualização de status do WhatsApp (mensagem enviada, entregue, lida)
    if (
        body.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("statuses")
    ):
        logging.info("Recebida uma atualização de status do WhatsApp.")
        return jsonify({"status": "ok"}), 200  # Retorna OK para confirmar o recebimento

    try:
        # Verifica se a mensagem recebida é válida
        if is_valid_whatsapp_message(body):
            process_whatsapp_message(body)  # Processa a mensagem recebida
            return jsonify({"status": "ok"}), 200  # Responde com sucesso
        else:
            # Se o evento não for reconhecido como uma mensagem da API do WhatsApp, retorna um erro 404
            return (
                jsonify({"status": "error", "message": "Não é um evento da API do WhatsApp"}),
                404,
            )
    except json.JSONDecodeError:
        # Caso ocorra um erro ao decodificar o JSON, registra o erro no log e retorna uma resposta de erro 400
        logging.error("Falha ao decodificar JSON")
        return jsonify({"status": "error", "message": "JSON inválido"}), 400


# Verificação obrigatória do webhook para o WhatsApp
def verify():
    """
    Verifica o webhook com base nos parâmetros enviados pela solicitação GET, conforme necessário pelo WhatsApp.
    """
    # Obtém os parâmetros de verificação do webhook
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    # Verifica se o token e o modo foram enviados
    if mode and token:
        # Verifica se o modo é "subscribe" e o token está correto
        if mode == "subscribe" and token == current_app.config["VERIFY_TOKEN"]:
            # Responde com o código 200 OK e o token de desafio da solicitação
            logging.info("WEBHOOK_VERIFICADO")
            return challenge, 200
        else:
            # Responde com '403 Forbidden' se os tokens de verificação não coincidirem
            logging.info("FALHA_NA_VERIFICAÇÃO")
            return jsonify({"status": "error", "message": "Falha na verificação"}), 403
    else:
        # Responde com '400 Bad Request' se parâmetros necessários estiverem ausentes
        logging.info("PARAMETRO_FALTANDO")
        return jsonify({"status": "error", "message": "Parâmetros ausentes"}), 400


# Rota para lidar com a verificação do webhook (GET)
@webhook_blueprint.route("/webhook", methods=["GET"])
def webhook_get():
    return verify()  # Chama a função de verificação do webhook


# Rota para lidar com eventos recebidos pelo webhook (POST)
@webhook_blueprint.route("/webhook", methods=["POST"])
@signature_required  # Aplica o decorador de segurança para verificar a assinatura da requisição
def webhook_post():
    return handle_message()  # Chama a função para processar a mensagem recebida
