import streamlit as st
from componentes import header, footer
from conversores import ociosidade_cc, estatisticas_internacao, censo_retroativo # Import atualizado

# 1. Configuração de página
st.set_page_config(page_title="Conversor de Relatórios - MV", layout="wide")

# 2. Renderização do Cabeçalho
header.exibir()

# 3. Menu Lateral
st.sidebar.title("Navegação")
opcao = st.sidebar.selectbox(
    "Selecione uma opção:", 
    [
        "Início", 
        "Ociosidade de Centro Cirúrgico",
        "Estatísticas de Internação",
        "Censo Retroativo" # Nova opção incluída
    ],
    key="menu_navegacao_principal"
)

# 4. Lógica de Navegação
if opcao == "Início":
    st.header("Bem-vindo ao Portal de Conversores")
    st.markdown("""
    Esta plataforma foi desenvolvida para otimizar o seu fluxo de trabalho ao trabalhar com relatórios emitidos pelo MV Soul no Hospital Municipal São José. 
    
    ### Como o sistema funciona?
    Os relatórios extraídos diretamente do sistema MV muitas vezes vêm em formatos complexos para análise imediata (como CSVs com estruturas de impressão ou PDF). Este sistema:
    1. **Lê e interpreta** a estrutura bruta dos arquivos.
    2. **Extrai os dados essenciais**, eliminando cabeçalhos repetitivos e lixo visual.
    3. **Realiza cálculos automáticos** conforme necessidade.
    4. **Consolida múltiplos arquivos** em uma única base de dados padronizada.

    ### Como utilizar?
    Utilize o **Menu Lateral** à esquerda para selecionar o tipo de relatório que você deseja converter. 
    Cada ferramenta solicitará o upload dos arquivos correspondentes e gerará uma planilha pronta para uso em Excel, Planilhas Google ou Power BI.
    """)
    
    st.info("ℹ️ **Segurança e Privacidade**: Os arquivos enviados são processados temporariamente na memória do servidor e descartados imediatamente após a conversão. **Nenhum dado é armazenado** de forma permanente ou utilizado para outros fins.")

elif opcao == "Ociosidade de Centro Cirúrgico":
    ociosidade_cc.exibir()

elif opcao == "Estatísticas de Internação":
    estatisticas_internacao.exibir()

elif opcao == "Censo Retroativo":
    censo_retroativo.exibir()

# 5. Rodapé
footer.exibir()