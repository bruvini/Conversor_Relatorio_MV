import streamlit as st
import pandas as pd
import re

def hora_decimal(h):
    try:
        h = str(h).replace('nan', '')
        if ':' not in h: return 0.0
        hh, mm = map(int, h.split(':'))
        return hh + (mm/60)
    except: return 0.0

def limpar_perc(p):
    try: return float(str(p).replace('%', '').replace(',', '.'))
    except: return 0.0

def formatar_hora(h):
    h = str(h).replace('nan', '').strip()
    if len(h) == 4 and ':' in h: return '0' + h
    if ':' not in h: return '00:00'
    return h

def decimal_para_str(d):
    h = int(d); m = int((d - h) * 60)
    return f"{h:02d}:{m:02d}"

def processar_relatorio(arquivo_upload):
    try:
        df_raw = pd.read_csv(arquivo_upload, header=None, encoding='latin-1', on_bad_lines='skip')
    except:
        arquivo_upload.seek(0)
        df_raw = pd.read_csv(arquivo_upload, header=None, encoding='cp1252', on_bad_lines='skip')

    dados_locais = []
    cc_atual_nome = "N/D"

    for index, row in df_raw.iterrows():
        linha_texto = " ".join([str(x) for x in row if pd.notna(x)])
        col0 = str(row[0]).strip()
        if 'Centro Cir' in linha_texto and ':' in linha_texto:
            match_cc = re.search(r'Centro Cir.*?:.*?(\d+)\s+(.*)', linha_texto, re.IGNORECASE)
            if match_cc: cc_atual_nome = match_cc.group(2).strip()
            continue
        if 'Data' in linha_texto or 'Total' in linha_texto or 'Emitido' in linha_texto: continue
        if re.match(r'\d{2}/\d{2}/\d{4}', col0):
            raw_col2 = str(row[2]).strip()
            raw_col3 = str(row[3]).strip()
            nome_sala = raw_col3
            match_misturado = re.match(r'^(\d+)\s+(.+)', raw_col2)
            if match_misturado: nome_sala = match_misturado.group(2)
            elif raw_col2.replace('.', '').isdigit() and (nome_sala == 'nan' or nome_sala == ''): nome_sala = "Nome Indefinido"
            elif raw_col2 != 'nan' and not raw_col2.replace('.', '').isdigit(): nome_sala = raw_col2
            
            inicio = str(row[6]).strip() if pd.notna(row[6]) else "00:00"
            cols_validas = [str(x).strip() for x in row if pd.notna(x) and str(x).strip() != '']
            perc = 0.0; tempo_ocioso = "00:00"; fim = "00:00"
            try:
                if len(cols_validas) >= 3:
                    perc = cols_validas[-1]
                    tempo_ocioso = cols_validas[-2]
                    if pd.notna(row[7]) and ':' in str(row[7]): fim = str(row[7])
                    elif pd.notna(row[8]) and ':' in str(row[8]): fim = str(row[8])
            except: pass
            dados_locais.append({
                'Data': col0, 'Centro_Cirurgico': cc_atual_nome, 'Sala_Cirurgica': nome_sala,
                'Inicio_Funcionamento': inicio, 'Fim_Funcionamento': fim,
                'Tempo_Ocioso_Original': tempo_ocioso, '%_Ociosidade': perc
            })
    return dados_locais

