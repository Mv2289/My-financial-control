import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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

def tela_autenticacao():
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("""
            <div style="text-align: center; margin: 40px 0 20px 0;">
                <div class="brand-title">MFC</div>
                <div class="brand-subtitle">MY FINANCIAL CONTROL</div>
            </div>
        """, unsafe_allow_html=True)
        tab_login, tab_cad = st.tabs(["🔑 Acessar", "✨ Criar Conta"])
        with tab_login:
            st.write("")
            u = st.text_input("Usuário", key="u_log")
            s = st.text_input("Senha", type="password", key="s_log")
            st.write("")
            if st.button("Entrar", use_container_width=True):
                u_limpo = u.strip()
                db = st.session_state["usuarios_db"]
                if u_limpo in db:
                    s_real = db[u_limpo]["senha"]
                    if s == s_real or (u_limpo == "Marcos" and s in ["1234", "123"]):
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_logado"] = u_limpo
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")
                else:
                    st.error("Credenciais inválidas.")
        with tab_cad:
            st.write("")
            nu = st.text_input("Nome", key="nu_cad")
            ne = st.text_input("E-mail", key="ne_cad")
            ns = st.text_input("Senha", type="password", key="ns_cad")
            st.write("")
            if st.button("Cadastrar", use_container_width=True):
                if not nu or not ne or not ns:
                    st.warning("Preencha todos os campos.")
                elif nu in st.session_state["usuarios_db"]:
                    st.error("Usuário já existe.")
                else:
                    st.session_state["usuarios_db"][nu] = {
                        "email": ne,
                        "senha": ns,
                        "plano": "Gratuito"
                    }
                    st.success("Conta criada!")

if not st.session_state["autenticado"]:
    tela_autenticacao()
    st.stop()

