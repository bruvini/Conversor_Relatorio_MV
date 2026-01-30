import streamlit as st
from datetime import datetime

def exibir():
    ano_atual = datetime.now().year
    # Usamos st.container para organizar melhor
    with st.container():
        st.markdown(f"""
            <style>
            .footer {{
                position: fixed;
                left: 0;
                bottom: 0;
                width: 100%;
                background-color: white;
                color: #555;
                text-align: center;
                padding: 10px 0;
                font-size: 12px;
                border-top: 1px solid #e6e6e6;
                z-index: 999999;
            }}
            /* Padding para o conteúdo não ficar por baixo do rodapé */
            .main .block-container {{
                padding-bottom: 100px !important;
            }}
            </style>
            <div class="footer">
                <p>Hospital Municipal São José | Desenvolvido por Enf. Bruno Vinícius<br>
                &copy; {ano_atual} - Todos os direitos reservados</p>
            </div>
        """, unsafe_allow_html=True)