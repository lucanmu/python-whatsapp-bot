from openai import OpenAI
import shelve
from dotenv import load_dotenv
import os
import time

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Obtém a chave da API da OpenAI a partir das variáveis de ambiente
OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")

# Inicializa o cliente da OpenAI usando a chave da API
client = OpenAI(api_key=OPEN_AI_API_KEY)


# --------------------------------------------------------------
# Função para fazer upload de arquivo
# --------------------------------------------------------------
def upload_file(path):
    """
    Faz upload de um arquivo com o propósito de ser utilizado por assistentes da OpenAI.
    """
    file = client.files.create(file=open(path, "rb"), purpose="assistants")
    return file


# Faz o upload de um arquivo PDF específico
file = upload_file("../data/airbnb-faq.pdf")


# --------------------------------------------------------------
# Função para criar um assistente
# --------------------------------------------------------------
def create_assistant(file):
    """
    Cria um assistente baseado no modelo GPT-4. Atualmente, não é possível
    configurar a temperatura do assistente via API.
    """
    assistant = client.beta.assistants.create(
        name="WhatsApp AirBnb Assistant",  # Nome do assistente
        instructions=(
            "Você é um assistente do WhatsApp que ajuda os hóspedes de nosso Airbnb em Paris. "
            "Use sua base de conhecimento para responder às perguntas dos clientes. Se você não souber a resposta, "
            "diga simplesmente que não pode ajudar e aconselhe-os a contatar o anfitrião diretamente. "
            "Seja amigável e engraçado."
        ),
        tools=[{"type": "retrieval"}],  # Ferramenta de busca/retrieval associada ao assistente
        model="gpt-4-1106-preview",  # Modelo GPT-4 usado pelo assistente
        file_ids=[file.id],  # ID do arquivo carregado para o assistente
    )
    return assistant


# Cria o assistente usando o arquivo enviado anteriormente
assistant = create_assistant(file)


# --------------------------------------------------------------
# Funções de gerenciamento de threads (conversas)
# --------------------------------------------------------------
def check_if_thread_exists(wa_id):
    """
    Verifica se um thread (conversa) já existe para o ID do WhatsApp (wa_id).
    """
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)  # Retorna o thread associado ao wa_id se existir


def store_thread(wa_id, thread_id):
    """
    Armazena um thread_id associado ao wa_id no banco de dados shelve.
    """
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id  # Armazena o thread_id no banco


# --------------------------------------------------------------
# Função para gerar resposta
# --------------------------------------------------------------
def generate_response(message_body, wa_id, name):
    """
    Gera uma resposta do assistente baseada na mensagem recebida.

    Verifica se já existe um thread associado ao wa_id, caso contrário cria um novo.
    """
    # Verifica se já existe um thread_id para o wa_id
    thread_id = check_if_thread_exists(wa_id)

    # Se o thread não existir, cria um novo e o armazena
    if thread_id is None:
        print(f"Criando novo thread para {name} com wa_id {wa_id}")
        thread = client.beta.threads.create()  # Cria um novo thread
        store_thread(wa_id, thread.id)  # Armazena o thread criado
        thread_id = thread.id  # Define o thread_id como o novo ID
    else:
        print(f"Recuperando thread existente para {name} com wa_id {wa_id}")
        thread = client.beta.threads.retrieve(thread_id)  # Recupera o thread existente

    # Adiciona a mensagem ao thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",  # Define o papel da mensagem como "usuário"
        content=message_body,  # Conteúdo da mensagem recebida
    )

    # Executa o assistente para gerar uma nova resposta
    new_message = run_assistant(thread)
    print(f"Para {name}:", new_message)
    return new_message


# --------------------------------------------------------------
# Função para rodar o assistente e gerar uma resposta
# --------------------------------------------------------------
def run_assistant(thread):
    """
    Executa o assistente para gerar uma resposta baseada no thread atual.
    """
    # Recupera o assistente
    assistant = client.beta.assistants.retrieve("asst_7Wx2nQwoPWSf710jrdWTDlfE")

    # Inicia a execução do assistente
    run = client.beta.threads.runs.create(
        thread_id=thread.id,  # ID do thread
        assistant_id=assistant.id,  # ID do assistente
    )

    # Aguarda a conclusão da execução
    while run.status != "completed":
        time.sleep(0.5)  # Atraso para evitar sobrecarga na API
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    # Recupera as mensagens geradas pelo assistente
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    new_message = messages.data[0].content[0].text.value  # Extrai o conteúdo da primeira mensagem gerada
    print(f"Mensagem gerada: {new_message}")
    return new_message


# --------------------------------------------------------------
# Teste do assistente
# --------------------------------------------------------------

# Envia uma mensagem para o assistente e gera uma resposta
new_message = generate_response("Qual é o horário de check-in?", "123", "John")
new_message = generate_response("Qual o código da caixa de chave?", "456", "Sarah")
new_message = generate_response("Qual foi minha pergunta anterior?", "123", "John")
new_message = generate_response("Qual foi minha pergunta anterior?", "456", "Sarah")
