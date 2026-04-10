import streamlit as st
import pandas as pd
from PIL import Image
import os
from streamlit_drawable_canvas import st_canvas

# 1. Configuração da Página (Sua Interface)
st.set_page_config(page_title="BioEstética - Dashboard Luiza", layout="wide")

# 2. Importação Flexível (Resolve o ModuleNotFoundError)
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    try:
        from st_gsheets_connection import GSheetsConnection
    except:
        st.error("Erro técnico: Bibliotecas de conexão não encontradas.")
        st.stop()

# 3. Conexão e Dados
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=0)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1SzYK2ocbSLisKk5oxEyqANNS8m3wZ4gcoLGSiFMNsQM/edit?usp=sharing"
    return conn.read(spreadsheet=url)

try:
    df = load_data().rename(columns={
        'Nome completo': 'nome',
        'Sexo (Masculino)': 'sexo_m',
        '27. Qual sua principal queixa? E seu objetivo com o tratamento?': 'queixa'
    })
except:
    st.error("Erro ao carregar planilha.")
    st.stop()

# --- SIDEBAR ---
paciente_sel = st.sidebar.selectbox("Paciente", sorted(df['nome'].unique()))
dados = df[df['nome'] == paciente_sel].iloc[0]

# --- INTERFACE ORIGINAL ---
st.title(f"Prontuário: {paciente_sel}")
tab1, tab2 = st.tabs(["📋 Anamnese", "📐 Mapa de Medidas"])

with tab1:
    col1, col2, col3 = st.columns(3)
    with col1: st.info("🩺 Condições"); st.write("Verificar Anamnese")
    with col2: st.warning("⚠️ Alertas"); st.write("Verificar Alergias")
    with col3: st.info("🎯 Queixa"); st.write(dados.get('queixa', 'N/A'))

with tab2:
    st.subheader("Marcação Corporal")
    
    # Lógica de imagem local (você já subiu os arquivos)
    is_m = str(dados.get('sexo_m')).lower() in ['true', '1.0', '1', 'sim']
    nome_img = "homem.png" if is_m else "mulher.png"
    
    if os.path.exists(nome_img):
        img_pil = Image.open(nome_img).convert("RGB")
        
        # CRITICAL FIX: Redimensionamos MANUALMENTE para evitar o erro de 'height'
        # Isso evita que o componente tente usar a função bugada do Streamlit
        largura, altura = 400, 733
        img_resized = img_pil.resize((largura, altura))
        
        c1, c2 = st.columns([1.5, 1])
        
        with c1:
            canvas_result = st_canvas(
                fill_color="rgba(255, 75, 75, 0.3)",
                stroke_width=2,
                stroke_color="#FF4B4B",
                background_image=img_resized, # Imagem já no tamanho certo
                update_streamlit=True,
                height=altura, # Altura fixa
                width=largura, # Largura fixa
                drawing_mode="point",
                key=f"canv_{paciente_sel}",
            )
        
        with c2:
            if canvas_result.json_data and canvas_result.json_data["objects"]:
                p = canvas_result.json_data["objects"][-1]
                st.success(f"📍 Ponto: X={int(p['left'])}, Y={int(p['top'])}")
                regiao = st.text_input("Região")
                if st.button("Salvar Medida"):
                    st.balloons()
            else:
                st.info("Clique na imagem para marcar.")
    else:
        st.error(f"Arquivo {nome_img} não encontrado no GitHub.")
