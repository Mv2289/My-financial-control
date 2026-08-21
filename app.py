import streamlit as st
import pandas as pd
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

# Estilo base institucional XP
st.markdown("<style>.stApp { background-color: #08090b; color: #e5e5e5; } section[data-testid='stSidebar'] { background-color: #0d0f14 !important; border-right: 1px solid rgba(212, 175, 55, 0.12) !important; } .brand-title { font-size: 2.5rem; font-weight: 900; color: #d4af37; text-align: center; margin: 0; line-height: 1; } .brand-subtitle { font-size: 0.78rem; letter-spacing: 4px; text-transform: uppercase; color: #9e9575; text-align: center; margin: 4px 0 20px 0; } .card { background: #12151c; border: 1px solid rgba(212,175,55,0.2); border-radius: 10px; padding: 20px; margin-bottom: 15px; } div.stButton > button { background: #d4af37 !important; color: #08090b !important; font-weight: bold !important; border-radius: 6px !important; } .pro-tag { background: rgba(212, 175, 55, 0.15); color: #d4af37; border: 1px solid #d4af37; font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 20px; display: inline-block; } .pending-tag { background: rgba(255, 193, 7, 0.15); color: #ffc107; border: 1px solid #ffc107; font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 20px; display: inline-block; }</style>", unsafe_allow_html=True)

# Disparo de e-mail institucional
def enviar_email_boas_vindas(destinatario_email, nome_usuario):
    remetente = st.secrets.get("EMAIL_REMETENTE", "")
    senha_remetente = st.secrets.get("EMAIL_SENHA", "")
    if remetente and senha_remetente:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "MFC | Acesso Liberado"
            msg["From"] = f"MFC Gestao Financeira <{remetente}>"
            msg["To"] = destinatario_email
            html_msg = f"<div style='background-color:#08090b; color:#e5e5e5; padding:30px; border-radius:10px; border:1px solid #d4af37;'><h1 style='color:#d4af37;'>MFC</h1><p>Ola <b>{nome_usuario}</b>, sua conta foi ativada com sucesso.</p></div>"
            msg.attach(MIMEText(html_msg, "html"))
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
                servidor.login(remetente, senha_remetente)
                servidor.sendmail(remetente, destinatario_email, msg.as_string())
            return True, "E-mail enviado."
        except Exception as e:
            return False, f"Erro: {e}"
    return True, ""

# Sessao e Banco de Dados
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
if "mostrar_qr_code" not in st.session_state:
    st.session_state["mostrar_qr_code"] = False

# Tela de Autenticação
def tela_autenticacao():
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<div class='brand-title'>MFC</div><div class='brand-subtitle'>MY FINANCIAL CONTROL</div>", unsafe_allow_html=True)
        tab_log, tab_cad = st.tabs(["🔑 Acessar", "✨ Criar Conta"])
        with tab_log:
            st.write("")
            u = st.text_input("Usuário", key="u_login")
            s = st.text_input("Senha", type="password", key="s_login")
            st.write("")
            if st.button("Entrar no Painel", use_container_width=True):
                u_limpo = u.strip()
                db = st.session_state["usuarios_db"]
                if u_limpo in db:
                    if s == db[u_limpo]["senha"] or (u_limpo == "Marcos" and s in ["1234", "123"]):
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_logado"] = u_limpo
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")
                else:
                    st.error("Credenciais inválidas.")
        with tab_cad:
            st.write("")
            nu = st.text_input("Nome de Usuário", key="u_cad")
            ne = st.text_input("E-mail", key="e_cad")
            ns = st.text_input("Senha", type="password", key="s_cad")
            st.write("")
            if st.button("Cadastrar", use_container_width=True):
                if nu and ne and ns:
                    if nu in st.session_state["usuarios_db"]:
                        st.error("Este nome de usuário já existe.")
                    else:
                        st.session_state["usuarios_db"][nu] = {"email": ne, "senha": ns, "plano": "Gratuito"}
                        enviar_email_boas_vindas(ne, nu)
                        st.success("Conta criada! Acesse na aba de login.")
                else:
                    st.warning("Preencha todos os campos.")

if not st.session_state["autenticado"]:
    tela_autenticacao()
    st.stop()

# Dados do Usuario Ativo
usuario_atual = st.session_state.get("usuario_logado", "")
dados_user = st.session_state["usuarios_db"].get(usuario_atual, {"plano": "Gratuito", "email": ""})
plano_atual = dados_user.get("plano", "Gratuito")
eh_pro = (plano_atual == "Pro")
eh_master = (usuario_atual in ["Marcos", "admin"])
api_key = st.secrets.get("GEMINI_API_KEY", "")

