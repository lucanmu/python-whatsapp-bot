import sys
import os
from dotenv import load_dotenv
import logging


def load_configurations(app):
    """
    Carrega as configurações do aplicativo a partir de variáveis de ambiente.
    As variáveis são carregadas do arquivo `.env` para garantir que dados sensíveis, como tokens e chaves, estejam disponíveis no ambiente de execução.
    """
    load_dotenv()  # Carrega as variáveis de ambiente a partir do arquivo .env
    
    # Define várias configurações da aplicação, lendo os valores das variáveis de ambiente
    app.config["ACCESS_TOKEN"] = os.getenv("ACCESS_TOKEN")  # Token de acesso para a API
    app.config["YOUR_PHONE_NUMBER"] = os.getenv("YOUR_PHONE_NUMBER")  # Seu número de telefone
    app.config["APP_ID"] = os.getenv("APP_ID")  # ID da aplicação
    app.config["APP_SECRET"] = os.getenv("APP_SECRET")  # Segredo da aplicação
    app.config["RECIPIENT_WAID"] = os.getenv("RECIPIENT_WAID")  # ID do destinatário no WhatsApp
    app.config["VERSION"] = os.getenv("VERSION")  # Versão da API que está sendo usada
    app.config["PHONE_NUMBER_ID"] = os.getenv("PHONE_NUMBER_ID")  # ID do número de telefone usado na API
    app.config["VERIFY_TOKEN"] = os.getenv("VERIFY_TOKEN")  # Token de verificação para autenticação


def configure_logging():
    """
    Configura o sistema de logging para a aplicação.
    Os logs serão enviados para o `stdout` (saída padrão) com um formato específico que inclui informações como a hora, nome do logger, nível de log e a mensagem.
    """
    logging.basicConfig(
        level=logging.INFO,  # Define o nível de log como 'INFO', ou seja, apenas mensagens de 'INFO' e superiores serão registradas
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Formato dos logs, incluindo timestamp, nome do logger, nível e mensagem
        stream=sys.stdout,  # Direciona a saída dos logs para o `stdout` (saída padrão)
    )
