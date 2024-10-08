from openai import OpenAI
import shelve
from dotenv import load_dotenv
import os
import time
import logging

# Carrega as variáveis de ambiente a partir do arquivo .env
load_dotenv()

# Obtém a chave de API e o ID do assistente do arquivo .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

# Inicializa o cliente da OpenAI usando a chave de API
client = OpenAI(api_key=OPENAI_API_KEY)


def upload_file(path):
    # Função para fazer upload de um arquivo para o assistente
    # Define o propósito do arquivo como "assistants", ou seja, será usado pelo assistente
    file = client.files.create(
        file=open("../../data/airbnb-faq.pdf", "rb"), purpose="assistants"
    )


def create_assistant(file):
    """
    Cria um assistente beta da OpenAI.
    Obs: Atualmente, não é possível definir a temperatura (grau de criatividade) do assistente via API.
    """
    assistant = client.beta.assistants.create(
        name="WhatsApp AirBnb Assistant",  # Nome do assistente
        instructions="Você é um assistente do WhatsApp que ajuda os hóspedes do nosso Airbnb em Paris. Use sua base de conhecimento para responder da melhor forma às perguntas dos clientes. Se não souber a resposta, diga que não pode ajudar e sugira que entrem em contato diretamente com o anfitrião. Seja amigável e engraçado.",  # Instruções para o assistente
        tools=[{"type": "retrieval"}],  # Ferramentas disponíveis para o assistente
        model="gpt-4-1106-preview",  # Modelo do GPT usado pelo assistente
        file_ids=[file.id],  # Arquivo carregado anteriormente
    )
    return assistant  # Retorna o assistente criado


# Função para verificar se um "thread" já existe para o ID do WhatsApp (wa_id)
def check_if_thread_exists(wa_id):
    # Usa um gerenciador de contexto para abrir o arquivo de banco de dados (shelve)
    # Isso garante que o arquivo será fechado corretamente após o uso
    with shelve.open("threads_db") as threads_shelf:
        # Verifica se o thread associado ao wa_id existe no banco de dados e o retorna, se existir
        return threads_shelf.get(wa_id, None)


# Função para armazenar um novo "thread" no banco de dados
def store_thread(wa_id, thread_id):
    # Abre o arquivo de banco de dados com a opção de gravação habilitada
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        # Armazena o thread_id associado ao wa_id
        threads_shelf[wa_id] = thread_id


def run_assistant(thread, name):
    # Função para rodar o assistente e gerar uma resposta

    # Recupera o assistente com base no ID definido
    assistant = client.beta.assistants.retrieve(OPENAI_ASSISTANT_ID)

    # Inicia a execução do assistente, criando um "run"
    run = client.beta.threads.runs.create(
        thread_id=thread.id,  # ID do thread
        assistant_id=assistant.id,  # ID do assistente
        # Instruções opcionais: Você pode personalizar a conversa com o nome do usuário
        # instructions=f"You are having a conversation with {name}",
    )

    # Aguarda a conclusão da execução
    # Consulta a documentação da OpenAI para a mecânica de polling (espera ativa por uma resposta)
    while run.status != "completed":
        # Aguarda meio segundo para evitar sobrecarga na API
        time.sleep(0.5)
        # Recupera o status atualizado da execução do assistente
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    # Recupera as mensagens geradas pela execução do thread
    messages = client.beta.threads.messages.list(thread_id=thread.id)

    # Obtém a primeira mensagem gerada e registra no log
    new_message = messages.data[0].content[0].text.value
    logging.info(f"Generated message: {new_message}")

    # Retorna a nova mensagem gerada pelo assistente
    return new_message


def generate_response(message_body, wa_id, name):
    # Função para gerar uma resposta para uma mensagem recebida

    # Verifica se já existe um thread associado ao wa_id no banco de dados
    thread_id = check_if_thread_exists(wa_id)

    # Se o thread não existir, cria um novo e o armazena
    if thread_id is None:
        logging.info(f"Criando um novo thread para {name} com wa_id {wa_id}")
        thread = client.beta.threads.create()  # Cria um novo thread
        store_thread(wa_id, thread.id)  # Armazena o novo thread no banco de dados
        thread_id = thread.id  # Define o thread_id como o novo ID criado

    # Se o thread já existir, apenas o recupera
    else:
        logging.info(f"Recuperando thread existente para {name} com wa_id {wa_id}")
        thread = client.beta.threads.retrieve(thread_id)

    # Adiciona a mensagem recebida ao thread existente
    message = client.beta.threads.messages.create(
        thread_id=thread_id,  # ID do thread
        role="user",  # Define o papel como "usuário" (quem envia a mensagem)
        content=message_body,  # Conteúdo da mensagem enviada pelo usuário
    )

    # Executa o assistente e obtém a resposta gerada
    new_message = run_assistant(thread, name)

    # Retorna a nova mensagem gerada pelo assistente
    return new_message
