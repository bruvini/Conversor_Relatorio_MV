import streamlit as st
import pandas as pd
import re
import io
from datetime import datetime

# --- FUNÇÕES DE UTILIDADE ---
def is_date(val):
    return bool(re.match(r'\d{2}/\d{2}/\d{4}', str(val).strip()))

def is_time(val):
    return bool(re.match(r'^\d{1,2}:\d{2}$', str(val).strip()))

def to_excel_time(time_str):
    """Converte HH:MM para fração do dia (Ex: 07:00 -> 0.291666)"""
    try:
        if not time_str or ':' not in str(time_str): return 0.0
        h, m = map(int, str(time_str).split(':'))
        # No Excel, 1 dia = 1.0. Então dividimos o total de horas por 24.
        decimal_hours = h + m / 60.0
        return round(decimal_hours / 24.0, 10)
    except: return 0.0

# --- LÓGICA DE PROCESSAMENTO ---
def processar_relatorio(arquivo_upload):
    try:
        df_raw = pd.read_csv(arquivo_upload, header=None, encoding='latin-1', on_bad_lines='skip')
    except:
        arquivo_upload.seek(0)
        df_raw = pd.read_csv(arquivo_upload, header=None, encoding='cp1252', on_bad_lines='skip')

    rows = df_raw.values.tolist()
    current_cc, current_date, data_consolidada = "N/D", None, []

    for i, row in enumerate(rows):
        row_str = [str(x).strip() if pd.notna(x) else "" for x in row]
        row_joined = " ".join(row_str).lower()
        
        # Identifica Centro Cirúrgico
        if "centro cir" in row_joined:
            for idx, val in enumerate(row_str):
                if "centro cir" in val.lower():
                    for j in range(idx + 1, len(row_str)):
                        cand = row_str[j].strip()
                        if cand and not cand.isdigit() and cand != ":":
                            if "centro cir" in cand.lower() and cand.endswith(":"):
                                continue
                            current_cc = cand
                            break
                    break
            continue

        if "total de horas" in row_joined or "funcionamento" in row_joined: continue
        if is_date(row_str[0]): current_date = row_str[0]
        
        times_in_row = [val for val in row_str if is_time(val)]
        
        if len(times_in_row) >= 2:
            room_name, found_room = "", False
            for idx in range(0, 5): 
                if idx >= len(row_str) or is_time(row_str[idx]): break
                if row_str[idx].isdigit():
                    for n_idx in range(idx + 1, idx + 4):
                        if n_idx < len(row_str) and row_str[n_idx] and not is_time(row_str[n_idx]) and not row_str[n_idx].isdigit():
                            room_name = row_str[n_idx]
                            found_room = True
                            break
                    if found_room: break

            if found_room and current_date:
                # Lógica de colunas dinâmicas
                if is_time(row_str[6]) and len(row_str) > 14: # Layout Largo
                    inicio, fim, ociosa, perc_str = row_str[6], row_str[7], row_str[13], row_str[14]
                elif is_time(row_str[4]) and len(row_str) > 11: # Layout Estreito
                    inicio, fim, ociosa, perc_str = row_str[4], row_str[5], row_str[10], row_str[11]
                else:
                    inicio, fim = times_in_row[0], times_in_row[1]
                    perc_str = row_str[-1]
                    ociosa = times_in_row[-1]

                # Convertendo para fração de dia (Padrão Planilha)
                start_val = to_excel_time(inicio)
                end_val = to_excel_time(fim)
                ociosa_val = to_excel_time(ociosa)
                disp_val = round(end_val - start_val, 10)
                util_val = round(max(0, disp_val - ociosa_val), 10)
                
                try: p = float(perc_str.replace('%', '').replace(',', '.'))
                except: p = (ociosa_val / disp_val * 100) if disp_val > 0 else 0.0

                data_consolidada.append({
                    'Data': current_date,
                    'Centro_Cirurgico': current_cc,
                    'Sala_Cirurgica': room_name,
                    'Inicio_Funcionamento': start_val,
                    'Fim_Funcionamento': end_val,
                    'Tempo_Disponivel': disp_val,
                    'Tempo_Utilizado': util_val,
                    'Tempo_Ocioso': ociosa_val,
                    # NOVA COLUNA AQUI: Multiplica a fração do dia por 24 horas
                    'Tempo_Ocioso_Decimal': round(ociosa_val * 24, 2),
                    '%_Ociosidade': round(p, 2)
                })
    return data_consolidada

# --- FUNÇÃO PRINCIPAL ---
def exibir():
    st.markdown("""
        <style>
        .banner-container {
            position: relative; width: 100%; height: 150px; overflow: hidden; border-radius: 10px; margin-bottom: 25px;
            background-image: url('https://rmscentrocirurgico.com.br/wp-content/uploads/2024/12/Equipamentos-de-ponta-em-centros-cirurgicos-O-que-isso-significa-para-voce-1024x536.jpg');
            background-size: cover; background-position: center 30%;
        }
        .banner-overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 45, 90, 0.5); backdrop-filter: blur(4px);
            display: flex; align-items: center; justify-content: center;
        }
        .banner-text { color: white; font-size: 28px; font-weight: bold; text-align: center; }
        </style>
        <div class="banner-container">
            <div class="banner-overlay"><div class="banner-text">Conversor de Ociosidade - Centro Cirúrgico</div></div>
        </div>
    """, unsafe_allow_html=True)

    with st.expander("Instruções para Extração no MV Soul"):
        st.markdown("1. **Atendimento** > **Centro Cirúrgico** > **Relatórios** > **Operacionais** > **Ociosidade das Salas**.\n2. Tipo: **Analítico** | Impressão: **CSV**.")

    uploaded_files = st.file_uploader("Upload de arquivos CSV", type=["csv"], accept_multiple_files=True)

    if uploaded_files:
        lista_total = []
        for file in uploaded_files:
            dados = processar_relatorio(file)
            if dados: lista_total.extend(dados)
        
        if lista_total:
            df = pd.DataFrame(lista_total)
            st.success(f"Processado: {len(df)} registros.")
            st.dataframe(df, use_container_width=True)
            
            # --- AREA DE DOWNLOAD ---
            nome_arquivo = datetime.now().strftime("OCIOSIDADE_SALA_CIRURGICA_%d_%m_%Y_%H_%M_%S.csv")
            csv_download = df.to_csv(index=False, encoding='utf-8-sig', decimal=',') # decimal=',' ajuda o Excel BR
            
            st.download_button(
                label="📥 Baixar Base Consolidada (CSV)",
                data=csv_download,
                file_name=nome_arquivo,
                mime="text/csv"
            )