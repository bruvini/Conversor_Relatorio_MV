import streamlit as st
import pandas as pd
import csv
import io
from datetime import datetime

def limpar_valor(valor):
    try:
        # Remove pontos de milhar e converte para int
        v = str(valor).strip().replace('.', '').replace(',', '.')
        return int(float(v)) if v and v != 'nan' else 0
    except:
        return 0

def processar_censo(arquivos_com_data):
    dados_totais = []

    for item in arquivos_com_data:
        arquivo = item['arquivo']
        # AJUSTE: Alterado de %d/%m/%Y para %d-%m-%Y para usar hífens
        data_referencia = item['data'].strftime('%d-%m-%Y')
        
        # Leitura do conteúdo do arquivo
        conteudo = arquivo.getvalue()
        try:
            texto = conteudo.decode('latin-1')
        except:
            texto = conteudo.decode('cp1252')
            
        reader = csv.reader(io.StringIO(texto))
        linhas = list(reader)
        
        setor_atual = "N/D"
        
        for idx, row in enumerate(linhas):
            if not row: continue
            
            # 1. Identifica o Setor na Coluna A (Índice 0)
            col0 = str(row[0]).strip()
            if 'Unidade de Interna' in col0:
                # Remove o prefixo e limpa espaços
                nome_setor = col0.split(':')[-1].strip()
                if nome_setor.upper() != "ENFERMARIA":
                    setor_atual = nome_setor
                continue
            
            # 2. Identifica a linha de Totais na Coluna C (Índice 2)
            if len(row) > 2 and 'Total de' in str(row[2]):
                if idx + 1 < len(linhas):
                    v = linhas[idx + 1] # Linha dos valores
                    
                    dados_totais.append({
                        'Data': data_referencia,
                        'Setor': setor_atual,
                        'Total': limpar_valor(v[3]) if len(v) > 3 else 0,
                        'Extras': limpar_valor(v[6]) if len(v) > 6 else 0,
                        'Ocup': limpar_valor(v[8]) if len(v) > 8 else 0,
                        'Vagos': limpar_valor(v[14]) if len(v) > 14 else 0,
                        'Reserv.': limpar_valor(v[17]) if len(v) > 17 else 0,
                        'Acomp.': limpar_valor(v[19]) if len(v) > 19 else 0,
                        'Infectados': limpar_valor(v[21]) if len(v) > 21 else 0,
                        'Reforma': limpar_valor(v[23]) if len(v) > 23 else 0,
                        'Interd. Infec.': limpar_valor(v[28]) if len(v) > 28 else 0,
                        'Interd. Temp.': limpar_valor(v[31]) if len(v) > 31 else 0,
                        'Interditado': limpar_valor(v[35]) if len(v) > 35 else 0,
                        'Manutenção': limpar_valor(v[37]) if len(v) > 37 else 0,
                        'Limpeza': limpar_valor(v[41]) if len(v) > 41 else 0
                    })

    if not dados_totais:
        return None
        
    df = pd.DataFrame(dados_totais)
    df['Data_dt'] = pd.to_datetime(df['Data'], format='%d-%m-%Y')
    df = df.sort_values(by=['Data_dt', 'Setor']).drop(columns=['Data_dt'])
    
    return df

def exibir():
    st.markdown("""
        <style>
        .banner-container {
            position: relative; width: 100%; height: 150px; overflow: hidden; border-radius: 10px; margin-bottom: 25px;
            background-image: url('https://www.lafis.com.br/Content/imagens/analise-setorial/Planos-de-Sa%C3%BAde-e-Hospitais-Privados.jpg');
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
            <div class="banner-overlay"><div class="banner-text">Conversor de Censo Retroativo</div></div>
        </div>
    """, unsafe_allow_html=True)

    with st.expander("Instruções para Emissão no MV Soul", expanded=False):
        st.markdown("""
        1. **Internação** > **Relatórios** > **Operacionais** > **Censo Retroativo**.
        2. Mude o tipo de impressão para **CSV**
        3. Unidade de Internação: **Todos**
        4. Data retroativa: Selecione a **data para o relatório** e o horário sempre como **23:59**.
        """)
        
    uploaded_files = st.file_uploader("Upload", type=["csv"], accept_multiple_files=True, key="uploader_censo_retro", label_visibility="collapsed")

    if uploaded_files:
        st.write("### 📅 Vincular Datas de Referência")
        arquivos_com_data = []
        
        for i, file in enumerate(uploaded_files):
            col_file, col_date = st.columns([2, 1])
            with col_file:
                st.markdown(f"📄 **{file.name}**")
            with col_date:
                data_ref = st.date_input(
                    f"Data para {file.name}", 
                    key=f"d_{file.name}_{i}", 
                    label_visibility="collapsed",
                    format="DD/MM/YYYY" 
                )
                arquivos_com_data.append({"arquivo": file, "data": data_ref})

        st.divider()
        if st.button("Processar e Consolidar Censo", type="primary"):
            with st.spinner("Tratando dados do censo..."):
                df_final = processar_censo(arquivos_com_data)
                
                if df_final is not None:
                    st.success(f"Conversão concluída! {len(df_final)} setores processados.")
                    st.dataframe(df_final, use_container_width=True)
                    
                    # --- AJUSTE DO NOME DO ARQUIVO ---
                    nome_arquivo = datetime.now().strftime("CENSO_RETROATIVO_%d_%m_%Y_%H_%M_%S.csv")
                    csv = df_final.to_csv(index=False, encoding='utf-8-sig')
                    
                    st.download_button(
                        label="📥 Baixar Censo Consolidado",
                        data=csv,
                        file_name=nome_arquivo,
                        mime="text/csv"
                    )
                else:
                    st.error("Não foi possível extrair dados.")