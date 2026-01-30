import streamlit as st
from datetime import datetime

def exibir():
    ano_atual = datetime.now().year
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
            z-index: 999;
        }}
        .main .block-container {{
            padding-bottom: 80px;
        }}
        </style>
        <div class="footer">
            <p>Hospital Municipal São José | Desenvolvido por Enf. Bruno Vinícius<br>
            &copy; {ano_atual}</p>
        </div>
    """, unsafe_allow_html=True)