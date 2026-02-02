import streamlit as st
import pandas as pd
import csv
import io
import re

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

    for row in linhas:
        if not row: continue
        
        # 1. Captura a Data na coluna C (Índice 2)
        # O padrão no CSV analítico é uma linha de cabeçalho com a data
        col_c = row[2].strip() if len(row) > 2 else ""
        match_data = re.search(r'(\d{2}/\d{2}/\d{4})', col_c)
        if match_data:
            data_atual = match_data.group(1)
            continue
            
        # 2. Captura o Setor na coluna A (Índice 0)
        setor_raw = str(row[0]).strip() if len(row) > 0 else ""
        
        # Ignora as linhas de resumo por dia que aparecem no final do bloco (onde Col A é uma data)
        if re.match(r'\d{2}/\d{2}/\d{4}', setor_raw):
            continue
            
        # Limpeza do texto do setor (remove prefixos do MV)
        setor = setor_raw.replace('Unidade de Internação :', '').replace('Unidade de Internação', '').strip()
        
        # Filtro de lixo: ignora linhas vazias ou cabeçalhos
        if not setor or any(p in setor.lower() for p in palavras_bloqueadas) or len(setor) < 3:
            continue
            
        # 3. Processamento dos dados se houver uma data capturada
        if data_atual:
            dados_finais.append({
                'Data': data_atual,
                'Setor': setor,
                '00:00': limpar_valor(row[4]) if len(row) > 4 else 0,         # Col E
                'Intern.': limpar_valor(row[6]) if len(row) > 6 else 0,       # Col G
                'Transf DE': limpar_valor(row[8]) if len(row) > 8 else 0,     # Col I
                'Altas': limpar_valor(row[11]) if len(row) > 11 else 0,       # Col L
                'Transf PARA': limpar_valor(row[13]) if len(row) > 13 else 0, # Col N
                'Obitos': limpar_valor(row[15]) if len(row) > 15 else 0,      # Col P
                'Óbitos +24Hs': limpar_valor(row[18]) if len(row) > 18 else 0, # Col S
                'Obitos -24Hs': limpar_valor(row[20]) if len(row) > 20 else 0, # Col U
                'Pac/Dia': limpar_valor(row[37]) if len(row) > 37 else 0      # Col AL
            })

    if not dados_finais:
        return None

    df = pd.DataFrame(dados_finais)
    
    # Ordenação final cronológica
    df['Data_dt'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    df = df.sort_values(by=['Data_dt', 'Setor']).drop(columns=['Data_dt'])

    return df

def exibir():
    # Estilização Visual do Banner
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
        ### Como extrair o arquivo correto:
        1. **Internação** > **Relatórios** > **Estatísticos** > **Hospitalar** > **Sintético**.
        2. Saída: **Tela**.
        3. **IMPORTANTE: Mantenha DESMARCADAS** as opções:
            * *Imprimir apenas resumo*
            * *Quadro de resumo por unidade*
        4. Selecionar **Todos** em **Tipo de Unidade de Internação** e **Tipo de Atendimento**.
        5. Selecionar: **Taxa Ocup. Operacional: Sim**.
        6. Tipo de impressão: **CSV**.
        """)
        st.info("ℹ️ **Nota**: Agora não é mais necessário informar a data manualmente. O sistema captura as datas de cada dia automaticamente de dentro do arquivo.")

    uploaded_files = st.file_uploader(
        "Uploader", 
        type=["csv"], 
        accept_multiple_files=True, 
        label_visibility="collapsed",
        key="uploader_internacao"
    )

    if uploaded_files:
        lista_dfs = []
        with st.spinner("Processando relatórios por período..."):
            for file in uploaded_files:
                df_proc = processar_estatisticas(file)
                if df_proc is not None:
                    lista_dfs.append(df_proc)
        
        if lista_dfs:
            df_final = pd.concat(lista_dfs).drop_duplicates()
            
            # Ordenação final garantida
            df_final['Data_dt'] = pd.to_datetime(df_final['Data'], format='%d/%m/%Y', errors='coerce')
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
            st.error("Erro: Não foi possível extrair dados. Verifique se as opções de resumo foram desmarcadas na extração do MV.")