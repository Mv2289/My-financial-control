import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
import json
import smtplib
import segno
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pypdf import PdfReader

st.set_page_config(
    page_title="MFC | My Financial Control",
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

    .pending-tag {
        background: rgba(255, 193, 7, 0.15);
        color: #ffc107;
        border: 1px solid #ffc107;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
        letter-spacing: 1px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# --- GERADOR OFICIAL DE PAYLOAD PIX (BR CODE BACEN) ---
def gerar_payload_pix(chave_pix, nome_titular, cidade_titular, valor=19.90, txid="MFCPRO"):
    def tlv(tag, valor_str):
        return f"{tag}{len(valor_str):02d}{valor_str}"

    merchant_account = tlv("00", "br.gov.bcb.pix") + tlv("01", chave_pix)
    
    payload = (
        tlv("00", "01") +
        tlv("26", merchant_account) +
        tlv("52", "0000") +
        tlv("53", "986") +
        tlv("54", f"{valor:.2f}") +
        tlv("58", "BR") +
        tlv("59", nome_titular[:25].upper()) +
        tlv("60", cidade_titular[:15].upper()) +
        tlv("62", tlv("05", txid[:25])) +
        "6304"
    )

    crc = 0xFFFF
    for char in payload:
        crc ^= ord(char) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
                
    crc_hex = f"{crc:04X}"
    return payload + crc_hex

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
    
    if eh_pro:
        badge_html = '<span class="pro-tag">⭐ PLANO PRO</span>'
    elif plano_atual == "Pendente":
        badge_html = '<span class="pending-tag">⏳ PAGAMENTO EM ANÁLISE</span>'
    else:
        badge_html = '<span style="background:#1a1c24; color:#777; font-size:0.72rem; padding:3px 8px; border-radius:4px;">PLANO BÁSICO</span>'
    
    st.markdown(f"""
        <div style="background: #11131a; padding: 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 20px;">
            <div style="font-size: 0.72rem; color: #777; text-transform: uppercase;">Usuário</div>
            <div style="font-weight: 700; font-size: 1.05rem; color: #ffffff;">{usuario_atual}</div>
            <div style="font-size: 0.75rem; color: #a89f81; margin: 2px 0 10px 0;">{user_email}</div>
            {badge_html}
        </div>
    """, unsafe_allow_html=True)
    
    opcoes_menu = ["📥 Upload de Extratos", "📊 Dashboard & Métricas", "🔮 Planejamento Futuro", "⭐ Assinatura PRO"]
    if eh_master:
        opcoes_menu.append("👥 Gestão de Usuários")
        
    menu_selecionado = st.radio("Menu", opcoes_menu, label_visibility="collapsed")
    
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
            with st.spinner("Processando extratos bancários..."):
                for arq in arquivos:
                    try:
                        res = processar_extrato_pdf(arq, api_key)
                        todas_transacoes.extend(res)
                    except Exception as err:
                        st.error(f"Erro em {arq.name}: {err}")
                
                if todas_transacoes:
                    st.session_state["transacoes"].extend(todas_transacoes)
                    st.success("✨ Sucesso! Movimentações consolidadas.")
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
        df_raw["valor"] = pd.to_numeric(df_raw["valor"], errors="coerce").fillna(0.0)
        df_raw["data_dt"] = pd.to_datetime(df_raw["data"], format="%d/%m/%Y", errors="coerce")
        df_raw = df_raw.sort_values(by="data_dt", ascending=False)
        
        df_rec = df_raw[df_raw["tipo"] == "Receita"]
        df_des = df_raw[df_raw["tipo"] == "Despesa"]
        
        total_entradas = float(df_rec["valor"].sum())
        total_saidas = float(df_des["valor"].sum())
        saldo_liquido = total_entradas - total_saidas
        taxa_poupanca = ((saldo_liquido / total_entradas) * 100.0) if total_entradas > 0 else 0.0
        cor_saldo = "#00e676" if saldo_liquido >= 0 else "#ff5252"

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
            df_render = df_raw[["data", "descricao", "tipo", "valor"]].copy()
            
            st.dataframe(
                df_render,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "data": "Data",
                    "descricao": "Descrição",
                    "tipo": "Tipo",
                    "valor": st.column_config.NumberColumn(
                        "Valor (R$)",
                        format="R$ %.2f"
                    )
                },
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
                    Projete metas para os próximos meses, ger
