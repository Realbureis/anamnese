import streamlit as st
import base64
import requests
from io import BytesIO
from PIL import Image

# Tratamento de importação da conexão
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    from st_gsheets_connection import GSheetsConnection

from streamlit_drawable_canvas import st_canvas

# 1. Configuração da Página
st.set_page_config(page_title="BioEstética - Dashboard Luiza", layout="wide")

# --- FUNÇÃO TÉCNICA PARA EVITAR O ERRO 'image_to_url' ---
def get_as_base64(file_id):
    url = f'https://drive.google.com/uc?id={file_id}'
    try:
        response = requests.get(url, timeout=15)
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        img = img.resize((400, 733))
        # O segredo: Converter para Base64 para o componente não tentar criar URL
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except:
        return None

# 2. Conexão Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    url = "https://docs.google.com/spreadsheets/d/1SzYK2ocbSLisKk5oxEyqANNS8m3wZ4gcoLGSiFMNsQM/edit?usp=sharing"
    return conn.read(spreadsheet=url, ttl="0")

try:
    df_bruto = load_data()
    df = df_bruto.rename(columns={
        'Nome completo': 'nome', 
        'Sexo (Masculino)': 'sexo_m',
        '27. Qual sua principal queixa? E seu objetivo com o tratamento?': 'queixa'
    })
except:
    st.error("Erro ao carregar planilha.")
    st.stop()

# --- SIDEBAR ---
lista_pacientes = sorted(df['nome'].dropna().unique())
paciente_selecionado = st.sidebar.selectbox("Selecione o Paciente", lista_pacientes)
dados = df[df['nome'] == paciente_selecionado].iloc[0]

st.title(f"Prontuário: {paciente_selecionado}")

# --- MAPA DE MEDIDAS ---
st.subheader("📐 Mapa de Medidas Corporal")

# IDs do seu Google Drive
ID_MASCULINO = "1nQTT0v1B5Ik5OMhOtC2YMEDlZEkB-Phf"
ID_FEMININO = "1xppoQNIJKa0ZXJzNxDYEXiPPpKJ19eX7"

is_masc = str(dados.get('sexo_m')).lower() in ['true', '1.0', '1', 'sim']
id_escolhido = ID_MASCULINO if is_masc else ID_FEMININO

# Obtemos a imagem já formatada em Base64
img_b64 = get_as_base64(id_escolhido)

if img_b64:
    col_mapa, col_info = st.columns([1.5, 1])
    
    with col_mapa:
        # AQUI É O PONTO CRÍTICO: 
        # Passamos a string Base64 DIRETAMENTE para o background_image
        canvas_result = st_canvas(
            fill_color="rgba(255, 75, 75, 0.3)",
            stroke_width=2,
            stroke_color="#FF4B4B",
            background_image=img_b64, # Não passamos o objeto Image, mas a string
            update_streamlit=True,
            height=733,
            width=400,
            drawing_mode="point",
            key=f"canvas_v_final_{paciente_selecionado}",
        )
    
    with col_info:
        if canvas_result.json_data and canvas_result.json_data["objects"]:
            ponto = canvas_result.json_data["objects"][-1]
            st.success(f"📍 Marcado: X={int(ponto['left'])}, Y={int(ponto['top'])}")
            regiao = st.text_input("Região")
            if st.button("Salvar Medida"):
                st.balloons()
        else:
            st.info("Clique na silhueta para marcar um ponto.")
else:
    st.error("Erro ao carregar a imagem do Drive. Verifique a permissão de compartilhamento.")
