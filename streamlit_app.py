import streamlit as st
from componentes import header, footer
from conversores import ociosidade_cc

# 1. Configuração inicial (DEVE ser a primeira coisa)
st.set_page_config(page_title="Conversor de Relatórios - MV", layout="wide")

# 2. Cabeçalho
header.exibir()

# 3. Menu Lateral (Adicionamos uma 'key' para evitar o KeyError)
st.sidebar.title("Navegação")
opcao = st.sidebar.selectbox(
    "Selecione uma opção:", 
    ["Início", "Ociosidade de Centro Cirúrgico"],
    key="menu_principal" 
)

# 4. Lógica de Páginas
if opcao == "Início":
    st.header("Bem-vindo ao Portal de Conversores")
    st.markdown("""
    Esta plataforma foi desenvolvida para otimizar o seu fluxo de trabalho ao trabalhar com relatórios emitidos pelo MV Soul no Hospital Municipal São José.
    ...
    """)
    st.info("ℹ️ Segurança e Privacidade: ...")

elif opcao == "Ociosidade de Centro Cirúrgico":
    ociosidade_cc.exibir()

# 5. Rodapé (Chamamos por último para não interferir nos widgets)
footer.exibir()