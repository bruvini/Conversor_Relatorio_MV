import streamlit as st
import pandas as pd
import csv
import io
import re
from datetime import datetime

# --- CONFIGURAÇÃO DOS LAYOUTS ---
# Baseado no seu mapeamento (Excel A=0, B=1, ... T=19, AA=26, etc.)
LAYOUT_7_LARGO = {
    'min_cols': 90,          # Se a linha tiver mais que isso, é o layout 7
    'col_data': 6,           # Coluna G
    'indices': {
        '00:00': 19,         # Col T
        'Intern.': 26,       # Col AA (26)
        'Transf DE': 33,     # Col AH (33)
        'Altas': 39,         # Col AN (39)
        'Transf PARA': 44,   # Col AS (44)
        'Obitos': 50,        # Col AY (50)
        'Óbitos +24Hs': 57,  # Col BF (57)
        'Obitos -24Hs': 60,  # Col BI (60)
        'Pac/Dia': 97        # Col CT (97)
    }
}

LAYOUT_6_CURTO = {
    'min_cols': 30,          # Se a linha tiver mais que isso (e menos que 90), é o layout 6
    'col_data': 2,           # Coluna C
    'indices': {
        '00:00': 4,          # Col E
        'Intern.': 6,        # Col G
        'Transf DE': 8,      # Col I
        'Altas': 11,         # Col L
        'Transf PARA': 13,   # Col N
        'Obitos': 15,        # Col P
        'Óbitos +24Hs': 18,  # Col S
        'Obitos -24Hs': 20,  # Col U
        'Pac/Dia': 37        # Col AL (37)
    }
}

def limpar_valor(valor):
    try:
        # Remove pontos de milhar e trata decimais
        v = str(valor).strip().replace('.', '').replace(',', '.')
        if not v or v.lower() in ['nan', 'null', '']: return 0
        return int(float(v))
    except:
        return 0

def is_date(string):
    """Verifica se a string é uma data DD/MM/YYYY"""
    return bool(re.search(r'\d{2}/\d{2}/\d{4}', str(string)))

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
    
    palavras_bloqueadas = [
        'unidade de internação', 'unidade', 'total', 'total geral', 
        'entradas', 'saídas', 'legenda', 'emitido em', 'página', 
        'hospitalar', 'sintético', 'indicadores', 'saldo', 'anterior'
    ]

    for row in linhas:
        if not row: continue
        
        # --- 1. IDENTIFICAÇÃO DE DATA ---
        # Tenta achar data na linha inteira (padrão "Data: ...")
        linha_texto = " ".join(row)
        match_data = re.search(r'Data:\s*(\d{2}/\d{2}/\d{4})', linha_texto)
        if match_data:
            data_atual = match_data.group(1)
            continue
            
        # Tenta achar data nas colunas específicas mapeadas (caso não tenha o prefixo "Data:")
        if len(row) > LAYOUT_7_LARGO['col_data'] and is_date(row[LAYOUT_7_LARGO['col_data']]):
            data_atual = re.search(r'\d{2}/\d{2}/\d{4}', row[LAYOUT_7_LARGO['col_data']]).group(0)
            continue
        if len(row) > LAYOUT_6_CURTO['col_data'] and is_date(row[LAYOUT_6_CURTO['col_data']]):
            data_atual = re.search(r'\d{2}/\d{2}/\d{4}', row[LAYOUT_6_CURTO['col_data']]).group(0)
            continue

        # --- 2. SELEÇÃO DO LAYOUT ---
        # Define qual mapa usar baseado no tamanho da linha
        mapa_atual = None
        qtd_cols = len(row)
        
        if qtd_cols >= LAYOUT_7_LARGO['min_cols']:
            mapa_atual = LAYOUT_7_LARGO['indices']
        elif qtd_cols >= LAYOUT_6_CURTO['min_cols']:
            mapa_atual = LAYOUT_6_CURTO['indices']
        else:
            continue # Linha muito curta, ignora

        # --- 3. VALIDAÇÃO DA LINHA (É Setor ou Cabeçalho?) ---
        # O Setor sempre está na Coluna A (índice 0) segundo sua instrução
        setor_raw = row[0].strip()
        
        # Filtros para ignorar cabeçalhos e lixo
        if (len(setor_raw) < 3 or 
            any(p in setor_raw.lower() for p in palavras_bloqueadas) or
            is_date(setor_raw)):
            continue

        # Validação extra: Verifica se a coluna de 'Intern.' contém número ou vazio (não pode ser texto tipo 'Intern.')
        idx_intern = mapa_atual['Intern.']
        if idx_intern < qtd_cols:
            valor_intern = row[idx_intern].strip()
            if 'intern' in valor_intern.lower() or 'entradas' in valor_intern.lower():
                continue # É linha de cabeçalho repetida
        
        # --- 4. EXTRAÇÃO DOS DADOS ---
        setor = setor_raw.replace('Unidade de Internação :', '').replace('Unidade de Internação', '').strip()
        
        try:
            item = {'Data': data_atual if data_atual else "Sintético", 'Setor': setor}
            
            # Itera sobre o mapa selecionado e extrai os valores
            for col_nome, col_idx in mapa_atual.items():
                valor = 0
                if col_idx < qtd_cols:
                    valor = limpar_valor(row[col_idx])
                item[col_nome] = valor
            
            dados_finais.append(item)
            
        except Exception as e:
            # Em caso de erro numa linha específica, pula sem quebrar tudo
            continue

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

    st.markdown("### 🧭 Instruções de Extração (MV Soul)")
    st.markdown("**Caminho:** `Atendimento > Internação > Relatórios > Estatísticos > Hospitalar > Sintético`")

    col_instrucao, col_aviso = st.columns([1.2, 1])
    with col_instrucao:
        st.info("""
        **🛠️ Parâmetros Obrigatórios:**
        * **Tipo de Impressão:** CSV
        * **Unidade de Internação / Serviço / Convênio:** `%`
        * **Período:** Data Inicial e Final
        * **Tipo de Unidade de Internação:** Todos
        * **Tipo de Atendimento:** Todos
        * **Contabilizar Taxa de Ocup. Operacional:** Sim
        """)
    with col_aviso:
        st.error("""
        **⚠️ MUITA ATENÇÃO:**
        * ❌ Imprime apenas resumo
        * ❌ Resumo de Unidade por Tipo de Convênio
        """)

    st.markdown("---")

    uploaded_files = st.file_uploader("Carregue o CSV (MV):", type=["csv"], accept_multiple_files=True, key="uploader_internacao")

    if uploaded_files:
        lista_dfs = []
        with st.spinner("Identificando layout (Largo vs Curto) e processando..."):
            for file in uploaded_files:
                df_proc = processar_estatisticas(file)
                if df_proc is not None:
                    lista_dfs.append(df_proc)
        
        if lista_dfs:
            df_final = pd.concat(lista_dfs).drop_duplicates()
            st.success(f"✅ Sucesso! {len(df_final)} registros processados.")
            st.dataframe(df_final, use_container_width=True)
            
            nome_arquivo = datetime.now().strftime("ESTATISTICA_INTERNACAO_%d_%m_%Y_%H_%M_%S.csv")
            csv_data = df_final.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(label="📥 Baixar Planilha", data=csv_data, file_name=nome_arquivo, mime="text/csv")
        else:
            st.warning("⚠️ O arquivo parece vazio ou não corresponde aos layouts mapeados (Colunas G ou T).")