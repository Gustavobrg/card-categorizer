from dotenv import load_dotenv
import os

# Carrega as variáveis do .env
load_dotenv()


# Acessa variáveis de ambiente
EMAIL_USER = os.getenv('EMAIL')
EMAIL_PASS = os.getenv('EMAIL_PASS')
REMITENTE = os.getenv('REMITENTE')
SUBJECT_KEYWORD = os.getenv('SUBJECT_KEYWORD')
PDF_PASS = os.getenv('PDF_PASS')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '../data/minhas_transacoes.db')
EXEMPLES_PATH = os.path.join(BASE_DIR, '../data/transacoes_categorizadas.csv')

MODEL = "gpt-3.5-turbo"

ALLOWED_CATEGORIES = [
    "Moradia", "Transporte", "Alimentação", "Saúde", 
    "Lazer e Entretenimento", "Despesas Pessoais", "Outros"
]

# Template de exemplos para o FewShotPrompt
EXAMPLE_TEMPLATE = """
Transação: {input}
Categoria: {output}
"""

PROMPT_PREFIX = "Você é um sistema que categoriza transações em categorias específicas. Exemplos:"
PROMPT_SUFFIX = "Agora classifique com base nos exemplos passados a seguinte transação:\nTransação: {input}\nCategoria:"
