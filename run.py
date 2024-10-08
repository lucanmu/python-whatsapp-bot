import logging

# Importa a função create_app da aplicação
from app import create_app

# Cria uma instância da aplicação Flask
app = create_app()

# Verifica se o arquivo está sendo executado diretamente (não importado como módulo)
if __name__ == "__main__":
    # Registra uma mensagem no log indicando que a aplicação Flask foi iniciada
    logging.info("Aplicação Flask iniciada")
    
    # Executa a aplicação Flask, tornando-a acessível a partir de qualquer IP (0.0.0.0) na porta 8000
    app.run(host="0.0.0.0", port=8000)
