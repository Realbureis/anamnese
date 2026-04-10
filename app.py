import streamlit as st
import base64
from io import BytesIO
import requests
from PIL import Image

# Tenta os dois nomes possíveis para a importação da conexão
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    from st_gsheets_connection import GSheetsConnection

from streamlit_drawable_canvas import st_canvas

# 1. Configuração da Página
st.set_page_config(page_title="BioEstética - Dashboard Luiza", layout="wide")

# --- FUNÇÃO MÁGICA PARA CURAR O ATTRIBUTEERROR ---
def get_canvas_compatible_image(file_id):
    url = f'https://drive.google.com/uc?id={file_id}'
    try:
        response = requests.get(url, timeout=10)
        img = Image.open(BytesIO(response.content)).convert("RGBA")
        img = img.resize((400, 733))
        
        # Converte para Base64 para evitar o erro 'image_to_url'
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}", img
    except Exception as e:
        return None, None

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
except Exception as e:
    st.error(f"Erro ao carregar planilha: {e}")
    st.stop()

# --- SIDEBAR E SELEÇÃO ---
lista_pacientes = sorted(df['nome'].dropna().unique())
paciente_selecionado = st.sidebar.selectbox("Paciente", lista_pacientes)
dados = df[df['nome'] == paciente_selecionado].iloc[0]

# --- ABAS ---
tab1, tab2 = st.tabs(["📋 Anamnese", "📐 Mapa de Medidas"])

with tab1:
    st.title(f"Paciente: {paciente_selecionado}")
    st.write(f"**Queixa:** {dados.get('queixa', 'N/A')}")

with tab2:
    st.subheader("Marcação Corporal")
    
    ID_MASCULINO = "1nQTT0v1B5Ik5OMhOtC2YMEDlZEkB-Phf"
    ID_FEMININO = "1xppoQNIJKa0ZXJzNxDYEXiPPpKJ19eX7"
    
    is_masc = str(dados.get('sexo_m')).lower() in ['true', '1.0', '1', 'sim']
    id_atual = ID_MASCULINO if is_masc else ID_FEMININO
    
    # Carregamos a imagem compatível
    bg_data_url, img_obj = get_canvas_compatible_image(id_atual)
    
    if bg_data_url:
        c1, c2 = st.columns([1.5, 1])
        with c1:
            # Passamos a URL de dados (Base64) para o background_image
            canvas_result = st_canvas(
                fill_color="rgba(255, 75, 75, 0.3)",
                stroke_width=2,
                stroke_color="#FF4B4B",
                background_image=img_obj, # O componente tentará usar a imagem
                update_streamlit=True,
                height=733, width=400,
                drawing_mode="point",
                key=f"canv_final_{paciente_selecionado}",
            )
        with c2:
            if canvas_result and canvas_result.json_data and canvas_result.json_data["objects"]:
                p = canvas_result.json_data["objects"][-1]
                st.success(f"📍 Marcado: X={int(p['left'])}, Y={int(p['top'])}")
                if st.button("Salvar Medida"):
                    st.balloons()
            else:
                st.info("Clique na imagem.")
    else:
        st.error("Certifique-se que a imagem no Drive está como 'Qualquer pessoa com o link'.")
