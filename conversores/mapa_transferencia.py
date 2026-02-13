import streamlit as st
import pandas as pd
import csv
import io
import re
from datetime import datetime

def processar_mapa(arquivo_upload):
    conteudo = arquivo_upload.getvalue()
    try:
        texto = conteudo.decode('latin-1')
    except:
        texto = conteudo.decode('cp1252')
        
    reader = csv.reader(io.StringIO(texto))
    linhas = list(reader)
    
    dados = []
    
    for row in linhas:
        # Se a linha for muito curta, pula (para não dar erro de Index)
        if len(row) < 10: 
            continue
            
        atendimento = str(row[1]).strip()
        
        # Identifica se a linha atual contém de fato um paciente:
        # O "Atendimento" na coluna B precisa ser um número
        if not atendimento.isdigit():
            continue
            
        # LAYOUT 1: A data está na Coluna F (Índice 5)
        if len(row) > 19 and re.match(r'\d{2}/\d{2}/\d{4}', str(row[5]).strip()):
            dados.append({
                'Atendimento': atendimento,
                'Paciente': str(row[2]).strip(),           # Col C
                'Dt.Movim.': str(row[5]).strip(),          # Col F
                'Unidade Origem': str(row[7]).strip(),     # Col H
                'Leito Origem': str(row[9]).strip(),       # Col J
                'Unidade Destino': str(row[11]).strip(),   # Col L
                'Leito Destino': str(row[13]).strip(),     # Col N
                'Clínica': str(row[19]).strip()            # Col T
            })
            
        # LAYOUT 2: A data está na Coluna D (Índice 3)
        elif len(row) > 12 and re.match(r'\d{2}/\d{2}/\d{4}', str(row[3]).strip()):
            dados.append({
                'Atendimento': atendimento,
                'Paciente': str(row[2]).strip(),           # Col C
                'Dt.Movim.': str(row[3]).strip(),          # Col D
                'Unidade Origem': str(row[4]).strip(),     # Col E
                'Leito Origem': str(row[6]).strip(),       # Col G
                'Unidade Destino': str(row[7]).strip(),    # Col H
                'Leito Destino': str(row[9]).strip(),      # Col J
                'Clínica': str(row[12]).strip()            # Col M
            })
            
    if not dados: return None
    
    df = pd.DataFrame(dados)
    
    # Ordena as movimentações cronologicamente e por paciente
    df['Data_dt'] = pd.to_datetime(df['Dt.Movim.'], format='%d/%m/%Y', errors='coerce')
    df = df.sort_values(by=['Data_dt', 'Paciente']).drop(columns=['Data_dt'])
    
    return df

def exibir():
    # --- CSS DO BANNER ---
    st.markdown("""
        <style>
        .banner-container {
            position: relative; width: 100%; height: 150px; overflow: hidden; border-radius: 10px; margin-bottom: 25px;
            background-image: url('https://enfermagemflorence.com.br/wp-content/uploads/2019/08/hospital-img2.jpg');
            background-size: cover; background-position: center center;
        }
        .banner-overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 45, 90, 0.5); backdrop-filter: blur(4px);
            display: flex; align-items: center; justify-content: center;
        }
        .banner-text { color: white; font-size: 28px; font-weight: bold; text-align: center; }
        </style>
        <div class="banner-container">
            <div class="banner-overlay"><div class="banner-text">Mapa de Transferência de Leito</div></div>
        </div>
    """, unsafe_allow_html=True)

    # --- INSTRUÇÕES ---
    st.markdown("### 🧭 Instruções de Extração (MV Soul)")
    st.markdown("**Caminho:** `Internação > Relatórios > Movimentação > Movimento de Transf. de Pacientes Internados`")

    st.info("""
    **🛠️ Parâmetros de Filtro:**
    * **Período:** Escolha a data inicial e final desejada.
    * **Tipo de Impressão:** CSV
    
    *💡 **Dica (Opcional):** Se você precisar analisar apenas setores específicos, vá até a aba **"Unidade"** no painel de extração e insira os códigos dos setores desejados antes de gerar o arquivo.*
    """)

    st.markdown("---")

    # --- UPLOADER ---
    st.markdown("#### Importação de Arquivos")
    st.write("Você pode selecionar e enviar múltiplos arquivos de uma vez. O sistema unificará todos os dados processados.")
    
    uploaded_files = st.file_uploader(
        "Carregue os relatórios em formato CSV:", 
        type=["csv"], 
        accept_multiple_files=True, 
        key="uploader_mapa_transf"
    )

    if uploaded_files:
        lista_dfs = []
        with st.spinner("Analisando layouts do arquivo e estruturando as movimentações..."):
            for file in uploaded_files:
                df_proc = processar_mapa(file)
                if df_proc is not None:
                    lista_dfs.append(df_proc)
        
        if lista_dfs:
            # Junta todos os arquivos em um único dataframe
            df_final = pd.concat(lista_dfs).drop_duplicates()
            
            st.success(f"✅ Sucesso! {len(df_final)} movimentações extraídas e limpas.")
            st.dataframe(df_final, use_container_width=True)
            
            # --- ÁREA DE DOWNLOAD ---
            nome_arquivo = datetime.now().strftime("MAPA_TRANSFERENCIA_%d_%m_%Y_%H_%M_%S.csv")
            csv_data = df_final.to_csv(index=False, encoding='utf-8-sig') # Mantém o padrão do Excel PT-BR
            
            st.download_button(
                label="📥 Baixar Planilha Consolidada", 
                data=csv_data, 
                file_name=nome_arquivo, 
                mime="text/csv"
            )
        else:
            st.warning("⚠️ Não foi possível encontrar dados válidos. O arquivo pode estar vazio ou a estrutura do CSV mudou.")