def exibir():
    # 1. CSS Customizado para Tradução e Banner
    st.markdown("""
        <style>
        /* Estilo do Banner em Faixa */
        .banner-container {
            position: relative;
            width: 100%;
            height: 150px;
            overflow: hidden;
            border-radius: 10px;
            margin-bottom: 25px;
            background-image: url('https://rmscentrocirurgico.com.br/wp-content/uploads/2024/12/Equipamentos-de-ponta-em-centros-cirurgicos-O-que-isso-significa-para-voce-1024x536.jpg');
            background-size: cover;
            background-position: center 30%;
        }
        .banner-overlay {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 45, 90, 0.5); /* Blur azulado */
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
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }

        /* Tradução do File Uploader para PT-BR */
        [data-testid="stFileUploadDropzone"] div div span::text {
            display: none;
        }
        [data-testid="stFileUploadDropzone"] div div span::after {
            content: "Arraste e solte os arquivos aqui";
            display: block;
        }
        [data-testid="stFileUploadDropzone"] div div small::text {
            display: none;
        }
        [data-testid="stFileUploadDropzone"] div div small::after {
            content: "Limite de 200MB por arquivo • CSV";
            display: block;
        }
        section[data-testid="stFileUploadDropzone"] button {
            display: none;
        }
        section[data-testid="stFileUploadDropzone"]::after {
            content: "Selecionar arquivos";
            display: inline-block;
            padding: 0.5em 1em;
            background-color: #004a99;
            color: white;
            border-radius: 5px;
            margin-top: 10px;
            cursor: pointer;
            text-align: center;
        }
        </style>
        
        <div class="banner-container">
            <div class="banner-overlay">
                <div class="banner-text">Conversor de Ociosidade - Centro Cirúrgico</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Bloco de Passo a Passo
    with st.expander("Clique aqui para ver o passo a passo de como emitir o relatório no MV Soul", expanded=False):
        st.markdown("""
        ### Instruções para Extração
        1. **Acesse o MV Soul**.
        2. Selecione o módulo **Atendimento** (ícone de estetoscópio).
        3. Navegue em: **Centro Cirúrgico e Obstétrico** > **Relatórios** > **Operacionais**.
        4. Escolha a opção **Ociosidade das Salas**.
        5. Na tela de parâmetros:
            * Mantenha **Centro Cirúrgico** e **Sala Cirúrgica** como "Todos".
            * Selecione o **Período Inicial e Final** (recomendado até 3 meses).
        6. Em **Tipo de Relatório**, selecione **Analítico**.
        7. Em **Tipo de Impressão**, selecione **CSV**.
        """)
        st.info("ℹ️ **Segurança**: Os arquivos são processados em RAM e descartados após a conversão. Nada é armazenado.")

    st.write("Selecione um ou mais arquivos gerados (R_OCIO_CIR) abaixo:")
    
    # O uploader agora aparecerá estilizado/traduzido pelo CSS acima
    uploaded_files = st.file_uploader(
        "Upload CSV", 
        type=["csv"], 
        accept_multiple_files=True, 
        label_visibility="collapsed",
        key="uploader_ociosidade"
    )

    if uploaded_files:
        lista_todos_dados = []
        progress_bar = st.progress(0)
        for i, file in enumerate(uploaded_files):
            dados = processar_relatorio(file)
            if dados: lista_todos_dados.extend(dados)
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        if lista_todos_dados:
            df = pd.DataFrame(lista_todos_dados)
            # Tratamento de dados
            df['Inicio_Funcionamento'] = df['Inicio_Funcionamento'].apply(formatar_hora)
            df['Fim_Funcionamento'] = df['Fim_Funcionamento'].apply(formatar_hora)
            df['%_Ociosidade'] = df['%_Ociosidade'].apply(limpar_perc)
            df['Inicio_Dec'] = df['Inicio_Funcionamento'].apply(hora_decimal)
            df['Fim_Dec'] = df['Fim_Funcionamento'].apply(hora_decimal)
            df['Tempo_Ocioso_Decimal'] = df['Tempo_Ocioso_Original'].apply(hora_decimal)
            df['Tempo_Disponivel_Dec'] = (df['Fim_Dec'] - df['Inicio_Dec']).clip(lower=0)
            df['Tempo_Utilizado_Dec'] = (df['Tempo_Disponivel_Dec'] - df['Tempo_Ocioso_Decimal']).clip(lower=0)
            df['Tempo_Disponivel'] = df['Tempo_Disponivel_Dec'].apply(decimal_para_str)
            df['Tempo_Utilizado'] = df['Tempo_Utilizado_Dec'].apply(decimal_para_str)
            df['Tempo_Ocioso'] = df['Tempo_Ocioso_Decimal'].apply(decimal_para_str)

            df['Data_Temp'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
            df = df.sort_values(by=['Data_Temp', 'Centro_Cirurgico', 'Sala_Cirurgica'])

            cols = ['Data', 'Centro_Cirurgico', 'Sala_Cirurgica', 'Inicio_Funcionamento', 
                    'Fim_Funcionamento', 'Tempo_Disponivel', 'Tempo_Utilizado', 
                    'Tempo_Ocioso', 'Tempo_Ocioso_Decimal', '%_Ociosidade']
            
            df_final = df[cols]
            st.success(f"Compilação concluída com {len(df_final)} registros.")
            st.dataframe(df_final, use_container_width=True)
            
            csv_unificado = df_final.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Baixar Base CSV Compilada",
                data=csv_unificado,
                file_name="ociosidade_consolidada_hmsj.csv",
                mime="text/csv"
            )
        else:
            st.error("Nenhum dado válido extraído.")