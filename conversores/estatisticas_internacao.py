import streamlit as st
import pandas as pd
import re

def processar_estatisticas(arquivo_upload):
    try:
        # Leitura flexível para detectar separador e encoding
        df_raw = pd.read_csv(arquivo_upload, header=None, encoding='latin-1', sep=None, engine='python', on_bad_lines='skip')
    except Exception:
        arquivo_upload.seek(0)
        df_raw = pd.read_csv(arquivo_upload, header=None, encoding='cp1252', sep=None, engine='python', on_bad_lines='skip')

    dados_finais = []
    data_atual = None

    for index, row in df_raw.iterrows():
        # 1. Captura a Data na coluna E (Índice 4)
        c4 = str(row[4]).strip() if pd.notna(row[4]) else ""
        match_data = re.search(r'(\d{2}/\d{2}/\d{4})', c4)
        if match_data:
            data_atual = match_data.group(1)
            continue
            
        # 2. Captura o Setor na coluna A (Índice 0)
        setor = str(row[0]).strip() if pd.notna(row[0]) else ""
        
        # Filtro de lixo aprimorado para ignorar cabeçalhos, totais e legendas
        palavras_bloqueadas = [
            'unidade de internação', 'unidade', 'total', 'total geral', 
            'entradas', 'saídas', 'legenda', 'emitido em', 'página'
        ]
        
        if not setor or any(p in setor.lower() for p in palavras_bloqueadas):
            continue
            
        # 3. Processamento dos dados se houver uma data ativa
        if data_atual:
            def clean_val(idx):
                try:
                    if idx >= len(row): return 0
                    v = str(row[idx]).strip()
                    if not v or v.lower() == 'nan': return 0
                    
                    # Tratamento de formato numérico BR
                    if ',' in v:
                        v = v.replace('.', '').replace(',', '.')
                    
                    # Converte para float e depois int para evitar o erro do "zero extra"
                    return int(float(v))
                except:
                    return 0

            # Mapeamento conforme coordenadas validadas
            dados_finais.append({
                'Data': data_atual,
                'Setor': setor,
                '00:00': clean_val(12),
                'Intern.': clean_val(16),
                'Transf DE': clean_val(21),
                'Altas': clean_val(26),
                'Transf PARA': clean_val(30),
                'Obitos': clean_val(34),
                'Óbitos +24Hs': clean_val(39),
                'Obitos -24Hs': clean_val(41),
                'Pac/Dia': clean_val(68)
            })

    if not dados_finais:
        return None

    df = pd.DataFrame(dados_finais)
    
    # Ordenação final por data
    df['Data_dt'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df = df.sort_values(by=['Data_dt', 'Setor']).drop(columns=['Data_dt'])

    return df

def exibir():
    # Estilização Visual (Banner e Uploader)
    st.markdown("""
        <style>
        .banner-container {
            position: relative;
            width: 100%;
            height: 150px;
            overflow: hidden;
            border-radius: 10px;
            margin-bottom: 25px;
            background-image: url('https://informasus.ufscar.br/wp-content/uploads/2020/07/image-from-rawpixel-id-259632-jpeg-scaled.jpg');
            background-size: cover;
            background-position: center center;
        }
        .banner-overlay {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 45, 90, 0.5);
            backdrop-filter: blur(4px);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .banner-text {
            color: white;
            font-size: 28px;
            font-weight: bold;
            text-align: center;
        }
        [data-testid="stFileUploadDropzone"] div div span::text { display: none; }
        [data-testid="stFileUploadDropzone"] div div span::after { content: "Arraste os arquivos R_EST_HOSPITALAR aqui"; display: block; }
        </style>
        <div class="banner-container">
            <div class="banner-overlay">
                <div class="banner-text">Estatísticas de Internação - Sintético</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    with st.expander("Instruções de Extração (MV Soul)", expanded=False):
        st.markdown("""
        1. **Internação** > **Relatórios** > **Estatísticos** > **Hospitalar** > **Sintético**.
        2. Saída: **Tela**.
        3. Manter tudo desmarcado as opções do quadro que tem as opções: **Imprimir apenas resumo** e **Quadro de resumo por unidade**.
        4. Selecionar **Todos** em **Tipo de Unidade de Internação** e **Tipo de Atendimento**.
        5. Selecionar: **Taxa Ocup. Operacional: Sim**.
        6. Tipo de impressão: **CSV**.
        """)
        st.info("ℹ️ **Segurança**: Os arquivos são processados em RAM e descartados após a conversão. Nada é armazenado.")

    uploaded_files = st.file_uploader(
        "Uploader", 
        type=["csv"], 
        accept_multiple_files=True, 
        label_visibility="collapsed",
        key="uploader_internacao"
    )

    if uploaded_files:
        lista_dfs = []
        with st.spinner("Processando relatórios..."):
            for file in uploaded_files:
                df_proc = processar_estatisticas(file)
                if df_proc is not None:
                    lista_dfs.append(df_proc)
        
        if lista_dfs:
            df_final = pd.concat(lista_dfs).drop_duplicates()
            
            df_final['Data_dt'] = pd.to_datetime(df_final['Data'], format='%d/%m/%Y')
            df_final = df_final.sort_values(by=['Data_dt', 'Setor']).drop(columns=['Data_dt'])

            st.success(f"Sucesso! {len(df_final)} registros processados.")
            st.dataframe(df_final, use_container_width=True)

            csv = df_final.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Baixar Planilha Consolidada",
                data=csv,
                file_name="estatisticas_internacao_hmsj.csv",
                mime="text/csv"
            )
        else:
            st.error("Erro: Não foi possível extrair dados. Verifique se o arquivo segue o padrão Sintético do MV.")