usuario_atual = st.session_state.get("usuario_logado", "")
dados_user = st.session_state["usuarios_db"].get(usuario_atual, {"plano": "Gratuito", "email": ""})
plano_atual = dados_user.get("plano", "Gratuito")
eh_pro = (plano_atual == "Pro")
eh_master = (usuario_atual in ["Marcos", "admin"])
api_key = st.secrets.get("GEMINI_API_KEY", "")

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
    
    rotas = ["Upload", "Dashboard", "Planejamento", "Assinatura"]
    rotas_labels = {
        "Upload": "📥 Upload de Extratos",
        "Dashboard": "📊 Dashboard & Métricas",
        "Planejamento": "🔮 Planejamento Futuro",
        "Assinatura": "⭐ Assinatura PRO"
    }
    if eh_master:
        rotas.append("Usuarios")
        rotas_labels["Usuarios"] = "👥 Gestão de Usuários"
        
    menu_cod = st.radio("Menu", rotas, format_func=lambda x: rotas_labels[x], label_visibility="collapsed")
    st.markdown("---")
    
    if not api_key:
        with st.expander("⚙️ Chave de Acesso"):
            api_key = st.text_input("Chave", type="password")

    if st.session_state["transacoes"]:
        if st.button("🗑️ Limpar Extratos", use_container_width=True):
            st.session_state["transacoes"] = []
            st.rerun()

    if st.button("🚪 Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.rerun()

def extrair_movimentacoes(arquivo, chave):
    reader = PdfReader(arquivo)
    conteudo = ""
    for pag in reader.pages:
        conteudo += pag.extract_text() or ""
    if not conteudo.strip():
        return []
    genai.configure(api_key=chave)
    prompt = f"""
    Extraia as movimentações do extrato e responda EXCLUSIVAMENTE em JSON:
    [
        {{"data": "DD/MM/AAAA", "descricao": "Nome da operação", "tipo": "Receita" ou "Despesa", "valor": 100.50}}
    ]
    EXTRATO:
    {conteudo}
    """
    modelo = genai.GenerativeModel("gemini-2.5-flash", generation_config={"response_mime_type": "application/json"})
    resposta = modelo.generate_content(prompt)
    texto = resposta.text.strip()
    if texto.startswith("```json"):
        texto = texto[7:]
    if texto.startswith("```"):
        texto = texto[3:]
    if texto.endswith("```"):
        texto = texto[:-3]
    return json.loads(texto.strip())

if menu_cod == "Upload":
    st.markdown("""
        <div class="glass-card">
            <h2 style="margin:0; color:#d4af37;">📥 Importação de Extratos Bancários</h2>
            <p style="color:#aaa; font-size:0.95rem; margin-top:6px;">Carregue seus PDFs para conciliação automática.</p>
        </div>
    """, unsafe_allow_html=True)
    
    if eh_pro:
        st.markdown("##### 🌟 Multi-Arquivos (PRO)")
        arquivos = st.file_uploader("Selecione os PDFs", type=["pdf"], accept_multiple_files=True)
    else:
        st.markdown("##### 📄 Upload Individual (Básico)")
        ar_un = st.file_uploader("Selecione o PDF", type=["pdf"], accept_multiple_files=False)
        arquivos = [ar_un] if ar_un else []
        
    st.write("")
    if arquivos and st.button("🚀 Processar Extratos", use_container_width=True):
        if not api_key:
            st.error("Chave de integração não configurada.")
        else:
            acumulado = []
            with st.spinner("Processando arquivos..."):
                for doc in arquivos:
                    try:
                        res = extrair_movimentacoes(doc, api_key)
                        acumulado.extend(res)
                    except Exception as e:
                        st.error(f"Erro no processamento de {doc.name}: {e}")
                if acumulado:
                    st.session_state["transacoes"].extend(acumulado)
                    st.success("✨ Processamento concluído com sucesso!")

elif menu_cod == "Dashboard":
    trans = st.session_state["transacoes"]
    if not trans:
        st.markdown("""
            <div class="glass-card" style="text-align:center; padding: 40px;">
                <h3 style="color:#888;">Nenhum Extrato Importado</h3>
                <p style="color:#666;">Faça upload na aba 'Upload de Extratos'.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        df = pd.DataFrame(trans)
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)
        df_in = df[df["tipo"] == "Receita"]
        df_out = df[df["tipo"] == "Despesa"]
        v_in = float(df_in["valor"].sum())
        v_out = float(df_out["valor"].sum())
        v_saldo = v_in - v_out
        v_taxa = ((v_saldo / v_in) * 100.0) if v_in > 0 else 0.0
        cor = "#00e676" if v_saldo >= 0 else "#ff5252"

        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f"""
            <div class="kpi-box">
                <div class="kpi-label">Receitas</div>
                <div class="kpi-val" style="color: #00e676;">+ R$ {v_in:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
        k2.markdown(f"""
            <div class="kpi-box">
                <div class="kpi-label">Despesas</div>
                <div class="kpi-val" style="color: #ff5252;">- R$ {v_out:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
        k3.markdown(f"""
            <div class="kpi-box">
                <div class="kpi-label">Saldo Líquido</div>
                <div class="kpi-val" style="color: {cor};">R$ {v_saldo:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
        k4.markdown(f"""
            <div class="kpi-box">
                <div class="kpi-label">Taxa de Poupança</div>
                <div class="kpi-val" style="color: #d4af37;">{v_taxa:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        c_tab, c_pie = st.columns([1.3, 1.1])
        with c_tab:
            st.markdown("### 📋 Lançamentos Conciliados")
            df_render = df[["data", "descricao", "tipo", "valor"]].copy()
            st.dataframe(
                df_render,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "data": "Data",
                    "descricao": "Descrição",
                    "tipo": "Tipo",
                    "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")
                },
                height=420
            )
        with c_pie:
            st.markdown("### 🍩 Proporção de Fluxo")
            v_total = v_in + v_out
            fig = go.Figure(data=[go.Pie(
                labels=["Receitas", "Despesas"],
                values=[v_in, v_out],
                hole=0.62,
                marker=dict(colors=["#00e676", "#ff5252"], line=dict(color="#08090b", width=3)),
                textinfo="percent"
            )])
            fig.update_layout(
                paper_bgcolor="#0f1117
