import streamlit as st
import pandas as pd
from PIL import Image
import os
import base64
from io import BytesIO
from streamlit_drawable_canvas import st_canvas

# 1. Configuração da Página
st.set_page_config(page_title="BioEstética - Dashboard Luiza", layout="wide")

# --- FUNÇÃO MÁGICA PARA CURAR O ERRO image_to_url ---
def get_image_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# 2. Importação Flexível
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    from st_gsheets_connection import GSheetsConnection

# 3. Conexão
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    url = "https://docs.google.com/spreadsheets/d/1SzYK2ocbSLisKk5oxEyqANNS8m3wZ4gcoLGSiFMNsQM/edit?usp=sharing"
    return conn.read(spreadsheet=url)

df_bruto = load_data()
df = df_bruto.rename(columns={'Nome completo': 'nome', 'Sexo (Masculino)': 'sexo_m'})

# --- SIDEBAR ---
lista_pacientes = sorted([n for n in df['nome'].unique() if pd.notna(n)])
paciente_sel = st.sidebar.selectbox("Paciente", lista_pacientes)
dados = df[df['nome'] == paciente_sel].iloc[0]

# --- INTERFACE ---
st.title(f"Prontuário: {paciente_sel}")
tab1, tab2 = st.tabs(["📋 Ficha", "📐 Mapa de Medidas"])

with tab1:
    st.info("🎯 Queixa Principal")
    st.write(dados.get('27. Qual sua principal queixa? E seu objetivo com o tratamento?', 'N/A'))

with tab2:
    st.subheader("Marcação Corporal")
    is_m = str(dados.get('sexo_m')).lower() in ['true', '1.0', '1', 'sim']
    nome_img = "homem.png" if is_m else "mulher.png"
    
    if os.path.exists(nome_img):
        img_pil = Image.open(nome_img).convert("RGBA")
        img_pil = img_pil.resize((400, 733))
        
        # AQUI ESTÁ O FIX: Transformamos a imagem em texto para enganar o erro
        # bg_image no canvas agora aceita o objeto PIL direto se o Streamlit não interferir
        
        c1, c2 = st.columns([1.5, 1])
        with c1:
            canvas_result = st_canvas(
                fill_color="rgba(255, 75, 75, 0.3)",
                stroke_width=2,
                stroke_color="#FF4B4B",
                background_image=img_pil,
                update_streamlit=True,
                height=733,
                width=400,
                drawing_mode="point",
                key=f"canvas_final_v20_{paciente_sel}", # Key nova para resetar o erro
            )
        with c2:
            if canvas_result.json_data and canvas_result.json_data["objects"]:
                p = canvas_result.json_data["objects"][-1]
                st.success(f"📍 Ponto: X={int(p['left'])}, Y={int(p['top'])}")
                if st.button("Salvar Medida"):
                    st.balloons()
    else:
        st.error(f"Arquivo {nome_img} não encontrado no GitHub.")
