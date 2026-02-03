import streamlit as st
import pandas as pd
import csv
import io
import re
from datetime import datetime

def limpar_valor(valor):
    try:
        # Remove pontos de milhar e trata decimais
        v = str(valor).strip().replace('.', '').replace(',', '.')
        if not v or v.lower() == 'nan': return 0
        return int(float(v))
    except:
        return 0

def processar_estatisticas(arquivo_upload):
    conteudo = arquivo_upload.getvalue()
    try:
        texto = conteudo.decode('latin-1')
    except:
        texto = conteudo.decode('cp1252')
        
    reader = csv.reader(io.StringIO(texto))
    linhas = list(reader)
    
    dados_finais = []
    data_atual = None
    
    # Palavras que indicam que a linha não é de dados de setores
    palavras_bloqueadas = [
        'unidade de internação', 'unidade', 'total', 'total geral', 
        'entradas', 'saídas', 'legenda', 'emitido em', 'página', 
        'hospitalar', 'sintético', 'indicadores'
    ]

    # 1. Verifica se o arquivo tem o padrão analítico (contém a palavra "Data:")
    tem_datas_internas = any("Data:" in " ".join(r) for r in linhas)

    for row in linhas:
        if not row: continue
        
        linha_texto = " ".join(row)
        
        # 1. Captura a Data (Padrão: Data: DD/MM/YYYY)
        match_data = re.search(r'Data:\s*(\d{2}/\d{2}/\d{4})', linha_texto)
        if match_data:
            data_atual = match_data.group(1)
            continue
            
        # 2. Identifica o Setor
        setor_raw = ""
        
        if tem_datas_internas:
            if len(row) > 0 and row[0].strip() and not any(p in row[0].lower() for p in palavras_bloqueadas):
                setor_raw = row[0].strip()
        else:
            if len(row) > 2 and row[2].strip() and not any(p in row[2].lower() for p in palavras_bloqueadas):
                setor_raw = row[2].strip()

        if not setor_raw or re.match(r'\d{2}/\d{2}/\d{4}', setor_raw) or len(setor_raw) < 3:
            continue
            
        setor = setor_raw.replace('Unidade de Internação :', '').replace('Unidade de Internação', '').strip()
        
        # 3. Mapeamento Dinâmico de Colunas
        if data_atual or not tem_datas_internas:
            if len(row) > 80:
                dados_finais.append({
                    'Data': data_atual if data_atual else "Sintético",
                    'Setor': setor,
                    '00:00': limpar_valor(row[17]),
                    'Intern.': limpar_valor(row[24]),
                    'Transf DE': limpar_valor(row[31]),
                    'Altas': limpar_valor(row[37]),
                    'Transf PARA': limpar_valor(row[42]),
                    'Obitos': limpar_valor(row[48]),
                    'Óbitos +24Hs': limpar_valor(row[55]),
                    'Obitos -24Hs': limpar_valor(row[58]),
                    'Pac/Dia': limpar_valor(row[95])
                })
            elif tem_datas_internas:
                dados_finais.append({
                    'Data': data_atual,
                    'Setor': setor,
                    '00:00': limpar_valor(row[4]),
                    'Intern.': limpar_valor(row[6]),
                    'Transf DE': limpar_valor(row[8]),
                    'Altas': limpar_valor(row[11]),
                    'Transf PARA': limpar_valor(row[13]),
                    'Obitos': limpar_valor(row[15]),
                    'Óbitos +24Hs': limpar_valor(row[18]),
                    'Obitos -24Hs': limpar_valor(row[20]),
                    'Pac/Dia': limpar_valor(row[37])
                })
            else:
                dados_finais.append({
                    'Data': "Consolidado",
                    'Setor': setor,
                    '00:00': limpar_valor(row[5]), 'Intern.': limpar_valor(row[8]),
                    'Transf DE': limpar_valor(row[11]), 'Altas': limpar_valor(row[13]),
                    'Transf PARA': limpar_valor(row[16]), 'Obitos': limpar_valor(row[20]),
                    'Óbitos +24Hs': limpar_valor(row[24]), 'Obitos -24Hs': limpar_valor(row[27]),
                    'Pac/Dia': limpar_valor(row[44])
                })

    if not dados_finais: return None
    
    df = pd.DataFrame(dados_finais)
    if data_atual:
        df['Data_dt'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df = df.sort_values(by=['Data_dt', 'Setor']).drop(columns=['Data_dt'])
    
    return df

def exibir():
    st.markdown("""
        <style>
        .banner-container {
            position: relative; width: 100%; height: 150px; overflow: hidden; border-radius: 10px; margin-bottom: 25px;
            background-image: url('https://informasus.ufscar.br/wp-content/uploads/2020/07/image-from-rawpixel-id-259632-jpeg-scaled.jpg');
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
            <div class="banner-overlay"><div class="banner-text">Estatísticas de Internação</div></div>
        </div>
    """, unsafe_allow_html=True)

    with st.expander("Instruções de Extração (MV Soul)", expanded=False):
        st.markdown("""
        1. **Internação** > **Relatórios** > **Estatísticos** > **Hospitalar** > **Sintético**.
        2. Tipo de impressão: **CSV**.
        """)

    uploaded_files = st.file_uploader("Uploader", type=["csv"], accept_multiple_files=True, label_visibility="collapsed", key="uploader_internacao")

    if uploaded_files:
        lista_dfs = []
        with st.spinner("Tratando dados..."):
            for file in uploaded_files:
                df_proc = processar_estatisticas(file)
                if df_proc is not None:
                    lista_dfs.append(df_proc)
        
        if lista_dfs:
            df_final = pd.concat(lista_dfs).drop_duplicates()
            st.success(f"Sucesso! {len(df_final)} registros processados.")
            st.dataframe(df_final, use_container_width=True)
            
            # --- AJUSTE DO NOME DO ARQUIVO ---
            nome_arquivo = datetime.now().strftime("ESTATISTICA_INTERNACAO_%d_%m_%Y_%H_%M_%S.csv")
            csv = df_final.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                label="📥 Baixar Planilha Consolidada",
                data=csv,
                file_name=nome_arquivo,
                mime="text/csv"
            )