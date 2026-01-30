import streamlit as st

def exibir():
    col1, col2, col3 = st.columns([1, 2, 1], vertical_alignment="center")
    
    with col1:
        st.image("https://mv.com.br/assets/img/content/mv_share.jpg", width=150)
    
    with col2:
        st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>Conversor de Relatórios - MV</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-weight: bold;'>Hospital Municipal São José</p>", unsafe_allow_html=True)
    
    with col3:
        st.image("https://media.licdn.com/dms/image/v2/C4D22AQHJwufLRwLmuA/feedshare-shrink_2048_1536/feedshare-shrink_2048_1536/0/1646686043965?e=2147483647&v=beta&t=gpXNQ2vHLfXkuz1hAo8B_lazEuwHHkeTCQXBg7IhrnY", width=180)
    
    st.divider()