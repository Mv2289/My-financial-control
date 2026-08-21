import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import urllib.parse
from pypdf import PdfReader

st.set_page_config(
    page_title="MFC | My Financial Control",
    page_icon="⚜️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo base
st.markdown("""
<style>
    .stApp { background-color: #08090b; color: #e5e5e5; }
    .brand-title { font-size: 2.5rem; font-weight: 900; color: #d4af37; text-align: center; }
    .brand-sub { font-size: 0.8rem; color: #9e9575; letter-spacing: 3px; text-align: center; margin-bottom: 20px; }
    .card { background: #12151c; border: 1px solid rgba(212,175,55,0.2); border-radius: 10px; padding: 20px; margin-bottom: 15px; }
    .kpi-title { font-size: 0.8rem; color: #a89f81; font-weight: bold; text-transform: uppercase; }
    .kpi-num { font-size: 1.6rem; font-weight: 800; }
    div.stButton > button { background: #d4af37 !important; color: #08090b !important; font-weight: bold !important; border-radius: 6px !important; }
</style>
""", unsafe_allow_html=True)

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

def tela_login():
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown('<div class="brand-title">MFC</div><div class="brand-sub">MY FINANCIAL CONTROL</div>', unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Entrar", "Cadastrar"])
        with tab1:
            u = st.text_input("Usuário", key="login_u")
            s = st.text_input("Senha", type="password", key="login_s")
            if st.button("Acessar Painel", use_container_width=True):
                u_limpo = u.strip()
                db = st.session_state["usuarios_db"]
                if u_limpo in db:
                    if s == db[u_limpo]["senha"] or (u_limpo == "Marcos" and s in ["1234", "123"]):
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_logado"] = u_limpo
                        st.rerun()
                    else:
                        st.error("Senha incorreta.")
                else:
                    st.error("Usuário não encontrado.")
        with tab2:
            nu = st.text_input("Nome", key="cad_u")
            ne = st.text_input("E-mail", key="cad_e")
            ns = st.text_input("Senha", type="password", key="cad_s")
            if st.button("Criar Conta", use_container_width=True):
                if nu and ne and ns:
                    if nu in st.session_state["usuarios_db"]:
                        st.error("Usuário já existe.")
                    else:
                        st.session_state["usuarios_db"][nu] = {"email": ne, "senha": ns, "plano": "Gratuito"}
                        st.success("Conta criada! Acesse na aba Entrar.")
                else:
                    st.warning("Preencha todos os campos.")

if not st.session_state["autenticado"]:
    tela_login()
    st.stop()

user_atual = st.session_state["usuario_logado"]
user_info = st.session_state["usuarios_db"].get(user_atual, {"plano": "Gratuito", "email": ""})
eh_pro = (user_info.get("plano") == "Pro")
eh_master = (user_atual in ["Marcos", "admin"])
api_key = st.secrets.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.markdown('<div class="brand-title" style="font-size:2rem;">MFC</div><div class="brand-sub">PAINEL</div>', unsafe_allow_html=True)
    tag_plano = "⭐ PRO" if eh_pro else ("⏳ PENDENTE" if user_info.get("plano") == "Pendente" else "BÁSICO")
    st.info(f"**{user_atual}**\nPlano: {tag_plano}")
    
    opcoes = ["Upload", "Dashboard", "Planejamento", "Assinatura"]
    nomes = {
        "Upload": "📥 Upload de Extratos",
        "Dashboard": "📊 Dashboard & Métricas",
        "Planejamento": "🔮 Planejamento",
        "Assinatura": "⭐ Assinatura PRO"
    }
    if eh_master:
        opcoes.append("Usuarios")
        nomes["Usuarios"] = "👥 Gestão de Usuários"
        
    menu = st.radio("Navegação", opcoes, format_func=lambda x: nomes[x], label_visibility="collapsed")
    st.markdown("---")
    
    if not api_key:
        with st.expander("Chave de Acesso"):
            api_key = st.text_input("API Key", type="password")

    if st.session_state["transacoes"]:
        if st.button("Limpar Extratos", use_container_width=True):
            st.session_state["transacoes"] = []
            st.rerun()

    if st.button("Sair da Conta", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.rerun()

def extrair_dados_pdf(arquivo, chave):
    reader = PdfReader(arquivo)
    conteudo = ""
    for pag in reader.pages:
        conteudo += pag.extract_text() or ""
    if not conteudo.strip():
        return []
    genai.configure(api_key=chave)
    prompt = f"Extraia transações em JSON: [{{\"data\":\"DD/MM/AAAA\",\"descricao\":\"Nome\",\"tipo\":\"Receita\" ou \"Despesa\",\"valor\":100.0}}]. EXTRATO: {conteudo}"
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

if menu == "Upload":
    st.subheader("📥 Upload de Extratos Bancários")
    if eh_pro:
        arqs = st.file_uploader("Selecione os PDFs (Multi-upload PRO)", type=["pdf"], accept_multiple_files=True)
    else:
        ar_un = st.file_uploader("Selecione o PDF (Plano Básico)", type=["pdf"], accept_multiple_files=False)
        arqs = [ar_un] if ar_un else []
        
    if arqs and st.button("Processar Extratos", use_container_width=True):
        if not api_key:
            st.error("Configure sua API Key nos Secrets do Streamlit.")
        else:
            acumulado = []
            with st.spinner("Processando..."):
                for doc in arqs:
                    try:
                        res = extrair_dados_pdf(doc, api_key)
                        acumulado.extend(res)
                    except Exception as e:
                        st.error(f"Erro em {doc.name}: {e}")
                if acumulado:
                    st.session_state["transacoes"].extend(acumulado)
                    st.success("Extratos conciliados com sucesso!")

elif menu == "Dashboard":
    dados = st.session_state["transacoes"]
    if not dados:
        st.info("Nenhum dado importado ainda. Vá na aba de Upload.")
    else:
        df = pd.DataFrame(dados)
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)
        
        rec = float(df[df["tipo"] == "Receita"]["valor"].sum())
        des = float(df[df["tipo"] == "Despesa"]["valor"].sum())
        saldo = rec - des
        taxa = ((saldo / rec) * 100.0) if rec > 0 else 0.0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Receitas", f"R$ {rec:,.2f}")
        c2.metric("Despesas", f"R$ {des:,.2f}")
        c3.metric("Saldo", f"R$ {saldo:,.2f}")
        c4.metric("Poupança", f"{taxa:.1f}%")
        
        st.write("")
        st.subheader("📋 Lançamentos")
        st.dataframe(
            df[["data", "descricao", "tipo", "valor"]],
            use_container_width=True,
            hide_index=True,
            column_config={"valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")}
        )
        
        st.subheader("📊 Comparativo de Fluxo")
        chart_data = pd.DataFrame({"Volume": [rec, des]}, index=["Receitas", "Despesas"])
        st.bar_chart(chart_data)

elif menu == "Planejamento":
    if not eh_pro:
        st.warning("Recurso exclusivo do Plano PRO. Acesse a aba Assinatura para desbloquear.")
    else:
        st.subheader("🔮 Planejamento Orçamentário")
        col1, col2 = st.columns
