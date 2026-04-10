import streamlit as st

# Tenta os dois nomes possíveis para a importação da conexão
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    from st_gsheets_connection import GSheetsConnection

from streamlit_drawable_canvas import st_canvas
from PIL import Image
import pandas as pd
import requests
from io import BytesIO

# 1. Configuração da Página
st.set_page_config(page_title="BioEstética - Dashboard Luiza", layout="wide")

# --- FUNÇÃO PARA PEGAR IMAGEM DO DRIVE ---
@st.cache_data(ttl=3600)
def load_image_from_drive(file_id):
    url = f'https://drive.google.com/uc?id={file_id}'
    try:
        response = requests.get(url, timeout=10)
        return Image.open(BytesIO(response.content)).convert("RGB")
    except:
        return None

# 2. Conexão Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    url = "https://docs.google.com/spreadsheets/d/1SzYK2ocbSLisKk5oxEyqANNS8m3wZ4gcoLGSiFMNsQM/edit?usp=sharing"
    return conn.read(spreadsheet=url, ttl="0")

try:
    df_bruto = load_data()
    # Mapeamento de colunas original
    df = df_bruto.rename(columns={
        'Nome completo': 'nome', 
        'Sexo (Masculino)': 'sexo_m',
        '27. Qual sua principal queixa? E seu objetivo com o tratamento?': 'queixa',
        '6.Está grávida ou amamentando? (Sim)': 'gravida_sim',
        '4. Possui alergia a medicamentos ou\n\xa0cosméticos? (Sim)': 'alergia_sim',
        'Se sim, quais?': 'alergia_detalhe'
    })
except Exception as e:
    st.error(f"Erro ao carregar planilha: {e}")
    st.stop()

# --- SIDEBAR ---
lista_pacientes = sorted(df['nome'].dropna().unique())
paciente_selecionado = st.sidebar.selectbox("Selecione o Paciente", lista_pacientes)
dados = df[df['nome'] == paciente_selecionado].iloc[0]

# --- CABEÇALHO ---
st.title(f"Prontuário Digital: {paciente_selecionado}")

# --- ABAS ---
tab1, tab2, tab3 = st.tabs(["📋 Ficha de Anamnese", "📐 Mapa de Medidas", "📊 Evolução"])

with tab1:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🩺 Condições Clínicas")
        st.success("Nenhuma doença relatada.")
    with col2:
        st.info("⚠️ Alertas de Risco")
        if str(dados.get('alergia_sim')).lower() in ['true', '1.0', '1', 'sim']:
            st.error(f"**ALERGIA:** {dados.get('alergia_detalhe', 'Sim')}")
        else: st.success("Sem alergias.")
    with col3:
        st.info("🎯 Queixa Principal")
        st.write(dados.get('queixa', 'N/A'))

with tab2:
    st.subheader("Marcação Corporal")
    
    # Seus IDs do Drive
    ID_MASCULINO = "1nQTT0v1B5Ik5OMhOtC2YMEDlZEkB-Phf"
    ID_FEMININO = "1xppoQNIJKa0ZXJzNxDYEXiPPpKJ19eX7"
    
    is_masc = str(dados.get('sexo_m')).lower() in ['true', '1.0', '1', 'sim']
    id_atual = ID_MASCULINO if is_masc else ID_FEMININO
    
    img_drive = load_image_from_drive(id_atual)
    
    if img_drive:
        c1, c2 = st.columns([1.5, 1])
        with c1:
            img_resized = img_drive.resize((400, 733))
            canvas_result = st_canvas(
                fill_color="rgba(255, 75, 75, 0.3)",
                stroke_width=2,
                stroke_color="#FF4B4B",
                background_image=img_resized,
                update_streamlit=True,
                height=733, width=400,
                drawing_mode="point",
                key=f"canv_{paciente_selecionado}",
            )
        with c2:
            if canvas_result and canvas_result.json_data and canvas_result.json_data["objects"]:
                p = canvas_result.json_data["objects"][-1]
                st.success(f"📍 Ponto: X={int(p['left'])}, Y={int(p['top'])}")
                regiao = st.text_input("Região")
                if st.button("Salvar Medida"):
                    st.balloons()
            else: st.info("Clique na imagem para marcar.")
    else:
        st.error("Erro ao carregar silhueta do Drive.")

with tab3:
    st.write("Evolução futura.")
