import streamlit as st
from st_gsheets_connection import GSheetsConnection
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import pandas as pd
import os

# 1. Configuração da Página
st.set_page_config(page_title="BioEstética - Dashboard Luiza", page_icon="🩺", layout="wide")

# 2. Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=0)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1SzYK2ocbSLisKk5oxEyqANNS8m3wZ4gcoLGSiFMNsQM/edit?usp=sharing"
    return conn.read(spreadsheet=url)

try:
    df_bruto = load_data()
except Exception as e:
    st.error(f"Erro ao conectar com a planilha: {e}")
    st.stop()

# 3. Mapeamento de Colunas (Sua interface original)
df = df_bruto.rename(columns={
    'Nome completo': 'nome',
    'Sexo (Masculino)': 'sexo_m',
    'Sexo (Feminino)': 'sexo_f',
    '1.Você possui alguma doença? (crônica, hormonal, autoimune) (Sim)': 'doenca_sim',
    'Se sim, qual?': 'doenca_detalhe',
    '6.Está grávida ou amamentando? (Sim)': 'gravida_sim',
    '4. Possui alergia a medicamentos ou\n\xa0cosméticos? (Sim)': 'alergia_sim',
    'Se sim, quais?': 'alergia_detalhe',
    '27. Qual sua principal queixa? E seu objetivo com o tratamento?': 'queixa',
    'Submitted at': 'data_envio'
})

# --- SIDEBAR ---
st.sidebar.title("🩺 Gestão de Pacientes")
lista_pacientes = sorted([n for n in df['nome'].unique() if pd.notna(n)])
paciente_sel = st.sidebar.selectbox("Selecione o Paciente", lista_pacientes)
dados = df[df['nome'] == paciente_sel].iloc[0]

# --- CABEÇALHO ---
st.title(f"Prontuário Digital: {paciente_sel}")
st.caption(f"Dados via Tally | Última Anamnese: {dados.get('data_envio', 'N/A')}")

# --- ABAS ---
tab1, tab2, tab3 = st.tabs(["📋 Ficha de Anamnese", "📐 Mapa de Medidas", "📊 Evolução"])

with tab1:
    st.subheader("Informações Coletadas")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("🩺 Condições Clínicas")
        if str(dados.get('doenca_sim')).lower() in ['true', '1.0', '1', 'sim']:
            st.error(f"**Doença:** {dados.get('doenca_detalhe', 'Relatada')}")
        else:
            st.success("Nenhuma doença relatada.")
            
    with col2:
        st.info("⚠️ Alertas de Risco")
        if str(dados.get('gravida_sim')).lower() in ['true', '1.0', '1', 'sim']:
            st.warning("⚠️ Paciente Gestante/Lactante")
        
        if str(dados.get('alergia_sim')).lower() in ['true', '1.0', '1', 'sim']:
            st.error(f"**ALERGIA:** {dados.get('alergia_detalhe', 'Relatada')}")
        else:
            st.success("Sem alergias.")

    with col3:
        st.info("🎯 Queixa Principal")
        st.write(dados.get('queixa', 'Não informado'))

    st.divider()
    st.markdown("#### 📝 Detalhes da Rotina")
    st.write(dados.get('28. Conte um pouco da sua rotina (trabalho, cuidados com a pele, alimentação...)', 'N/A'))

with tab2:
    st.subheader("Marcação Corporal")
    
    is_m = str(dados.get('sexo_m')).lower() in ['true', '1.0', '1', 'sim']
    nome_img = "homem.png" if is_m else "mulher.png"
    
    if os.path.exists(nome_img):
        img_pil = Image.open(nome_img).convert("RGB")
        img_resized = img_pil.resize((400, 733))
        
        c1, c2 = st.columns([1.5, 1])
        with c1:
            canvas_result = st_canvas(
                fill_color="rgba(255, 75, 75, 0.3)",
                stroke_width=2,
                stroke_color="#FF4B4B",
                background_image=img_resized,
                update_streamlit=True,
                height=733,
                width=400,
                drawing_mode="point",
                key=f"canv_prod_{paciente_sel}",
            )
        with c2:
            if canvas_result.json_data and canvas_result.json_data["objects"]:
                p = canvas_result.json_data["objects"][-1]
                st.success(f"📍 Ponto: X={int(p['left'])}, Y={int(p['top'])}")
                regiao = st.text_input("Região")
                if st.button("Salvar Medida"):
                    st.balloons()
    else:
        st.error(f"Arquivo {nome_img} não encontrado no GitHub.")

with tab3:
    st.write("Evolução futura.")
