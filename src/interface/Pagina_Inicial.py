import streamlit as st

st.set_page_config(
    page_title="Página Inicial",
    page_icon="👋",
)

st.write("# Bem vindo a Página! 👋")

st.sidebar.success("Selecione uma pagina acima ")

st.markdown(
    """
    Selecione uma página:
    - Dashboard: para visualizar os dados
    - Categorizar: treinar com mais exemplos
"""
)