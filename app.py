import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import json
from pypdf import PdfReader

st.set_page_config(page_title="Gestor Financeiro Inteligente", page_icon="💵", layout="wide")

# --- PALETA DE CORES DA SUA PLANILHA (CSS PERSONALIZADO) ---
st.markdown("""
<style>
    /* Fundo geral e fontes */
    .stApp {
        background-color: #121212;
        color: #F3E5AB;
    }
    
    /* Barra Lateral */
    section[data-testid="stSidebar"] {
        background-color: #1A1A1A;
        border-right: 1px solid #2A2415;
    }
    
    /* Títulos e Cabeçalhos */
    h1, h2, h3, h4, h5, h6 {
        color: #D4AF37 !important;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Abas / Tabs */
    button[data-baseweb="tab"] {
        color: #CCCCCC !important;
        background-color: transparent !important;
    }
    button[aria-selected="true"] {
        color: #D4AF37 !important;
        border-bottom-color: #D4AF37 !important;
        font-weight: bold;
    }
    
    /* Cards de Métricas / KPIs */
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        border: 1px solid #2A2415;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.4);
    }
    div[data-testid="stMetricLabel"] p {
        color: #C5A059 !important;
        font-size: 0.95rem !important;
        font-weight: bold;
    }
    div[data-testid="stMetricValue"] div {
        color: #FFFFFF !important;
        font-weight: bold;
    }
    
    /* Botões */
    div.stButton > button {
        background-color: #2A2415;
        color: #D4AF37;
        border: 1px solid #D4AF37;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s;
    }
    div.stButton > button:hover {
        background-color: #D4AF37;
        color: #121212;
        border-color: #D4AF37;
    }
    
    /* Inputs */
    input, textarea, select {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. GERENCIAMENTO DE USUÁRIOS E SESSÃO ---
if "usuarios" not in st.session_state:
    st.session_state["usuarios"] = {
        "admin": "admin123",
        "Marcos": "1234"
    }

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""
if "transacoes" not in st.session_state:
    st.session_state["transacoes"] = []

def tela_autenticacao():
    st.markdown("<h2 style='text-align: center; color: #D4AF37;'>💵 PAINEL DE CONTROLE FINANCEIRO</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #F3E5AB;'>Gerenciamento e análise de gastos</p>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        aba_login, aba_cadastro = st.tabs(["🔑 Entrar", "📝 Criar Conta"])
        
        with aba_login:
            st.subheader("Acesse sua conta")
            usuario = st.text_input("Usuário", key="login_user")
            senha = st.text_input("Senha", type="password", key="login_pass")
            
            if st.button("Entrar", use_container_width=True):
                if usuario in st.session_state["usuarios"] and st.session_state["usuarios"][usuario] == senha:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_logado"] = usuario
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
                    
        with aba_cadastro:
            st.subheader("Novo Cadastro")
            novo_usuario = st.text_input("Escolha um Nome de Usuário", key="cad_user")
            nova_senha = st.text_input("Crie uma Senha", type="password", key="cad_pass")
            confirma_senha = st.text_input("Confirme sua Senha", type="password", key="cad_pass_conf")
            
            if st.button("Cadastrar", use_container_width=True):
                if not novo_usuario or not nova_senha:
                    st.warning("Preencha todos os campos.")
                elif novo_usuario in st.session_state["usuarios"]:
                    st.error("Este nome de usuário já existe.")
                elif nova_senha != confirma_senha:
                    st.error("As senhas não coincidem.")
                else:
                    st.session_state["usuarios"][novo_usuario] = nova_senha
                    st.success("Conta criada com sucesso! Acesse na aba 'Entrar'.")

if not st.session_state["autenticado"]:
    tela_autenticacao()
    st.stop()

# --- GESTÃO DA CHAVE DE API (AUTOMÁTICA OU MANUAL) ---
api_key = ""
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['usuario_logado']}")
    if st.session_state["usuario_logado"] == "admin":
        st.caption("🛡️ Perfil: Administrador")
        with st.expander("👥 Usuários Cadastrados"):
            st.write(list(st.session_state["usuarios"].keys()))
            
    st.markdown("---")
    
    if not api_key:
        st.subheader("⚙️ Configurações de IA")
        api_key = st.text_input("Gemini API Key", type="password", help="Pegue gratuitamente em aistudio.google.com")
        st.markdown("---")
        
    if st.button("Sair da Conta", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.rerun()

# --- 2. FUNÇÃO PARA LER EXTRATO COM GEMINI ---
def processar_extrato_pdf(file, chave_api):
    reader = PdfReader(file)
    texto_extrato = ""
    for page in reader.pages:
        texto_extrato += page.extract_text() or ""
        
    if not texto_extrato.strip():
        raise Exception("Não foi possível extrair texto do PDF. O arquivo pode ser uma imagem escaneada.")

    genai.configure(api_key=chave_api)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={"response_mime_type": "application/json"}
    )
    
    prompt = f"""
    Você é um assistente financeiro especialista. Analise o extrato bancário abaixo e extraia TODAS as transações.
    Retorne EXCLUSIVAMENTE um array JSON contendo objetos com os seguintes campos:
    - "data": string (formato DD/MM/AAAA)
    - "descricao": string (nome da pessoa, loja ou serviço)
    - "tipo": string ("Receita" para entradas/rendimentos ou "Despesa" para pagamentos/débitos/saídas)
    - "categoria": string (escolha entre: Alimentação, Transporte, Lazer / Outros, Cartão de credito, Salário, Investimento, Vendas, Conta Mensal)
    - "valor": float (valor numérico positivo com ponto, ex: 35.50)

    EXTRATO:
    {texto_extrato}
    """
    
    response = model.generate_content(prompt)
    
    texto_resposta = response.text.strip()
    if texto_resposta.startswith("```json"):
        texto_resposta = texto_resposta[7:]
    if texto_resposta.startswith("```"):
        texto_resposta = texto_resposta[3:]
    if texto_resposta.endswith("```"):
        texto_resposta = texto_resposta[:-3]
        
    return json.loads(texto_resposta.strip())

# --- 3. INTERFACE PRINCIPAL ---
st.markdown("<h2 style='color: #D4AF37;'>💵 PAINEL DE CONTROLE FINANCEIRO</h2>", unsafe_allow_html=True)

tab_upload, tab_dashboard, tab_plane