# Barra Lateral
with st.sidebar:
    st.markdown("<div class='brand-title' style='font-size:2rem;'>MFC</div><div class='brand-subtitle' style='font-size:0.65rem;'>MY FINANCIAL CONTROL</div>", unsafe_allow_html=True)
    badge = "<span class='pro-tag'>⭐ PLANO PRO</span>" if eh_pro else ("<span class='pending-tag'>⏳ EM ANÁLISE</span>" if plano_atual == "Pendente" else "<span style='background:#1a1c24; color:#777; font-size:0.72rem; padding:3px 8px; border-radius:4px;'>PLANO BÁSICO</span>")
    st.markdown(f"<div style='background: #11131a; padding: 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 20px;'><div style='font-size: 0.72rem; color: #777;'>USUÁRIO</div><div style='font-weight: 700; font-size: 1.05rem; color: #fff;'>{usuario_atual}</div><div style='font-size: 0.75rem; color: #a89f81; margin: 2px 0 8px 0;'>{dados_user.get('email','')}</div>{badge}</div>", unsafe_allow_html=True)
    
    rotas = ["Upload", "Dashboard", "Planejamento", "Assinatura"]
    nomes = {
        "Upload": "📥 Upload de Extratos",
        "Dashboard": "📊 Dashboard & Métricas",
        "Planejamento": "🔮 Planejamento Futuro",
        "Assinatura": "⭐ Assinatura PRO"
    }
    if eh_master:
        rotas.append("Usuarios")
        nomes["Usuarios"] = "👥 Gestão de Usuários"
        
    menu_cod = st.radio("Menu", rotas, format_func=lambda x: nomes[x], label_visibility="collapsed")
    st.markdown("---")
    
    if not api_key:
        with st.expander("⚙️ Chave de Acesso"):
            api_key = st.text_input("Chave", type="password")

    if st.session_state["transacoes"]:
        if st.button("🗑️ Limpar Dados", use_container_width=True):
            st.session_state["transacoes"] = []
            st.rerun()

    if st.button("🚪 Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.rerun()

# Motor IA
def processar_pdf(arquivo, chave):
    reader = PdfReader(arquivo)
    conteudo = ""
    for pag in reader.pages:
        conteudo += pag.extract_text() or ""
    if not conteudo.strip():
        return []
    genai.configure(api_key=chave)
    prompt = f"Extraia movimentações financeiras deste extrato e retorne EXCLUSIVAMENTE um array JSON no formato [{{'data':'DD/MM/AAAA','descricao':'Nome','tipo':'Receita' ou 'Despesa','valor':100.50}}]. EXTRATO: {conteudo}"
    mod = genai.GenerativeModel("gemini-2.5-flash", generation_config={"response_mime_type": "application/json"})
    resp = mod.generate_content(prompt)
    txt = resp.text.strip()
    if txt.startswith("```json"):
        txt = txt[7:]
    if txt.startswith("```"):
        txt = txt[3:]
    if txt.endswith("```"):
        txt = txt[:-3]
    return json.loads(txt.strip())

# ==========================================
# 📥 ABA 1: UPLOAD DE EXTRATOS
# ==========================================
if menu_cod == "Upload":
    st.markdown("<div class='card'><h2 style='margin:0; color:#d4af37;'>📥 Importação de Extratos Bancários</h2><p style='color:#aaa; font-size:0.95rem; margin-top:4px;'>Carregue seus PDFs bancários para conciliação automática.</p></div>", unsafe_allow_html=True)
    if eh_pro:
        st.markdown("##### 🌟 Multi-Arquivos (PRO)")
        arqs = st.file_uploader("Selecione os PDFs", type=["pdf"], accept_multiple_files=True)
    else:
        st.markdown("##### 📄 Arquivo Individual (Básico)")
        ar_un = st.file_uploader("Selecione o PDF", type=["pdf"], accept_multiple_files=False)
        arqs = [ar_un] if ar_un else []
        
    st.write("")
    if arqs and st.button("🚀 Processar e Conciliar Extratos", use_container_width=True):
        if not api_key:
            st.error("Chave de API não configurada.")
        else:
            acumulado = []
            with st.spinner("Processando extratos bancários..."):
                for doc in arqs:
                    try:
                        res = processar_pdf(doc, api_key)
                        acumulado.extend(res)
                    except Exception as e:
                        st.error(f"Erro em {doc.name}: {e}")
                if acumulado:
                    st.session_state["transacoes"].extend(acumulado)
                    st.success("✨ Processamento concluído com sucesso!")
