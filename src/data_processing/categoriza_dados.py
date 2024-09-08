import os
import sqlite3
import pandas as pd
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain.prompts.example_selector.ngram_overlap import NGramOverlapExampleSelector
from langchain_core.example_selectors.base import BaseExampleSelector
from openai import OpenAI
from tqdm import tqdm
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import config

from data_processing.download_fatura import baixar_anexos_email
from data_processing.PDF_parse import extrair_fatura_pdf

os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY


BASE_DIR = config.BASE_DIR
DB_PATH = config.DB_PATH
EXEMPLES_PATH = config.EXEMPLES_PATH

# Definição de categorias permitidas
ALLOWED_CATEGORIES = config.ALLOWED_CATEGORIES

# Template de exemplos para o FewShotPrompt
EXAMPLE_TEMPLATE = config.EXAMPLE_TEMPLATE

# Classe CustomExampleSelector
class CustomExampleSelector(BaseExampleSelector):
    def __init__(self, examples, max_examples=3):
        self.max_examples = max_examples
        self.ngram_selector = NGramOverlapExampleSelector(
            examples=examples,
            example_prompt=PromptTemplate(
                template=EXAMPLE_TEMPLATE,
                input_variables=["input", "output"],
            ),
            threshold=0.1,
        )

    def add_example(self, example):
        self.examples.append(example)

    def select_examples(self, input_str):
        selected_examples = self.ngram_selector.select_examples(input_str)
        return selected_examples[:self.max_examples]

# Função para categorizar transações
def categorize_transaction(input_text, prompt_template, client):
    prompt = prompt_template.format(input=input_text)
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=config.MODEL,
    )
    response = chat_completion.choices[0].message.content.strip()
    return response if response in ALLOWED_CATEGORIES else "Outros"

# Função principal
def main():

    # Baixar anexos e extrair dados
    arquivos = baixar_anexos_email()
    dfs = []
    for i, arquivo in enumerate(arquivos):
        csv_filename = f"data/fatura_{i}.csv"  # Nome único para cada CSV
        df = extrair_fatura_pdf(arquivo, csv_filename)
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)
    print(f"Número de transações: {df.shape[0]}")

    # Carregar exemplos categorizados
    df_exemplos = pd.read_csv(EXEMPLES_PATH)
    examples = [{"input": row["Transação"], "output": row["Categoria"]} for _, row in df_exemplos.iterrows()]

    # Criar o cliente OpenAI
    client = OpenAI()

    # Configurar prompt com o seletor customizado
    custom_selector = CustomExampleSelector(examples=examples, max_examples=3)
    few_shot_prompt = FewShotPromptTemplate(
        example_selector=custom_selector,
        example_prompt=PromptTemplate(
            template=EXAMPLE_TEMPLATE,
            input_variables=["input", "output"],
        ),
        prefix=config.PROMPT_PREFIX,
        suffix=config.PROMPT_SUFFIX,
        input_variables=["input"],
        example_separator="\n",
    )

    # Aplicar a categorização com barra de progresso
    tqdm.pandas(desc="Categorizando transações")
    df["Categoria"] = df["Transação"].progress_apply(lambda x: categorize_transaction(x, few_shot_prompt, client))

    outros_df = df[df["Categoria"] == "Outros"]

    # Salvar no banco de dados SQLite
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("transacoes_categorizadas", conn, if_exists="append", index=False)


    # Salvar itens categorizados como "Outros" em um arquivo CSV (sem duplicatas)
    csv_path = os.path.join("data", "outros_categorizar.csv")
    
    if not outros_df.empty:
        if os.path.isfile(csv_path):
            # Se o arquivo já existir, concatenar os dados
            outros_df.to_csv(csv_path, mode='a', header=False, index=False)
        else:
            # Caso contrário, criar um novo arquivo
            outros_df.to_csv(csv_path, index=False)
    
    # Remover duplicatas após a concatenação
    if os.path.isfile(csv_path):
        df_outros = pd.read_csv(csv_path)
        if os.path.isfile(EXEMPLES_PATH):
            df_categorizadas = pd.read_csv(EXEMPLES_PATH)
            # Manter apenas as transações que não estão em df_categorizadas
            df_outros = df_outros[~df_outros["Transação"].isin(df_categorizadas["Transação"])]
        df_outros.drop_duplicates(subset=["Transação"], inplace=True)
        df_outros.to_csv(csv_path, index=False)

if __name__ == "__main__":
    main()