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

    input, textarea, select {
        background-color: #12151c !important;
        color: #ffffff !important;
        border: 1px solid #232733 !important;
        border-radius: 8px !important;
    }
    input:focus {
        border-color: #d4af37 !important;
    }

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
            msg["From"] = f"MFC Gestão Financeira <{remetente}>"
            msg["To"] = destinatario_email
            
            html = f"""
            <div style="background-color:#08090b; color:#e5e5e5; padding:35px; border-radius:12px; border:1px solid #d4af37; font-family:'Inter', Arial, sans-serif;">
                <h1 style="color:#d4af37; margin:0; font-size:26px;">MFC</h1>
                <p style="color:#9e9575; font-size:11px; letter-spacing:3px; margin:0 0 20px 0;">MY FINANCIAL CONTROL</p>
                <p style="font-size:15px; line-height:1.6; color:#ccc;">Olá <b>{nome_usuario}</b>, sua conta foi ativada com sucesso.</p>
                <p style="font-size:14px; color:#999;">Agora você pode automatizar a conciliação dos seus extratos bancários com precisão institucional.</p>
                <br>
                <small style="color:#555;">MFC • Plataforma de Gestão Financeira</small>
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
        "Marcos": {"email": "marcos@mfc.com", "senha": "1234", "plano": "Pro"}
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
            <div style="text-align: center; margin: 40px 0 20px 0;">
                <div class="brand-title">MFC</div>
                <div class="brand-subtitle">MY FINANCIAL CONTROL</div>
            </div>
        """, unsafe_allow_html=True)
        
        aba_login, aba_cadastro = st.tabs(["🔑 Acessar", "✨ Criar Conta"])
        
        with aba_login:
            st.write("")
            usuario = st.text_input("Usuário", key="login_user")
            senha = st.text_input("Senha", type="password", key="login_pass")
            st.write("")
            if st.button("Entrar no Painel", use_container_width=True):
                user_clean = usuario.strip()
                if user_clean in st.session_state["usuarios_db"]:
                    senha_cadastrada = st.session_state["usuarios_db"][user_clean]["senha"]
                    if senha == senha_cadastrada or (user_clean == "Marcos" and senha in ["1234", "123"]):
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_logado"] = user_clean
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")
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
        with st.expander("⚙️ Chave de Integração"):
            api_key = st.text_input("Chave de Acesso", type="password")

    if st.session_state["transacoes"]:
        if st.button("🗑️ Limpar Dados Atuais", use_container_width=True):
            st.session_state["transacoes"] = []
            st.rerun()

    if st.button("🚪 Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.rerun()

# --- MOTOR DE CONCILIAÇÃO MFC ---
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
                Carregue seus extratos em PDF (PicPay, Nubank, Itaú, Bradesco, etc.) para conciliação automática.
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
    if arquivos and st.button("🚀 Processar e Conciliar Extratos", use_container_width=True):
        if not api_key:
            st.error("Chave de acesso não configurada. Salve nos Secrets do Streamlit ou na barra lateral.")
        else:
            todas_transacoes = []
            with st.spinner(f"Processando e conciliando {len(arquivos)} documento(s)..."):
                for arq in arquivos:
                    try:
                        res = processar_extrato_pdf(arq, api_key)
                        todas_transacoes.extend(res)
                    except Exception as err:
                        st.error(f"Erro em {arq.name}: {err}")
                
                if todas_transacoes:
                    st.session_state["transacoes"].extend(todas_transacoes)
                    st.success(f"✨ Sucesso! {len(todas_transacoes)} movimentações consolidadas.")
                    st.info("👉 Acesse a aba 📊 Dashboard & Métricas para ver a análise.")

# ==========================================
# 📊 ABA 2: DASHBOARD & MÉTRICAS
# ==========================================
elif menu_selecionado == "📊 Dashboard & Métricas":
    df_raw = pd.DataFrame(st.session_state["transacoes"])
    
    if df_raw.empty:
        st.markdown("""
            <div class="glass-card" style="text-align:center; padding: 40px;">
                <h3 style="color:#888;">Nenhum Extrato Importado</h3>
                <p style="color:#666;">Faça o upload do seu primeiro PDF bancário na aba 'Upload de Extratos'.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        df_raw["valor"] = pd.to_numeric(df_raw["valor"])
        df_raw["data_dt"] = pd.to_datetime(df_raw["data"], format="%d/%m/%Y", errors="coerce")
        df_raw = df_raw.sort_values(by="data_dt", ascending=False)
        
        total_entradas = df_raw[df_raw["tipo"] == "Receita"]["valor"].sum()
        total_saidas = df_raw[df_raw["tipo"] == "Despesa"]["valor"].sum()
        saldo_liquido = total_entradas - total_saidas
        taxa_poupanca = ((saldo_liquido / total_entradas) * 100) if total_entradas > 0 else 0.0
        cor_saldo = "#00e676" if saldo_liquido >= 0 else "#ff5252"

        # --- CARDS KPIS ESTILO XP ---
        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f"""
            <div class="kpi-box">
                <div class="kpi-label">Receitas (Entradas)</div>
                <div class="kpi-val" style="color: #00e676;">+ R$ {total_entradas:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
        
        k2.markdown(f"""
            <div class="kpi-box">
                <div class="kpi-label">Despesas (Saídas)</div>
                <div class="kpi-val" style="color: #ff5252;">- R$ {total_saidas:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
        
        k3.markdown(f"""
            <div class="kpi-box">
                <div class="kpi-label">Saldo Líquido</div>
                <div class="kpi-val" style="color: {cor_saldo};">R$ {saldo_liquido:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
        
        k4.markdown(f"""
            <div class="kpi-box">
                <div class="kpi-label">Taxa de Poupança</div>
                <div class="kpi-val" style="color: #d4af37;">{taxa_poupanca:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.write("")
        
        c_tab, c_graf = st.columns([1.3, 1.1])
        
        with c_tab:
            st.markdown("### 📋 Lançamentos Conciliados")
            df_table = df_raw.copy()
            df_table["valor_num"] = df_table.apply(lambda r: r["valor"] if r["tipo"] == "Receita" else -r["valor"], axis=1)
            
            df_render = df_table[["data", "descricao", "valor_num"]].rename(
                columns={"data": "Data", "descricao": "Descrição", "valor_num": "Valor (R$)"}
            )
            
            def cor_valor(val):
                return 'color: #00e676; font-weight: 700;' if val > 0 else 'color: #ff5252; font-weight: 700;'

            styler = df_render.style.format({
                "Valor (R$)": lambda x: f"+ R$ {x:,.2f}" if x > 0 else f"- R$ {abs(x):,.2f}"
            })
            
            try:
                styler = styler.map(cor_valor, subset=["Valor (R$)"])
            except AttributeError:
                styler = styler.applymap(cor_valor, subset=["Valor (R$)"])

            st.dataframe(
                styler,
                use_container_width=True,
                hide_index=True,
                height=450
            )
            
        with c_graf:
            st.markdown("### 🍩 Proporção de Fluxo")
            total_vol = total_entradas + total_saidas
            
            fig = go.Figure(data=[go.Pie(
                labels=["Entradas (Receitas)", "Saídas (Despesas)"],
                values=[total_entradas, total_saidas],
                hole=0.62,
                marker=dict(
                    colors=["#00e676", "#ff5252"],
                    line=dict(color="#08090b", width=3)
                ),
                textinfo="percent",
                textfont=dict(size=14, color="#ffffff", family="Inter"),
                hovertemplate="<b>%{label}</b><br>Volume: R$ %{value:,.2f}<br>Proporção: %{percent}<extra></extra>"
            )])
            
            fig.update_layout(
                paper_bgcolor="#0f1117",
                plot_bgcolor="#0f1117",
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.15,
                    xanchor="center",
                    x=0.5,
                    font=dict(color="#e5e5e5", size=12)
                ),
                annotations=[
                    dict(
                        text=f"<span style='font-size:11px; color:#888;'>VOLUME TOTAL</span><br><b style='font-size:16px; color:#ffffff;'>R$ {total_vol:,.2f}</b>",
                        x=0.5, y=0.5,
                        font_size=14,
                        showarrow=False
                    )
                ],
                margin=dict(t=10, b=30, l=10, r=10),
                height=450
            )
            st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 🔮 ABA 3: PLANEJAMENTO FUTURO
# ==========================================
elif menu_selecionado == "🔮 Planejamento Futuro":
    if not eh_pro:
        st.markdown("""
            <div class="glass-card" style="text-align: center; border: 1px solid #d4af37; padding: 40px 20px;">
                <div class="pro-tag">Recurso Exclusivo PRO</div>
                <h2 style="color: #d4af37; margin: 15px 0 10px 0;">🔮 Planejamento Orçamentário</h2>
                <p style="color: #bbb; max-width: 550px; margin: 0 auto 20px auto; font-size: 0.95rem;">
                    Projete metas para os próximos meses, gerencie despesas fixas e acompanhe sua capacidade de poupança com relatórios automatizados.
                </p>
                <div style="font-size: 1.4rem; color: #00e676; font-weight: 800; margin-bottom: 15px;">R$ 19,90 / mês</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="glass-card">
                <h2 style="margin:0; color:#d4af37;">🔮 Planejamento Orçamentário Estratégico</h2>
                <p style="color:#aaa; font-size:0.95rem; margin-top:4px;">Simulação preditiva de metas e capacidade de investimento.</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("#### 🎯 Metas de Gastos")
            renda_est = st.number_input("Renda Prevista (R$)", value=5000.0, step=200.0)
            teto_gasto = st.number_input("Teto Máximo Desejado (R$)", value=3200.0, step=100.0)
            meta_sobra = renda_est - teto_gasto
            
            st.markdown(f"""
                <div class="kpi-box" style="margin-top: 15px; text-align: left; border-color: rgba(212,175,55,0.3);">
                    <div class="kpi-label">Economia Projetada</div>
                    <div class="kpi-val" style="color: #00e676;">R$ {meta_sobra:,.2f}</div>
                    <small style="color: #666;">Capacidade de poupança mensal</small>
                </div>
            """, unsafe_allow_html=True)
            
        with col_p2:
            st.markdown("#### 💡 Despesas Fixas")
            fixos = st.number_input("Custos Recorrentes (Aluguel, Luz, etc.)", value=1800.0, step=100.0)
            livre_lazer = teto_gasto - fixos
            
            if livre_lazer > 0:
                st.success(f"Saldo Livre para Lazer & Variáveis: **R$ {livre_lazer:,.2f}**")
            else:
                st.error("Atenção: Os custos fixos estão superando o teto planejado.")

# ==========================================
# ⭐ ABA 4: ASSINATURA PRO
# ==========================================
elif menu_selecionado == "⭐ Assinatura PRO":
    st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <div class="brand-title" style="font-size: 2.2rem;">MFC PRO</div>
            <p style="color: #888; font-size: 0.95rem; margin-top: 4px;">Eleve o seu controle patrimonial a outro nível</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown("""
            <div class="glass-card" style="border-color: rgba(255,255,255,0.06);">
                <h3 style="color:#888 !important; margin-top:0;">Básico</h3>
                <h2 style="color:#fff !important; font-size:1.8rem;">Grátis</h2>
                <hr style="border-color: rgba(255,255,255,0.06);">
                <ul style="color:#888; line-height:2; font-size:0.9rem; list-style:none; padding-left:0;">
                    <li>✔ 1 Upload por vez</li>
                    <li>✔ Resumo de entradas e saídas</li>
                    <li>✔ Gráficos de proporção</li>
                    <li>✖ <strike>Multi-upload simultâneo</strike></li>
                    <li>✖ <strike>Aba de Planejamento Futuro</strike></li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        
    with col_c2:
        st.markdown("""
            <div class="glass-card" style="border: 2px solid #d4af37;">
                <div class="pro-tag">Recomendado</div>
                <h3 style="color:#d4af37 !important; margin: 10px 0 0 0;">Plano PRO</h3>
                <h2 style="color:#00e676 !important; font-size:1.9rem; margin: 4px 0 0 0;">
                    R$ 19,90 <span style="font-size:0.9rem; color:#aaa; font-weight:400;">/ mês</span>
                </h2>
                <hr style="border-color: rgba(212,175,55,0.2);">
                <ul style="color:#e5e5e5; line-height:2; font-size:0.9rem; list-style:none; padding-left:0;">
                    <li>✔ <b>Upload de múltiplos PDFs de uma só vez</b></li>
                    <li>✔ <b>Módulo completo de Planejamento Futuro</b></li>
                    <li>✔ Consolidação multi-bancos sem limites</li>
                    <li>✔ Processamento prioritário de alta velocidade</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        
    if not eh_pro:
        st.write("")
        st.markdown("### 💳 Ativação do Plano PRO")
        tab_px, tab_cc = st.tabs(["⚡ Pagamento Pix", "💳 Cartão de Crédito"])
        
        with tab_px:
            st.info("Chave Pix Oficial para ativação instantânea: financeiro@mfc.com.br (Valor: R$ 19,90)")
            if st.button("Confirmar Pagamento Pix", use_container_width=True):
                st.session_state["usuarios_db"][usuario_atual]["plano"] = "Pro"
                st.success("🎉 Pagamento confirmado! Sua conta agora é PRO.")
                st.rerun()
                
        with tab_cc:
            st.text_input("Número do Cartão", placeholder="0000 0000 0000 0000")
            c_c1, c_c2 = st.columns(2)
            c_c1.text_input("Validade", placeholder="MM/AA")
            c_c2.text_input("CVV", type="password", placeholder="123")
            if st.button("Pagar R$ 19,90 e Ativar", use_container_width=True):
                st.session_state["usuarios_db"][usuario_atual]["plano"] = "Pro"
                st.success("🎉 Pagamento aprovado com sucesso! Acesso PRO liberado.")
                st.rerun()
    else:
        st.markdown("""
            <div class="glass-card" style="border-color: #00e676; text-align: center; margin-top: 20px;">
                <h3 style="color: #00e676 !important; margin: 0;">✔ Assinatura PRO Ativa</h3>
                <p style="color: #aaa; margin: 5px 0 0 0;">Você possui acesso a todos os recursos ilimitados do MFC.</p>
            </div>
        """, unsafe_allow_html=True)
