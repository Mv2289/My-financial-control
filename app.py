import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pypdf import PdfReader

st.set_page_config(
    page_title="MFC | My Financial Control",
    page_icon="⚜️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO INSTITUCIONAL XP INVESTIMENTOS (DARK & GOLD MINIMALIST) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #08090b !important;
        background: radial-gradient(circle at 50% 0%, #151821 0%, #08090b 75%) fixed !important;
        color: #e5e5e5 !important;
    }

    /* Barra Lateral */
    section[data-testid="stSidebar"] {
        background-color: #0d0f14 !important;
        border-right: 1px solid rgba(212, 175, 55, 0.12) !important;
    }
    
    /* Tipografia da Marca */
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

    /* Containers Glass */
    .glass-card {
        background: rgba(18, 20, 26, 0.7);
        border: 1px solid rgba(212, 175, 55, 0.15);
        backdrop-filter: blur(12px);
        border-radius: 14px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        margin-bottom: 20px;
    }

    /* KPI Cards */
    .kpi-box {
        background: #0f1117;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: all 0.2s ease;
    }
    .kpi-box:hover {
        border-color: rgba(212, 175, 55, 0.4);
        transform: translateY(-2px);
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

    /* Botões Dourados XP */
    div.stButton > button {
        background: #d4af37 !important;
        color: #08090b !important;
        border: 1px solid #d4af37 !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 14px rgba(212, 175, 55, 0.2) !important;
    }
    div.stButton > button:hover {
        background: #e6c35c !important;
        border-color: #e6c35c !important;
        color: #000000 !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.35) !important;
    }

    /* Abas / Tabs */
    button[data-baseweb="tab"] {
        color: #888888 !important;
        font-weight: 600 !important;
        background-color: transparent !important;
        border-bottom: 2px solid transparent !important;
    }
    button[aria-selected="true"] {
        color: #d4af37 !important;
        border-bottom-color: #d4af37 !important;
    }

    /* Inputs */
    input, textarea, select {
        background-color: #12151c !important;
        color: #ffffff !important;
        border: 1px solid #232733 !important;
        border-radius: 8px !important;
    }
    input:focus {
        border-color: #d4af37 !important;
    }

    /* Badges */
    .pro-tag {
        background: rgba(212, 175, 55, 0.15);
        color: #d4af37;
        border: 1px solid #d4af37;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
        letter-spacing: 1px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÃO DE E-MAIL ---
def enviar_email_boas_vindas(destinatario_email, nome_usuario):
    remetente = st.secrets.get("EMAIL_REMETENTE", "")
    senha_remetente = st.secrets.get("EMAIL_SENHA", "")
    
    if remetente and senha_remetente:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "MFC | Acesso Liberado"
            msg["From"] = f"MFC Intelligence <{remetente}>"
            msg["To"] = destinatario_email
            
            html = f"""
            <div style="background-color:#08090b; color:#e5e5e5; padding:35px; border-radius:12px; border:1px solid #d4af37; font-family:'Inter', Arial, sans-serif;">
                <h1 style="color:#d4af37; margin:0; font-size:26px;">MFC</h1>
                <p style="color:#9e9575; font-size:11px; letter-spacing:3px; margin:0 0 20px 0;">MY FINANCIAL CONTROL</p>
                <p style="font-size:15px; line-height:1.6; color:#ccc;">Olá <b>{nome_usuario}</b>, sua conta foi ativada com sucesso.</p>
                <p style="font-size:14px; color:#999;">Agora você pode automatizar a conciliação dos seus extratos bancários com precisão institucional.</p>
                <br>
                <small style="color:#555;">MFC Intelligence • Plataforma de Gestão Financeira</small>
            </div>
            """
            msg.attach(MIMEText(html, "html"))
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
                servidor.login(remetente, senha_remetente)
                servidor.sendmail(remetente, destinatario_email, msg.as_string())
            return True, "E-mail de confirmação enviado."
        except Exception as e:
            return False, f"Erro no envio do e-mail: {e}"
    return True, "(Configure credenciais no Secrets para disparo real)."

# --- BANCO DE DADOS & SESSÃO ---
if "usuarios_db" not in st.session_state:
    st.session_state["usuarios_db"] = {
        "admin": {"email": "admin@mfc.com", "senha": "admin", "plano": "Pro"},
        "Marcos": {"email": "marcos@mfc.com", "senha": "123", "plano": "Pro"}
    }

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""
if "transacoes" not in st.session_state:
    st.session_state["transacoes"] = []

# --- TELA DE LOGIN INSTITUCIONAL ---
def tela_autenticacao():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
            <div style="text-align: center; margin: 40px 0 25px 0;">
                <div class="brand-title">MFC</div>
                <div class="brand-subtitle">MY FINANCIAL CONTROL</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        aba_login, aba_cadastro = st.tabs(["🔑 Acessar", "✨ Criar Conta"])
        
        with aba_login:
            st.write("")
            usuario = st.text_input("Usuário", key="login_user")
            senha = st.text_input("Senha", type="password", key="login_pass")
            st.write("")
            if st.button("Entrar no Painel", use_container_width=True):
                if usuario in st.session_state["usuarios_db"] and st.session_state["usuarios_db"][usuario]["senha"] == senha:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_logado"] = usuario
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")
                    
        with aba_cadastro:
            st.write("")
            novo_usuario = st.text_input("Nome de Usuário", key="cad_user")
            novo_email = st.text_input("E-mail", placeholder="seu@email.com", key="cad_email")
            nova_senha = st.text_input("Senha", type="password", key="cad_pass")
            confirma_senha = st.text_input("Confirmar Senha", type="password", key="cad_pass_conf")
            st.write("")
            if st.button("Cadastrar", use_container_width=True):
                if not novo_usuario or not novo_email or not nova_senha:
                    st.warning("Preencha todos os campos.")
                elif "@" not in novo_email or "." not in novo_email:
                    st.error("Insira um e-mail válido.")
                elif novo_usuario in st.session_state["usuarios_db"]:
                    st.error("Este nome de usuário já existe.")
                elif nova_senha != confirma_senha:
                    st.error("As senhas não coincidem.")
                else:
                    st.session_state["usuarios_db"][novo_usuario] = {
                        "email": novo_email,
                        "senha": nova_senha,
                        "plano": "Gratuito"
                    }
                    _, msg_email = enviar_email_boas_vindas(novo_email, novo_usuario)
                    st.success(f"Conta registrada com sucesso! {msg_email}")
        
        st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state["autenticado"]:
    tela_autenticacao()
    st.stop()

# --- USUÁRIO E PLANO ---
usuario_atual = st.session_state.get("usuario_logado", "")
dados_usuario = st.session_state["usuarios_db"].get(usuario_atual, {"plano": "Gratuito", "email": ""})
plano_atual = dados_usuario.get("plano", "Gratuito")
eh_pro = (plano_atual == "Pro")
user_email = dados_usuario.get("email", "")

api_key = st.secrets.get("GEMINI_API_KEY", "")

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("""
        <div style="padding: 10px 0 20px 0; text-align: center;">
            <div class="brand-title" style="font-size: 2.2rem;">MFC</div>
            <div class="brand-subtitle" style="font-size: 0.65rem;">MY FINANCIAL CONTROL</div>
        </div>
    """, unsafe_allow_html=True)
    
    badge_html = '<span class="pro-tag">⭐ PLANO PRO</span>' if eh_pro else '<span style="background:#1a1c24; color:#777; font-size:0.72rem; padding:3px 8px; border-radius:4px;">PLANO BÁSICO</span>'
    
    st.markdown(f"""
        <div style="background: #11131a; padding: 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 20px;">
            <div style="font-size: 0.72rem; color: #777; text-transform: uppercase;">Usuário</div>
            <div style="font-weight: 700; font-size: 1.05rem; color: #ffffff;">{usuario_atual}</div>
            <div style="font-size: 0.75rem; color: #a89f81; margin: 2px 0 10px 0;">{user_email}</div>
            {badge_html}
        </div>
    """, unsafe_allow_html=True)
    
    menu_selecionado = st.radio(
        "Menu",
        ["📥 Upload de Extratos", "📊 Dashboard & Métricas", "🔮 Planejamento Futuro", "⭐ Assinatura PRO"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    if usuario_atual == "admin":
        with st.expander("🛡️ Gestão de Usuários (Admin)"):
            for u, dados in list(st.session_state["usuarios_db"].items()):
                st.write(f"**{u}** ({dados['plano']})")
                c_a1, c_a2 = st.columns(2)
                if dados["plano"] == "Gratuito":
                    if c_a1.button("Virar Pro", key=f"ad_pro_{u}"):
                        st.session_state["usuarios_db"][u]["plano"] = "Pro"
                        st.rerun()
                else:
                    if u != "admin" and c_a2.button("Downgrade", key=f"ad_down_{u}"):
                        st.session_state["usuarios_db"][u]["plano"] = "Gratuito"
                        st.rerun()
        st.markdown("---")
        
    if not api_key:
        with st.expander("⚙️ Gemini API Key"):
            api_key = st.text_input("Chave de API", type="password")

    if st.session_state["transacoes"]:
        if st.button("🗑️ Limpar Dados Atuais", use_container_width=True):
            st.session_state["transacoes"] = []
            st.rerun()

    if st.button("🚪 Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.rerun()

# --- MOTOR DE LEITURA IA GEMINI ---
def processar_extrato_pdf(file, chave_api):
    reader = PdfReader(file)
    texto_extrato = ""
    for page in reader.pages:
        texto_extrato += page.extract_text() or ""
        
    if not texto_extrato.strip():
        raise Exception("Não foi possível extrair texto do PDF. O arquivo pode estar protegido ou ser imagem escaneada.")

    genai.configure(api_key=chave_api)
    
    modelos_disponiveis = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelos_disponiveis.append(m.name)
    except Exception:
        pass
    
    preferencias = [
        "models/gemini-2.5-flash",
        "models/gemini-2.0-flash",
        "models/gemini-flash-latest",
        "models/gemini-1.5-flash",
        "models/gemini-pro"
    ]
    candidatos = [m for m in preferencias if m in modelos_disponiveis] or modelos_disponiveis or ["gemini-2.5-flash"]

    prompt = f"""
    Você é o motor de conciliação financeira do MFC (My Financial Control). Analise o extrato abaixo e extraia rigorosamente todas as movimentações.
    Retorne EXCLUSIVAMENTE um array JSON contendo objetos no formato:
    - "data": string (DD/MM/AAAA)
    - "descricao": string (nome claro da transação, pessoa, banco ou comércio)
    - "tipo": string ("Receita" ou "Despesa")
    - "valor": float (valor numérico positivo com ponto, ex: 150.50)

    EXTRATO:
    {texto_extrato}
    """
    
    response = None
    ultimo_erro = None
    for modelo in candidatos:
        try:
            m = genai.GenerativeModel(model_name=modelo, generation_config={"response_mime_type": "application/json"})
            response = m.generate_content(prompt)
            if response and response.text:
                break
        except Exception as e:
            ultimo_erro = e
            continue
            
    if not response:
        raise ultimo_erro
        
    res_text = response.text.strip()
    if res_text.startswith("```json"):
        res_text = res_text[7:]
    if res_text.startswith("```"):
        res_text = res_text[3:]
    if res_text.endswith("```"):
        res_text = res_text[:-3]
    return json.loads(res_text.strip())

# ==========================================
# 📥 ABA 1: UPLOAD DE EXTRATOS
# ==========================================
if menu_selecionado == "📥 Upload de Extratos":
    st.markdown("""
        <div class="glass-card">
            <h2 style="margin:0; color:#d4af37;">📥 Importação de Extratos Bancários</h2>
            <p style="color:#aaa; font-size:0.95rem; margin-top:6px;">
                Carregue seus extratos em PDF (PicPay, Nubank, Itaú, Bradesco, etc.) para extração automática.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    if eh_pro:
        st.markdown("##### 🌟 Upload Multi-Arquivos (PRO)")
        arquivos = st.file_uploader("Selecione um ou vários PDFs", type=["pdf"], accept_multiple_files=True)
    else:
        st.markdown("##### 📄 Upload Individual (Plano Básico)")
        arquivo_unico = st.file_uploader("Selecione o extrato em PDF", type=["pdf"], accept_multiple_files=False)
        arquivos = [arquivo_unico] if arquivo_unico else []
        
    st.write("")
    if arquivos and st.button("🚀 Processar Extratos com Inteligência Artificial", use_container_width=True):
        if not api_key:
            st.error("Chave de API não configurada. Adicione
