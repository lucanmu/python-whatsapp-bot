from functools import wraps
from flask import current_app, jsonify, request
import logging
import hashlib
import hmac


def validate_signature(payload, signature):
    """
    Função para validar a assinatura do payload recebido com a assinatura esperada.
    """
    # Usa o segredo do aplicativo para gerar o hash do payload
    expected_signature = hmac.new(
        bytes(current_app.config["APP_SECRET"], "latin-1"),  # Secret key do app
        msg=payload.encode("utf-8"),  # Payload recebido, codificado em UTF-8
        digestmod=hashlib.sha256,  # Algoritmo de hash SHA-256
    ).hexdigest()  # Gera o hash e converte em uma string hexadecimal

    # Compara a assinatura gerada com a assinatura recebida
    return hmac.compare_digest(expected_signature, signature)


def signature_required(f):
    """
    Decorador para garantir que as requisições recebidas no webhook sejam válidas e assinadas com a assinatura correta.
    """

    @wraps(f)  # Preserva informações originais da função decorada (como nome e docstring)
    def decorated_function(*args, **kwargs):
        # Extrai a assinatura do cabeçalho HTTP 'X-Hub-Signature-256', removendo o prefixo 'sha256='
        signature = request.headers.get("X-Hub-Signature-256", "")[7:]

        # Valida a assinatura usando a função validate_signature
        if not validate_signature(request.data.decode("utf-8"), signature):
            # Loga a falha de verificação de assinatura
            logging.info("Falha na verificação da assinatura!")
            # Retorna um erro 403 (proibido) com uma mensagem de assinatura inválida
            return jsonify({"status": "error", "message": "Invalid signature"}), 403

        # Se a assinatura for válida, executa a função original
        return f(*args, **kwargs)

    return decorated_function
