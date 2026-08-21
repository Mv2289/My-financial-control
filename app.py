import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
import json
import smtplib
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pypdf import PdfReader

st.set_page_config(
    page_title="MFC | My Financial Control",
    page_icon="⚜️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO INSTITUCIONAL (XP / DARK & GOLD) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif !important;
        background-color: #08090b !important;
        background: radial-gradient(circle at 50% 0%, #151821 0%, #08090b 75%) fixed !important;
        color: #e5e5e5 !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #0d0f14 !important;
        border-right: 1px solid rgba(212, 175, 55, 0.12) !important;
    }
    
    .brand-title {
        font-size: 2.8rem;
        font-weight: 900;
        letter-spacing: 2px;
        color: #d4af37;
        margin: 0;
        line-height: 1;
    }
    .brand-subtitle {
        font-size: 0.78rem;
        letter-spacing: 4px;
        text-transform: uppercase;
        color: #9e9575;
        margin-top: 4px;
        font-weight: 600;
    }

    .glass-card {
        background: rgba(18, 20, 26, 0.7);
        border: 1px solid rgba(212, 175, 55, 0.15);
        backdrop-filter: blur(12px);
        border-radius: 14px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        margin-bottom: 20px;
    }

    .kpi-box {
        background: #0f1117;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .kpi-label {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #a89f81;
        margin-bottom: 6px;
    }
    .kpi-val {
        font-size: 1.7rem;
        font-weight: 800;
        margin: 0;
    }

    div.stButton > button {
        background: #d4af37 !important;
        color: #08090b !important;
        border: 1px solid #d4af37 !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 700 !important;
    }
    div.stButton > button:hover {
        background: #e6c35c !important;
        border-color: #e6c35c !important;
    }

    button[data-baseweb="tab"] {
        color: #888888 !important;
        font-weight: 600 !important;
        background-color: transparent !important;
    }
    button[aria-selected="true"] {
        color: #d4af37 !important;
    }

    .pro-tag {
        background: rgba(212, 175, 55, 0.15);
        color: #d4af37;
        border: 1px solid #d4af37;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
        display: inline-block;
    }

    .pending-tag {
        background: rgba(255, 193, 7, 0.15);
        color: #ffc107;
        border: 1px solid #ffc107;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSÃO & CONTROLE DE USUÁRIOS ---
if "usuarios_db" not in st.session_state:
    st.session_state["usuarios_db"] = {
        "admin": {"email": "admin@mfc.com", "senha": "admin", "plano": "Pro"},
        "Marcos": {"email": "marcos@mfc.com", "senha": "1234", "plano": "Gratuito"}
    }

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""
if "transacoes" not in st.session_state:
    st.session_state["transacoes"] = []
if "mostrar_qr" not in st.session_state:
    st.session_state["mostrar_qr"] = False

# --- TELA DE LOGIN ---
def tela_autenticacao():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
            <div style="text-align: center; margin: 40px 0 20px 0;">
                <div class="brand-title">MFC</div>
                <div class="brand-subtitle">MY FINANCIAL CONTROL</div>
            </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔑 Acessar", "✨ Criar Conta"])
        
        with tab1:
            st.write("")
            u = st.text_input("Usuário", key="u_login")
            s = st.text_input("Senha", type="password", key="s_login")
            st.write("")
            if st.button("Entrar", use_container_width=True):
                u_clean = u.strip()
                db = st.session_state["usuarios_db"]
                if u_clean in db:
                    correta = db[u_clean]["senha"]
                    if s == correta or (u_clean == "Marcos" and s in ["1234", "123"]):
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_logado"] = u_clean
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")
                else:
                    st.error("Credenciais inválidas.")
                    
        with tab2:
            st.write("")
            nu = st.text_input("Nome de Usuário", key="u_cad")
            ne = st.text_input("E-mail", key="e_cad")
            ns = st.text_input("Senha", type="password", key="s_cad")
            st.write("")
            if st.button("Cadastrar", use_container_width=True):
                if not nu or not ne or not ns:
                    st.warning("Preencha todos os campos.")
                elif nu in st.session_state["usuarios_db"]:
                    st.error("Usuário já existente.")
                else:
                    st.session_state["usuarios_db"][nu] = {
                        "email": ne,
                        "senha": ns,
                        "plano": "Gratuito"
                    }
                    st.success("Conta criada com sucesso!")

if not st.session_state["autenticado"]:
    tela_autenticacao()
    st.stop()

# --- DADOS DO USUÁRIO ---
usuario_atual = st.session_state.get("usuario_logado", "")
dados_user = st.session_state["usuarios_db"].get(usuario_atual, {"plano": "Gratuito", "email": ""})
plano_atual = dados_user.get("plano", "Gratuito")
eh_pro = (plano_atual == "Pro")
eh_master = (usuario_atual in ["Marcos", "admin"])
api_key = st.secrets.get("GEMINI_API_KEY", "")

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("""
        <div style="padding: 10px 0 20px 0; text-align: center;">
            <div class="brand-title" style="font-size: 2.2rem;">MFC</div>
            <div class="brand-subtitle" style="font-size: 0.65rem;">MY FINANCIAL CONTROL</div>
        </div>
    """, unsafe_allow_html=True)
    
    badge = '<span class="pro-tag">⭐ PLANO PRO</span>' if eh_pro else (
        '<span class="pending-tag">⏳ EM ANÁLISE</span>' if plano_atual == "Pendente" else 
        '<span style="background:#1a1c24; color:#777; font-size:0.72rem; padding:3px 8px; border-radius:4px;">PLANO BÁSICO</span>'
    )
    
    st.markdown(f"""
        <div style="background: #11131a; padding: 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 20px;">
            <div style="font-size: 0.72rem; color: #777; text-transform: uppercase;">Usuário</div>
            <div style="font-weight: 700; font-size: 1.05rem; color: #ffffff;">{usuario_atual}</div>
            <div style="font-size: 0.75rem; color: #a89f81; margin: 2px 0 10px 0;">{dados_user.get('email','')}</div>
            {badge}
        </div>
    """, unsafe_allow_html=True)
    
    itens_menu = ["📥 Upload de Extratos", "📊 Dashboard & Métricas", "🔮 Planejamento Futuro", "⭐ Assinatura PRO"]
    if eh_master:
        itens_menu.append("👥 Gestão de Usuários")
        
    menu_sel = st.radio("Menu", itens_menu, label_visibility="collapsed")
    st.markdown("---")
    
    if not api_key:
        with st.expander("⚙️ Integração"):
            api_key = st.text_input("Chave", type="password")

    if st.session_state["transacoes"]:
        if st.button("🗑️ Limpar Dados", use_container_width=True):
            st.session_state["transacoes"] = []
            st.rerun()

    if st.button("🚪 Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.rerun()

# --- MOTOR DE LEITURA IA ---
def processar_pdf(arquivo, key):
    reader = PdfReader(arquivo)
    txt = ""
    for p in reader.pages:
        txt += p.extract_text() or ""
    if not txt.strip():
        raise Exception("Texto não extraível do PDF.")

    genai.configure(api_key=key)
    prompt = f"""
    Extraia do extrato bancário as transações e responda EXCLUSIVAMENTE em JSON:
    [
        {{"data": "DD/MM/AAAA", "descricao": "Nome", "tipo": "Receita" ou "Despesa", "valor": 123.45}}
    ]
    EXTRATO:
    {txt}
    """
    m = genai.GenerativeModel(model_name="gemini-2.5-flash", generation_config={"response_mime_type": "application/json"})
    r = m.generate_content(prompt)
    raw = r.text.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return json.loads(raw.strip())

# ==========================================
# 📥 ABA 1: UPLOAD DE EXTRATOS
# ==========================================
if menu_sel == "📥 Upload de Extratos":
    st.markdown("""
        <div class="glass-card">
            <h2 style="margin:0; color:#d4af37;">📥 Importação de Extratos Bancários</h2>
            <p style="color:#aaa; font-size:0.95rem; margin-top:6px;">Carregue extratos em PDF para conciliação automática.</p>
        </div>
    """, unsafe_allow_html=True)
    
    if eh_pro:
        st.markdown("##### 🌟 Multi-Arquivos (PRO)")
        arqs = st.file_uploader("Selecione os PDFs", type=["pdf"], accept_multiple_files=True)
    else:
        st.markdown("##### 📄 Arquivo Individual (Básico)")
        ar_un = st.file_uploader("Selecione o PDF", type=["pdf"], accept_multiple_files=False)
        arqs = [ar_un] if ar_un else []
        
    st.write("")
    if arqs and st.button("🚀 Processar Extratos", use_container_width=True):
        if not api_key:
            st.error("Chave de API não configurada.")
        else:
            lista = []
            with st.spinner("Processando..."):
                for a in arqs:
                    try:
                        res = processar_pdf(a, api_key)
                        lista.extend(res)
                    except Exception as err:
                        st.error(f"Erro em {a.name}: {err}")
                if lista:
                    st.session_state["transacoes"].extend(lista)
                    st.success("✨ Processamento concluído com sucesso!")

# ==========================================
# 📊 ABA 2: DASHBOARD & MÉTRICAS
# ==========================================
elif menu_sel == "📊 Dashboard & Mét
