import streamlit as st
import pandas as pd
import os
import sys

# Adiciona o caminho para o diretório pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import config

# Adiciona o diretório 'src' ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from data_processing.download_fatura import baixar_anexos_email
from data_processing.PDF_parse import extrair_fatura_pdf

EXEMPLES_PATH = config.EXEMPLES_PATH
ALLOWED_CATEGORIES = config.ALLOWED_CATEGORIES

# Função para carregar os dados categorizados
def carregar_dados_categorizados():
    if os.path.exists(EXEMPLES_PATH):
        return pd.read_csv(EXEMPLES_PATH)
    else:
        return pd.DataFrame(columns=['Data', 'Transação', 'País', 'Moeda', 'Valor', 'Categoria'])

# Função para carregar arquivos de fatura
def carregar_arquivos_fatura():
    return [f for f in os.listdir('data') if f.startswith(('fatura', 'outros')) and f.endswith('.csv')]

# Função para exibir a transação atual
def exibir_transacao(df, index):
    row = df.iloc[index]
    return f"Data: {row['Data']}\nTransação: {row['Transação']}\nPaís: {row['País']}\nMoeda: {row['Moeda']}\nValor: {row['Valor']}"

# Função para salvar a categoria
def salvar_categoria(df, categoria, index, opcao):
    if opcao == 1:
        st.session_state.categorized_data_opcao1.append({
            "Data": df.iloc[index]["Data"],
            "Transação": df.iloc[index]["Transação"],
            "País": df.iloc[index]["País"],
            "Moeda": df.iloc[index]["Moeda"],
            "Valor": df.iloc[index]["Valor"],
            "Categoria": categoria
        })
        st.session_state.current_index_opcao1 += 1
    elif opcao == 2:
        st.session_state.categorized_data_opcao2.append({
            "Data": df.iloc[index]["Data"],
            "Transação": df.iloc[index]["Transação"],
            "País": df.iloc[index]["País"],
            "Moeda": df.iloc[index]["Moeda"],
            "Valor": df.iloc[index]["Valor"],
            "Categoria": categoria
        })
        st.session_state.current_index_opcao2 += 1

# Inicializa o estado da sessão
if 'categorized_data_opcao1' not in st.session_state:
    st.session_state.categorized_data_opcao1 = []
if 'current_index_opcao1' not in st.session_state:
    st.session_state.current_index_opcao1 = 0
if 'categorized_data_opcao2' not in st.session_state:
    st.session_state.categorized_data_opcao2 = []
if 'current_index_opcao2' not in st.session_state:
    st.session_state.current_index_opcao2 = 0
if 'arquivo_selecionado_opcao2' not in st.session_state:
    st.session_state.arquivo_selecionado_opcao2 = None
if 'df_novos_exemplos_opcao2' not in st.session_state:
    st.session_state.df_novos_exemplos_opcao2 = None

# Configura a página
st.set_page_config(
    page_title="Categorização de Transações",
    page_icon="📝",
)

# Título da página
st.title("Categorização de Transações")

# Carrega os dados existentes, se houver
df_categorizados = carregar_dados_categorizados()

# Define as opções do usuário, ocultando a primeira se já houver dados
if df_categorizados.empty:
    opcoes = ["Categorizar novos dados", "Adicionar exemplos a partir de CSV", "Visualizar dados categorizados"]
else:
    opcoes = ["Adicionar exemplos a partir de CSV", "Visualizar dados categorizados"]
opcao = st.selectbox("Escolha uma ação", opcoes)

@st.cache_data  # Adicione esta linha para usar o cache
def carregar_dados():
    arquivos = baixar_anexos_email()
    dfs = []
    for i, arquivo in enumerate(arquivos):
        csv_filename = f"data/fatura_{i}.csv" 
        df = extrair_fatura_pdf(arquivo, csv_filename)
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)
    return df

# Processa a opção selecionada
if opcao == "Categorizar novos dados":
    df = carregar_dados()  # Carrega os dados da função em cache
    print(f"Número de transações: {df.shape[0]}")

    if st.session_state.current_index_opcao1 < len(df):
        st.write(exibir_transacao(df, st.session_state.current_index_opcao1))

        cols = st.columns(len(ALLOWED_CATEGORIES))
        for i, categoria in enumerate(ALLOWED_CATEGORIES):
            with cols[i]:
                if st.button(categoria, key=f"opcao1_{i}_{st.session_state.current_index_opcao1}"):
                    salvar_categoria(df, categoria, st.session_state.current_index_opcao1, opcao=1)

        if st.session_state.categorized_data_opcao1:
            df_categorized = pd.DataFrame(st.session_state.categorized_data_opcao1)
            st.subheader("Transações Categorizadas")
            st.dataframe(df_categorized)
    else:
        st.write("Todas as transações foram categorizadas.")
        df_categorized = pd.DataFrame(st.session_state.categorized_data_opcao1)
        df_categorized.drop_duplicates(subset=["Transação"], inplace=True)
        df_categorized.to_csv(EXEMPLES_PATH, index=False)
        st.write("As transações categorizadas foram salvas no arquivo 'transacoes_categorizadas.csv'.")

elif opcao == "Adicionar exemplos a partir de CSV":
    arquivos_fatura = carregar_arquivos_fatura()

    if st.session_state.arquivo_selecionado_opcao2 is None:
        st.session_state.arquivo_selecionado_opcao2 = st.selectbox("Selecione um arquivo de fatura", arquivos_fatura)

    if st.button("Carregar") and st.session_state.arquivo_selecionado_opcao2:
        st.session_state.df_novos_exemplos_opcao2 = pd.read_csv(os.path.join('data', st.session_state.arquivo_selecionado_opcao2))
        st.write(f"Arquivo '{st.session_state.arquivo_selecionado_opcao2}' carregado com sucesso.")

    if st.session_state.df_novos_exemplos_opcao2 is not None:
        df_novos_exemplos = st.session_state.df_novos_exemplos_opcao2

        if st.session_state.current_index_opcao2 < len(df_novos_exemplos):
            st.write(exibir_transacao(df_novos_exemplos, st.session_state.current_index_opcao2))

            cols = st.columns(len(ALLOWED_CATEGORIES))
            for i, categoria in enumerate(ALLOWED_CATEGORIES):
                with cols[i]:
                    if st.button(categoria, key=f"opcao2_{i}_{st.session_state.current_index_opcao2}"):
                        salvar_categoria(df_novos_exemplos, categoria, st.session_state.current_index_opcao2, opcao=2)

            if st.session_state.categorized_data_opcao2:
                df_categorized_novos = pd.DataFrame(st.session_state.categorized_data_opcao2)
                st.subheader("Transações Categorizadas da Nova Fatura")
                st.dataframe(df_categorized_novos)
        else:
            st.write("Todas as novas transações foram categorizadas.")
            df_categorizados = pd.concat([df_categorizados, pd.DataFrame(st.session_state.categorized_data_opcao2)], ignore_index=True)
            df_categorizados.drop_duplicates(subset=["Transação"], inplace=True)
            df_categorizados.to_csv(EXEMPLES_PATH, index=False)
            st.write("Novos exemplos categorizados foram adicionados e salvos com sucesso.")

elif opcao == "Visualizar dados categorizados":
    if not df_categorizados.empty:
        st.subheader("Transações Categorizadas")
        st.dataframe(df_categorizados)
    else:
        st.write("Nenhum dado categorizado encontrado.")