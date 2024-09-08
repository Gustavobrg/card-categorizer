import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import config

import sqlite3
import pandas as pd

def visualizar_dados_em_dataframe(banco_de_dados, consulta):
    # Conectar ao banco de dados SQLite
    conn = sqlite3.connect(banco_de_dados)
    
    # Executar a consulta e ler os dados em um DataFrame
    df = pd.read_sql_query(consulta, conn)
    
    # Fechar a conexão
    conn.close()
    
    return df

# Exemplo de uso
banco_de_dados = config.DB_PATH
consulta = "SELECT * FROM transacoes_categorizadas"  # Use o nome correto da tabela
conn = sqlite3.connect(banco_de_dados)
df = pd.read_sql_query(consulta, conn)
conn.close()

st.set_page_config(
    page_title="Dashboard Gastos",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

#df = pd.read_csv("transacoes_categorizadas.csv")
df['Data'] = pd.to_datetime(df['Data'], format='%Y-%m-%d')
df['Valor'] = df['Valor'].astype(float)

# Função para calcular o mês de referência
def calcular_mes_referencia(data):
    if data.day <= 10:
        # Se o dia for antes do dia 10, o mês de referência é o mês anterior
        return (data - pd.DateOffset(months=1)).strftime('%m/%Y')
    else:
        # Se o dia for a partir do dia 10, o mês de referência é o mês corrente
        return data.strftime('%m/%Y')

# Aplicando a função para criar a nova coluna 'mes_referencia'
df['mes_referencia'] = df['Data'].apply(calcular_mes_referencia)

# Extraindo o ano da coluna 'data'
df['year'] = df['Data'].dt.year
df['month'] = df['Data'].dt.month

with st.sidebar:
    st.title('💰 Dashboard Gastos')
    
    year_list = list(df.year.unique())[::-1]
    month_list = list(df['mes_referencia'].unique())[::-1]
    month_list.sort()

    selected_year = st.selectbox('Selecione um ano', year_list, index=len(year_list)-1)
    selected_month = st.selectbox('Selecione um mês', month_list, index=len(month_list)-1)

    df_filtered = df[(df['mes_referencia'] == selected_month)]

    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    selected_color_theme = st.selectbox('Select a color theme', color_theme_list)

def plot_daily_expenses_plotly(df_categorized, input_color_theme='viridis'):
    """
    Função para plotar um gráfico de barras de gastos por dia a partir de um DataFrame categorizado usando Plotly.

    Parâmetros:
    df_categorized (pd.DataFrame): DataFrame contendo as colunas 'Data' e 'Valor'.
    input_color_theme (str): Tema de cores para o gráfico (padrão: 'viridis').

    Retorno:
    plotly.graph_objects.Figure: Figura contendo o gráfico de barras interativo.
    """

    # Agrupando por Data e somando os valores
    df_grouped = df_categorized.groupby('Data').sum().reset_index()


    # Ordenando o DataFrame pelas datas
    df_grouped = df_grouped.sort_values(by='Data')

    # Definindo uma lista de paletas de cores suportadas pelo Plotly
    color_themes = {
        'viridis': px.colors.sequential.Viridis,
        'plasma': px.colors.sequential.Plasma,
        'inferno': px.colors.sequential.Inferno,
        'magma': px.colors.sequential.Magma,
        'cividis': px.colors.sequential.Cividis,
        'blues': px.colors.sequential.Blues,
        'greens': px.colors.sequential.Greens,
        'reds': px.colors.sequential.Reds,
        'turbo': px.colors.sequential.Turbo
    }
    
    # Selecionando a paleta de cores apropriada
    color_palette = color_themes.get(input_color_theme, px.colors.sequential.Viridis)
    
    # Identificando dias de final de semana e dias úteis
    df_grouped['Opacity'] = df_grouped['Data'].dt.weekday.isin([5, 6]).map({True: 0.5, False: 1.0})  # 0.5 para finais de semana, 1.0 para dias úteis

    # Criando o gráfico de barras usando Plotly Express
    fig = px.bar(
        df_grouped,
        x=df_grouped['Data'].dt.strftime('%d/%m'),  # Formatando a data para 'dd/MM'
        y='Valor',
        labels={'x': 'Data', 'Valor': 'Total Gasto (R$)'},
        title='Gastos por Dia',
        text='Valor',  # Adiciona os valores nas barras
        color_discrete_sequence=color_palette  # Aplicando o tema de cores
    )

    # Ajustando a opacidade das barras
    fig.update_traces(marker=dict(opacity=df_grouped['Opacity']))

    # Ajustando a apresentação dos textos no gráfico
    fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    fig.update_layout(xaxis_tickangle=-60)

    return fig

def calculate_metrics(df_categorized, selected_month):
    """
    Calcula as métricas de gastos por categoria para o mês selecionado e o mês anterior.

    Parâmetros:
    df_categorized (pd.DataFrame): DataFrame contendo as colunas 'Data', 'Categoria' e 'Valor'.
    selected_month (str): Mês selecionado no formato 'MM/YYYY'.

    Retorno:
    dict: Dicionário contendo as métricas calculadas.
    """
    
    # Converter 'Data' e 'mes_referencia' para datetime se necessário
    df_categorized['mes_referencia'] = pd.to_datetime(df_categorized['mes_referencia'], format='%m/%Y')
    df_categorized['Data'] = pd.to_datetime(df_categorized['Data'])

    df_categorized['Valor'] = df_categorized['Valor'].astype(float)
    
    selected_month = pd.to_datetime(f"01/{selected_month}", format='%d/%m/%Y')
    selected_year = selected_month.year
    selected_month_num = selected_month.month

    df_selected_month = df_categorized[df_categorized['mes_referencia'] == selected_month]

    # Calculando o total gasto por categoria para o mês selecionado
    expenses_current_month = df_selected_month.groupby('Categoria')['Valor'].sum()

    previous_end_date = pd.Timestamp(year=selected_year, month=selected_month_num, day=10)

    # O mês anterior começa no dia 10 do mês anterior
    previous_start_date = previous_end_date - pd.DateOffset(months=1)
        
    df_previous_month = df_categorized[(df_categorized['Data'] > previous_start_date) & (df_categorized['Data'] <= previous_end_date)]

    # Calculando o total gasto por categoria para o mês anterior
    expenses_previous_month = df_previous_month.groupby('Categoria')['Valor'].sum()

    # Garantir que os índices estejam alinhados
    all_categories = expenses_current_month.index.union(expenses_previous_month.index)
    expenses_current_month = expenses_current_month.reindex(all_categories, fill_value=0)
    expenses_previous_month = expenses_previous_month.reindex(all_categories, fill_value=0)

    # Calculando as variações por categoria
    variation_by_category = expenses_current_month - expenses_previous_month
    variation_percent_by_category = (variation_by_category / expenses_previous_month) * 100

    # Calculando o total de gastos e variação total
    total_current_month = expenses_current_month.sum()
    total_previous_month = expenses_previous_month.sum()
    total_variation = total_current_month - total_previous_month
    total_variation_percent = (total_variation / total_previous_month) * 100 if total_previous_month != 0 else 0

    # Retornando os resultados em um dicionário
    return {
        'expenses_current_month': expenses_current_month,
        'expenses_previous_month': expenses_previous_month,
        'variation_by_category': variation_by_category,
        'variation_percent_by_category': variation_percent_by_category,
        'total_current_month': total_current_month,
        'total_previous_month': total_previous_month,
        'total_variation': total_variation,
        'total_variation_percent': total_variation_percent
    }

def plot_monthly_expenses_by_category(df_categorized, input_color_theme='viridis'):
    """
    Função para plotar um gráfico de linhas mostrando a evolução dos gastos por categoria mês a mês.

    Parâmetros:
    df_categorized (pd.DataFrame): DataFrame contendo as colunas 'Data', 'Categoria', e 'Valor'.
    input_color_theme (str): Tema de cores para o gráfico (padrão: 'viridis').

    Retorno:
    plotly.graph_objects.Figure: Figura contendo o gráfico de linhas interativo.
    """
    
    # Extraindo ano e mês para agregar os dados mensalmente
    df_categorized['Ano'] = df_categorized['Data'].dt.year
    df_categorized['Mês'] = df_categorized['Data'].dt.to_period('M').astype(str)

    # Agrupando os dados por ano, mês e categoria
    df_monthly = df_categorized.groupby(['mes_referencia', 'Categoria'])['Valor'].sum().reset_index()
    
    # Definindo uma lista de paletas de cores suportadas pelo Plotly
    color_themes = {
        'viridis': px.colors.sequential.Viridis,
        'plasma': px.colors.sequential.Plasma,
        'inferno': px.colors.sequential.Inferno,
        'magma': px.colors.sequential.Magma,
        'cividis': px.colors.sequential.Cividis,
        'blues': px.colors.sequential.Blues,
        'greens': px.colors.sequential.Greens,
        'reds': px.colors.sequential.Reds,
        'turbo': px.colors.sequential.Turbo
    }
    
    # Selecionando a paleta de cores apropriada
    color_palette = color_themes.get(input_color_theme, px.colors.sequential.Viridis)
    
    # Criando o gráfico de linhas usando Plotly Express com o tema de cores escolhido
    fig = px.line(
        df_monthly,
        x='mes_referencia',
        y='Valor',
        color='Categoria',
        markers=True,
        labels={'mes_referencia': 'Mês/Ano', 'Valor': 'Total Gasto (R$)'},
        title='Evolução dos Gastos por Categoria Mês a Mês',
        color_discrete_sequence=color_palette  # Aplicando o tema de cores
    )

    # Formatando o eixo X para mostrar apenas o mês/ano
    fig.update_xaxes(
        tickformat='%m/%Y',  # Formato mês/ano
        tickmode='array',  # Usar um array de valores
        tickvals=df_monthly['mes_referencia'].unique(),  # Valores a serem exibidos
        ticktext=[pd.to_datetime(date, format='%Y-%m').strftime('%m/%Y') for date in df_monthly['mes_referencia'].unique()]  # Formatação dos textos
    )

    # Atualizando o layout para posicionar a legenda acima do gráfico
    fig.update_layout(
        xaxis_tickangle=-60,
        legend=dict(
            orientation='h',  # Define a orientação horizontal
            yanchor='bottom',  # Ancora a posição vertical da legenda no fundo
            y=1.,  # Posiciona a legenda acima do gráfico
            xanchor='center',  # Ancora a posição horizontal da legenda no centro
            x=0.5,  # Posiciona a legenda no centro horizontalmente
            title_text=''
        )
    )

    return fig

def plot_treemap_expenses_by_category(df_categorized, input_color_theme='viridis'):
    """
    Função para plotar um gráfico de treemap mostrando a proporção dos gastos por categoria para o mês selecionado.

    Parâmetros:
    df_categorized (pd.DataFrame): DataFrame contendo as colunas 'Data', 'Categoria', e 'Valor'.
    input_color_theme (str): Tema de cores para o gráfico (padrão: 'viridis').

    Retorno:
    plotly.graph_objects.Figure: Figura contendo o gráfico de treemap interativo.
    """
    
    # Extraindo ano e mês para agregar os dados mensalmente
    df_categorized['Ano'] = df_categorized['Data'].dt.year
    df_categorized['Mês'] = df_categorized['Data'].dt.to_period('M').astype(str)
    
    # Agrupando os dados por ano, mês e categoria
    df_monthly = df_categorized.groupby(['Categoria'])['Valor'].sum().reset_index()
    
    # Definindo uma lista de paletas de cores suportadas pelo Plotly
    color_themes = {
        'viridis': px.colors.sequential.Viridis,
        'plasma': px.colors.sequential.Plasma,
        'inferno': px.colors.sequential.Inferno,
        'magma': px.colors.sequential.Magma,
        'cividis': px.colors.sequential.Cividis,
        'blues': px.colors.sequential.Blues,
        'greens': px.colors.sequential.Greens,
        'reds': px.colors.sequential.Reds,
        'turbo': px.colors.sequential.Turbo
    }
    
    # Selecionando a paleta de cores apropriada
    color_palette = color_themes.get(input_color_theme, px.colors.sequential.Viridis)
    
    # Criando o gráfico de treemap usando Plotly Express com o tema de cores escolhido
    fig = px.treemap(
        df_monthly,
        path=['Categoria'],  # Define a hierarquia das categorias
        values='Valor',
        labels={'Valor': 'Total Gasto (R$)'},
        title='Proporção dos Gastos por Categoria',
        color='Valor',  # Usar 'Valor' para colorir os segmentos
        color_continuous_scale=color_palette  # Aplicando o tema de cores
    )
    
    # Atualizando o layout para ajustar a visualização
    fig.update_layout(
        margin=dict(t=50, l=0, r=0, b=0),  # Ajusta as margens para melhor visualização
        coloraxis_colorbar=dict(
            title='',  # Remove o título da barra de cores
            tickvals=[],  # Remove os ticks da barra de cores
            ticktext=[]  # Remove os textos da barra de cores
        )
    )

    return fig

def calculate_weekday_weekend_metrics(df):
    """
    Calcula a média dos valores agrupados por data para dias de semana e finais de semana.

    Parâmetros:
    df (pd.DataFrame): DataFrame contendo as colunas 'Data' e 'Valor'.

    Retorno:
    dict: Dicionário contendo as médias para dias de semana e finais de semana.
    """
    # Garantir que a coluna 'Data' seja do tipo datetime
    df['Data'] = pd.to_datetime(df['Data'])
    
    # Adicionar a coluna 'Dia_da_Semana' (0=segunda-feira, 6=domingo)
    df['Dia_da_Semana'] = df['Data'].dt.weekday
    
    # Agrupar por 'Data' e somar os valores
    df_grouped = df.groupby('Data')['Valor'].sum().reset_index()
    
    # Adicionar a coluna 'Dia_da_Semana' ao DataFrame agrupado
    df_grouped['Dia_da_Semana'] = df_grouped['Data'].dt.weekday
    
    # Separar dias de semana (0 a 4) e finais de semana (5 e 6)
    weekdays = df_grouped[df_grouped['Dia_da_Semana'] < 5]
    weekends = df_grouped[df_grouped['Dia_da_Semana'] >= 5]
    
    # Calcular as médias
    average_weekday = weekdays['Valor'].mean()
    average_weekend = weekends['Valor'].mean()
    
    return average_weekday, average_weekend

col = st.columns((1.5, 4.5, 2), gap='medium')


with col[0]:
    st.markdown('#### Gastos')

    metrics = calculate_metrics(df, selected_month)
    st.metric(label="Gastos Totais", value=f"R$ {metrics['total_current_month'].round(2)}", delta=metrics['total_variation'].round(2), delta_color="inverse")

    for category in metrics['expenses_current_month'].index:
        current_month_expense = metrics['expenses_current_month'].get(category, 0)
        previous_month_expense = metrics['expenses_previous_month'].get(category, 0)
        delta = metrics['variation_by_category'].get(category, 0)
        st.metric(label=f"Gastos em {category}", value=f"R$ {current_month_expense.round(2)}", delta=delta.round(2), delta_color="inverse")


with col[1]:
    #st.markdown('#### Total Population')
    
    bar_chart = plot_daily_expenses_plotly(df_filtered, selected_color_theme)
    st.plotly_chart(bar_chart, use_container_width=True)

    bar_chart_category = plot_monthly_expenses_by_category(df, selected_color_theme)
    st.plotly_chart(bar_chart_category, use_container_width=True)

with col[2]:

    mean_weekday, mean_weekend = calculate_weekday_weekend_metrics(df_filtered)
    # Exibir métricas
    st.metric(label="Média de Gastos durante a Semana", value=f"R$ {mean_weekday:.2f}")
    st.metric(label="Média de Gastos nos Finais de Semana", value=f"R$ {mean_weekend:.2f}")
    area = plot_treemap_expenses_by_category(df_filtered, selected_color_theme)
    st.plotly_chart(area, use_container_width=True)