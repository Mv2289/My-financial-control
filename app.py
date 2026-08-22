import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
import json
import smtplib
import mercadopago
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pypdf import PdfReader

st.set_page_config(
    page_title="MFC | My Financial Control",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo institucional XP / Private Banking Premium com Redesign Moderno do Menu Lateral
css_style = """
<style>
    @import url('[https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap](https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap)');
    
    html, body, [class*='css'], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background-color: #08090b !important;
        color: #e5e5e5 !important;
    }
    
    section[data-testid='stSidebar'] {
        background-color: #0c0e12 !important;
        border-right: 1px solid rgba(212, 175, 55, 0.1) !important;
    }
    
    .brand-title {
        font-size: 2.6rem;
        font-weight: 800;
        letter-spacing: 2px;
        color: #d4af37;
        margin: 0;
        line-height: 1;
        text-align: center;
    }
    .brand-subtitle {
        font-size: 0.72rem;
        letter-spacing: 4px;
        text-transform: uppercase;
        color: #8c8568;
        margin-top: 4px;
        font-weight: 600;
        text-align: center;
        margin-bottom: 24px;
    }
    
    .user-profile-card {
        background: linear-gradient(145deg, rgba(22, 25, 34, 0.8), rgba(14, 16, 22, 0.95));
        border: 1px solid rgba(212, 175, 55, 0.18);
        border-radius: 14px;
        padding: 18px 16px;
        margin-bottom: 22px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    .glass-card {
        background: rgba(18, 20, 26, 0.75);
        border: 1px solid rgba(212, 175, 55, 0.14);
        border-radius: 14px;
        padding: 24px;
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
        font-size: 0.76rem;
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
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: 700 !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button:hover {
        background: #e6c35c !important;
        border-color: #e6c35c !important;
        color: #000000 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.25) !important;
    }
    
    .pro-tag {
        background: rgba(212, 175, 55, 0.12);
        color: #d4af37;
        border: 1px solid rgba(212, 175, 55, 0.45);
        font-size: 0.72rem;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 20px;
        display: inline-block;
        letter-spacing: 0.5px;
    }
    
    /* ==========================================
       REDESIGN DO MENU LATERAL (SEM BOLINHAS)
       ========================================== */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    
    div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
    
    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        padding: 11px 16px !important;
        border-radius: 10px !important;
        cursor: pointer !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        margin: 0 !important;
    }
    
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
        background: rgba(212, 175, 55, 0.06) !important;
        border-color: rgba(212, 175, 55, 0.25) !important;
        transform: translateX(3px);
    }
    
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(90deg, rgba(212, 175, 55, 0.16), rgba(212, 175, 55, 0.04)) !important;
        border: 1px solid #d4af37 !important;
        box-shadow: 0 0 16px rgba(212, 175, 55, 0.15) !important;
    }
    
    div[data-testid="stRadio"] > div[role="radiogroup"] > label p {
        color: #a0a0a5 !important;
        font-size: 0.92rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
        letter-spacing: 0.2px !important;
    }
    
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) p {
        color: #d4af37 !important;
        font-weight: 700 !important;
    }
    
    div[data-baseweb="select"] input {
        caret-color: transparent !important;
        cursor: pointer !important;
        user-select: none !important;
        pointer-events: none !important;
    }
    div[data-baseweb="select"] {
        cursor: pointer !important;
    }
    [data-testid="stDataFrameHeader"] button,
    [data-testid="stDataFrameHeaderMenu"],
    [data-testid="stDataFrame"] th button,
    [data-testid="stDataFrame"] [role="columnheader"] button {
        display: none !important;
        opacity: 0 !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }
    #MainMenu, footer, header {
        visibility: hidden !important;
    }
</style>
<script>
    window.parent.document.addEventListener('keydown', function(e) {
        if ((e.key === 'c' || e.key === 'C') && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
            e.stopPropagation();
        }
    }, true);
</script>
"""
st.markdown(css_style, unsafe_allow_html=True)

# Disparo de e-mail institucional
def enviar_email_boas_vindas(destinatario_email, nome_usuario):
    remetente = st.secrets.get("EMAIL_REMETENTE", "")
    senha_remetente = st.secrets.get("EMAIL_SENHA", "")
    if remetente and senha_remetente:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "MFC | Acesso Liberado"
            msg["From"] = "MFC Gestao Financeira <" + remetente + ">"
            msg["To"] = destinatario_email
            html_msg = "<div style='background-color:#08090b; color:#e5e5e5; padding:30px; border-radius:10px; border:1px solid #d4af37;'><h1 style='color:#d4af37;'>MFC</h1><p>Ola <b>" + str(nome_usuario) + "</b>, sua conta foi ativada com sucesso.</p></div>"
            msg.attach(MIMEText(html_msg, "html"))
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
                servidor.login(remetente, senha_remetente)
                servidor.sendmail(remetente, destinatario_email, msg.as_string())
            return True, "E-mail enviado."
        except Exception as e:
            return False, "Erro: " + str(e)
    return True, ""

# Funções da API Mercado Pago para Pix Automático
def criar_cobranca_pix(access_token, email_cliente, nome_cliente, valor=19.90):
    sdk = mercadopago.SDK(access_token)
    primeiro_nome = nome_cliente.split()[0] if nome_cliente else "Cliente"
    email_valido = email_cliente if ("@" in email_cliente and "." in email_cliente) else "contato@mfc.com"
    payment_data = {
        "transaction_amount": float(valor),
        "description": "MFC Assinatura PRO - Mensal",
        "payment_method_id": "pix",
        "payer": {
            "email": email_valido,
            "first_name": primeiro_nome
        }
    }
    payment_response = sdk.payment().create(payment_data)
    payment = payment_response.get("response", {})
    
    qr_base64 = payment.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64", "")
    qr_copia_cola = payment.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", "")
    payment_id = payment.get("id")
    
    return payment_id, qr_base64, qr_copia_cola

def checar_status_pagamento(access_token, payment_id):
    sdk = mercadopago.SDK(access_token)
    payment_response = sdk.payment().get(payment_id)
    payment = payment_response.get("response", {})
    return payment.get("status", "pending")

# Banco de dados e sessão persistente
if "usuarios_db" not in st.session_state:
    st.session_state["usuarios_db"] = {
        "admin": {
            "email": "admin@mfc.com", 
            "senha": "admin", 
            "plano": "Pro", 
            "data_aquisicao": "01/01/2026", 
            "data_vencimento": "01/01/2099"
        },
        "Marcos": {
            "email": "marcos@mfc.com", 
            "senha": "1234", 
            "plano": "Gratuito", 
            "data_aquisicao": None, 
            "data_vencimento": None
        }
    }

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""
if "transacoes" not in st.session_state:
    st.session_state["transacoes"] = []
if "chat_mensagens" not in st.session_state:
    st.session_state["chat_mensagens"] = []
if "pix_payment_id" not in st.session_state:
    st.session_state["pix_payment_id"] = None
if "pix_qr_base64" not in st.session_state:
    st.session_state["pix_qr_base64"] = ""
if "pix_copia_cola" not in st.session_state:
    st.session_state["pix_copia_cola"] = ""

# Estado persistente dos filtros do Dashboard
if "filtro_periodo" not in st.session_state:
    st.session_state["filtro_periodo"] = None
if "filtro_busca" not in st.session_state:
    st.session_state["filtro_busca"] = ""
if "filtro_tipo" not in st.session_state:
    st.session_state["filtro_tipo"] = "Todos"
if "filtro_ordem" not in st.session_state:
    st.session_state["filtro_ordem"] = "Mais Recentes"

# Função de checagem e expiração automática de 30 dias
def verificar_expiracao_assinaturas():
    hoje = datetime.now().date()
    for u, dados in st.session_state["usuarios_db"].items():
        if u != "admin" and dados.get("plano") == "Pro":
            dt_venc_str = dados.get("data_vencimento")
            if dt_venc_str:
                try:
                    dt_venc = datetime.strptime(dt_venc_str, "%d/%m/%Y").date()
                    if hoje > dt_venc:
                        st.session_state["usuarios_db"][u]["plano"] = "Gratuito"
                except Exception:
                    pass

verificar_expiracao_assinaturas()

# Ativação do Plano PRO com ciclo de 30 dias
def ativar_plano_pro(nome_usuario):
    hoje = datetime.now()
    vencimento = hoje + timedelta(days=30)
    st.session_state["usuarios_db"][nome_usuario]["plano"] = "Pro"
    st.session_state["usuarios_db"][nome_usuario]["data_aquisicao"] = hoje.strftime("%d/%m/%Y")
    st.session_state["usuarios_db"][nome_usuario]["data_vencimento"] = vencimento.strftime("%d/%m/%Y")

# Tela de Autenticação
def tela_autenticacao():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div style='text-align: center; margin: 40px 0 20px 0;'><div class='brand-title'>MFC</div><div class='brand-subtitle'>MY FINANCIAL CONTROL</div></div>", unsafe_allow_html=True)
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
                        "plano": "Gratuito",
                        "data_aquisicao": None,
                        "data_vencimento": None
                    }
                    _, msg_email = enviar_email_boas_vindas(novo_email, novo_usuario)
                    st.success("Conta registrada com sucesso! " + str(msg_email))

if not st.session_state["autenticado"]:
    tela_autenticacao()
    st.stop()

# Usuário Ativo
usuario_atual = st.session_state.get("usuario_logado", "")
dados_usuario = st.session_state["usuarios_db"].get(usuario_atual, {"plano": "Gratuito", "email": ""})
plano_atual = dados_usuario.get("plano", "Gratuito")
eh_pro = (plano_atual == "Pro")
user_email = dados_usuario.get("email", "")

eh_admin = (usuario_atual == "admin")

api_key = st.secrets.get("GEMINI_API_KEY", "")
mp_access_token = st.secrets.get("MP_ACCESS_TOKEN", "")

# Barra Lateral
with st.sidebar:
    st.markdown("<div style='padding: 8px 0 16px 0; text-align: center;'><div class='brand-title' style='font-size: 2.3rem;'>MFC</div><div class='brand-subtitle'>MY FINANCIAL CONTROL</div></div>", unsafe_allow_html=True)
    
    badge_html = '<span class="pro-tag">★ PLANO PRO</span>' if eh_pro else '<span style="background:rgba(255,255,255,0.05); color:#888; font-size:0.72rem; padding:3px 10px; border-radius:12px; font-weight:600;">PLANO BÁSICO</span>'
    card_perfil_html = "<div class='user-profile-card'><div style='font-size: 0.68rem; color: #73737a; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;'>Conta Ativa</div><div style='font-weight: 800; font-size: 1.12rem; color: #ffffff; margin-top: 2px;'>" + str(usuario_atual) + "</div><div style='font-size: 0.76rem; color: #948d70; margin: 2px 0 10px 0; word-break: break-all;'>" + str(user_email) + "</div>" + badge_html + "</div>"
    st.markdown(card_perfil_html, unsafe_allow_html=True)
    
    rotas_chaves = ["upload", "dashboard", "chat_ia", "planejamento", "assinatura"]
    mapa_titulos = {
        "upload": "📥  Upload de Extratos",
        "dashboard": "📊  Dashboard & Métricas",
        "chat_ia": "💬  Consultor IA (PRO)",
        "planejamento": "🎯  Planejamento Estratégico",
        "assinatura": "⭐  Assinatura PRO"
    }
    
    if eh_admin:
        rotas_chaves.append("usuarios")
        mapa_titulos["usuarios"] = "👥  Gestão de Usuários"
        
    menu_selecionado = st.radio("Menu", rotas_chaves, format_func=lambda x: mapa_titulos[x], label_visibility="collapsed")
    st.markdown("<div style='margin: 16px 0;'></div>", unsafe_allow_html=True)
        
    if not api_key:
        with st.expander("⚙️ Chave de Integração"):
            api_key = st.text_input("Chave de Acesso", type="password")

    if st.session_state["transacoes"]:
        if st.button("🗑️ Limpar Dados Atuais", use_container_width=True):
            st.session_state["transacoes"] = []
            st.session_state["chat_mensagens"] = []
            st.session_state["filtro_periodo"] = None
            st.session_state["filtro_busca"] = ""
            st.rerun()

    if st.button("🚪 Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.rerun()

# Motor IA para Extração
def processar_extrato_pdf(file, chave_api):
    reader = PdfReader(file)
    texto_extrato = ""
    for page in reader.pages:
        texto_extrato += page.extract_text() or ""
        
    if not texto_extrato.strip():
        raise Exception("Não foi possível extrair texto do PDF.")

    genai.configure(api_key=chave_api)
    prompt = (
        "Analise o extrato financeiro e retorne EXCLUSIVAMENTE um array JSON contendo objetos no formato: "
        '[{"data":"DD/MM/AAAA","descricao":"Nome","tipo":"Receita" ou "Despesa","valor":150.50}]. '
        "EXTRATO: " + texto_extrato
    )
    
    modelos_para_testar = [
        "models/gemini-3.6-flash",
        "gemini-3.6-flash",
        "models/gemini-2.0-flash",
        "gemini-2.0-flash",
        "models/gemini-1.5-flash",
        "gemini-1.5-flash"
    ]
    
    response = None
    ultimo_erro = None
    
    for nome_modelo in modelos_para_testar:
        try:
            m = genai.GenerativeModel(model_name=nome_modelo, generation_config={"response_mime_type": "application/json"})
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

# Motor IA para Chat Consultor Financeiro com formatação estritamente limpa
def responder_chat_consultor(chave_api, transacoes_lista, historico_chat, pergunta_usuario):
    genai.configure(api_key=chave_api)
    
    contexto_financeiro = json.dumps(transacoes_lista, ensure_ascii=False)
    system_instruction = (
        "Você é o Consultor Financeiro Oficial do MFC (My Financial Control). "
        "Seu tom é executivo, direto, analítico e de alto nível. "
        "Você tem acesso total aos lançamentos bancários conciliados do cliente neste JSON: " + contexto_financeiro + ". "
        "Analise esses dados para responder às perguntas do usuário com números exatos, insights de corte de custos, "
        "identificação de gastos invisíveis/supérfluos e recomendações estratégicas de investimento e poupança. "
        "REGRA ESTRITA DE FORMATAÇÃO: NÃO utilize notação matemática LaTeX (como $ ou $$), nem blocos de código, "
        "nem tags de cores. Escreva valores financeiros em formato de texto comum (exemplo: R$ 1.500,00 ou R$ 45,00). "
        "Use formatação limpa em tópicos com marcadores e negrito comum (**texto**)."
    )
    
    modelos = ["models/gemini-3.6-flash", "gemini-3.6-flash", "models/gemini-2.0-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    
    prompt_conversa = system_instruction + chr(10) + chr(10) + "HISTÓRICO DA CONVERSA:" + chr(10)
    for msg in historico_chat:
        prompt_conversa += str(msg["role"]).upper() + ": " + str(msg["content"]) + chr(10)
    prompt_conversa += "USER: " + str(pergunta_usuario) + chr(10) + "ASSISTANT:"
    
    for mod in modelos:
        try:
            m = genai.GenerativeModel(model_name=mod)
            res = m.generate_content(prompt_conversa)
            if res and res.text:
                texto_limpo = res.text.strip()
                texto_limpo = texto_limpo.replace("$", "")
                return texto_limpo
        except Exception:
            continue
    return "Desculpe, não foi possível analisar sua solicitação no momento. Verifique sua chave de integração."

# ==========================================
# 📥 ABA 1: UPLOAD DE EXTRATOS
# ==========================================
if menu_selecionado == "upload":
    st.markdown("<div class='glass-card'><h2 style='margin:0; color:#d4af37;'>📥 Importação de Extratos Bancários</h2><p style='color:#aaa; font-size:0.95rem; margin-top:6px;'>Carregue seus extratos em PDF para conciliação automática.</p></div>", unsafe_allow_html=True)
    
    if eh_pro:
        st.markdown("##### 🌟 Upload Multi-Arquivos (PRO)")
        arquivos = st.file_uploader("Selecione os PDFs", type=["pdf"], accept_multiple_files=True)
    else:
        st.markdown("##### 📄 Upload Individual (Plano Básico)")
        arquivo_unico = st.file_uploader("Selecione o extrato em PDF", type=["pdf"], accept_multiple_files=False)
        arquivos = [arquivo_unico] if arquivo_unico else []
        
    st.write("")
    if arquivos and st.button("🚀 Processar e Conciliar Extratos", use_container_width=True):
        if not api_key:
            st.error("Chave de acesso não configurada.")
        else:
            todas_transacoes = []
            with st.spinner("Processando extratos bancários..."):
                for arq in arquivos:
                    try:
                        res = processar_extrato_pdf(arq, api_key)
                        todas_transacoes.extend(res)
                    except Exception as err:
                        st.error("Erro em " + str(arq.name) + ": " + str(err))
                
                if todas_transacoes:
                    st.session_state["transacoes"].extend(todas_transacoes)
                    st.session_state["filtro_periodo"] = None
                    st.success("✨ Sucesso! Movimentações consolidadas.")

# ==========================================
# 📊 ABA 2: DASHBOARD & MÉTRICAS
# ==========================================
elif menu_selecionado == "dashboard":
    df_raw = pd.DataFrame(st.session_state["transacoes"])
    
    if df_raw.empty:
        st.markdown("<div class='glass-card' style='text-align:center; padding: 40px;'><h3 style='color:#888;'>Nenhum Extrato Importado</h3><p style='color:#666;'>Faça o upload do seu primeiro PDF bancário na aba 'Upload de Extratos'.</p></div>", unsafe_allow_html=True)
    else:
        df_raw["valor"] = pd.to_numeric(df_raw["valor"], errors="coerce").fillna(0.0)
        df_raw["data_dt"] = pd.to_datetime(df_raw["data"], format="%d/%m/%Y", errors="coerce")
        df_raw = df_raw.sort_values(by="data_dt", ascending=False)
        
        # Filtros de busca e período no topo com chaves de sessão persistentes
        st.markdown("### 📋 Lançamentos Conciliados")
        f1, f2, f3, f4 = st.columns([1.2, 0.9, 0.9, 1.2])
        
        with f1:
            busca = st.text_input("🔍 Buscar lançamento", value=st.session_state["filtro_busca"], key="dash_input_busca", placeholder="Nome ou comércio...")
            st.session_state["filtro_busca"] = busca
            
        with f2:
            opcoes_tipo = ["Todos", "Receitas", "Despesas"]
            idx_tipo = opcoes_tipo.index(st.session_state["filtro_tipo"]) if st.session_state["filtro_tipo"] in opcoes_tipo else 0
            filtro_tipo = st.selectbox("Tipo", opcoes_tipo, index=idx_tipo, key="dash_select_tipo")
            st.session_state["filtro_tipo"] = filtro_tipo
            
        with f3:
            opcoes_ordem = ["Mais Recentes", "Mais Antigos", "Maior Valor", "Menor Valor"]
            idx_ordem = opcoes_ordem.index(st.session_state["filtro_ordem"]) if st.session_state["filtro_ordem"] in opcoes_ordem else 0
            ordem = st.selectbox("Ordenar por", opcoes_ordem, index=idx_ordem, key="dash_select_ordem")
            st.session_state["filtro_ordem"] = ordem
            
        with f4:
            min_dt = df_raw["data_dt"].min()
            max_dt = df_raw["data_dt"].max()
            if pd.isna(min_dt) or pd.isna(max_dt):
                min_val, max_val = datetime.today().date(), datetime.today().date()
            else:
                min_val, max_val = min_dt.date(), max_dt.date()
                
            val_periodo_inicial = st.session_state["filtro_periodo"] if st.session_state["filtro_periodo"] else (min_val, max_val)
            intervalo_data = st.date_input("Período", value=val_periodo_inicial, format="DD/MM/YYYY", key="dash_date_periodo")
            st.session_state["filtro_periodo"] = intervalo_data

        # Dataset filtrado pelo período para padronizar KPIs, Pizza e Tabela
        df_periodo = df_raw.copy()
        if isinstance(intervalo_data, (tuple, list)) and len(intervalo_data) == 2:
            d_ini, d_fim = intervalo_data
            df_periodo = df_periodo[(df_periodo["data_dt"].dt.date >= d_ini) & (df_periodo["data_dt"].dt.date <= d_fim)]

        df_rec_periodo = df_periodo[df_periodo["tipo"] == "Receita"]
        df_des_periodo = df_periodo[df_periodo["tipo"] == "Despesa"]
        
        total_entradas = float(df_rec_periodo["valor"].sum())
        total_saidas = float(df_des_periodo["valor"].sum())
        saldo_liquido = total_entradas - total_saidas
        if total_entradas > 0:
            taxa_poupanca = (saldo_liquido / total_entradas) * 100.0
        else:
            taxa_poupanca = 0.0
        cor_saldo = "#00e676" if saldo_liquido >= 0 else "#ff5252"

        # Cards KPIs sincronizados com o período selecionado
        k1, k2, k3, k4 = st.columns(4)
        k1.markdown("<div class='kpi-box'><div class='kpi-label'>Receitas</div><div class='kpi-val' style='color: #00e676;'>+ R$ {:,.2f}</div></div>".format(total_entradas), unsafe_allow_html=True)
        k2.markdown("<div class='kpi-box'><div class='kpi-label'>Despesas</div><div class='kpi-val' style='color: #ff5252;'>- R$ {:,.2f}</div></div>".format(total_saidas), unsafe_allow_html=True)
        k3.markdown("<div class='kpi-box'><div class='kpi-label'>Saldo Líquido</div><div class='kpi-val' style='color: {};'>R$ {:,.2f}</div></div>".format(cor_saldo, saldo_liquido), unsafe_allow_html=True)
        k4.markdown("<div class='kpi-box'><div class='kpi-label'>Taxa de Poupança</div><div class='kpi-val' style='color: #d4af37;'>{:.1f}%</div></div>".format(taxa_poupanca), unsafe_allow_html=True)
        
        st.write("")
        st.write("")

        # Filtros adicionais para tabela (texto e tipo)
        df_filtrado = df_periodo.copy()
        if busca:
            df_filtrado = df_filtrado[df_filtrado["descricao"].str.contains(busca, case=False, na=False)]
        if filtro_tipo == "Receitas":
            df_filtrado = df_filtrado[df_filtrado["tipo"] == "Receita"]
        elif filtro_tipo == "Despesas":
            df_filtrado = df_filtrado[df_filtrado["tipo"] == "Despesa"]

        if ordem == "Mais Recentes":
            df_filtrado = df_filtrado.sort_values(by="data_dt", ascending=False)
        elif ordem == "Mais Antigos":
            df_filtrado = df_filtrado.sort_values(by="data_dt", ascending=True)
        elif ordem == "Maior Valor":
            df_filtrado = df_filtrado.sort_values(by="valor", ascending=False)
        elif ordem == "Menor Valor":
            df_filtrado = df_filtrado.sort_values(by="valor", ascending=True)

        c_tab, c_pie = st.columns([1.35, 0.95])
        with c_tab:
            df_render = df_filtrado[["data", "descricao", "tipo", "valor"]].copy()
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
                height=380
            )
            
        with c_pie:
            st.markdown("##### 📊 Proporção de Fluxo")
            total_vol = total_entradas + total_saidas
            
            # Gráfico de Rosca Ultra Moderno (Compatível com todas as versões do Plotly)
            fig_pie = go.Figure(data=[go.Pie(
                labels=["Receitas", "Despesas"],
                values=[total_entradas, total_saidas],
                hole=0.68,
                marker=dict(
                    colors=["#00e676", "#ff4343"],
                    line=dict(color="#08090b", width=3)
                ),
                textinfo="percent",
                textposition="inside",
                insidetextorientation="horizontal",
                textfont=dict(size=14, color="#ffffff", family="Plus Jakarta Sans"),
                sort=False,
                direction="clockwise"
            )])
            
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.12,
                    xanchor="center",
                    x=0.5,
                    font=dict(color="#a0a0a5", size=12, family="Plus Jakarta Sans"),
                    itemgap=20
                ),
                annotations=[
                    dict(
                        text="<span style='font-size:11px; color:#8c8568; letter-spacing:1px; font-weight:700;'>VOLUME TOTAL</span><br><b style='font-size:18px; color:#ffffff; font-family:Plus Jakarta Sans;'>R$ {:,.2f}</b>".format(total_vol),
                        x=0.5, y=0.5,
                        font_size=14,
                        showarrow=False
                    )
                ],
                margin=dict(t=10, b=30, l=10, r=10),
                height=360
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # ==========================================
        # GRÁFICO COMPARATIVO GERAL EM ESCALA (TODOS OS MESES + TOTAL GERAL)
        # ==========================================
        st.write("")
        st.markdown("### 📊 Evolução Mensal e Comparativo de Gastos")
        
        df_evol = df_raw.dropna(subset=["data_dt"]).copy()
        df_evol["mes_ano_period"] = df_evol["data_dt"].dt.to_period("M")
        
        meses_unicos = sorted(df_evol["mes_ano_period"].unique())
        
        if len(meses_unicos) > 0:
            meses_labels = [m.strftime("%b/%y").capitalize() for m in meses_unicos]
            receitas_mes = []
            despesas_mes = []
            
            for m in meses_unicos:
                df_m = df_evol[df_evol["mes_ano_period"] == m]
                rec = float(df_m[df_m["tipo"] == "Receita"]["valor"].sum())
                des = float(df_m[df_m["tipo"] == "Despesa"]["valor"].sum())
                receitas_mes.append(rec)
                despesas_mes.append(des)
                
            total_geral_receitas = float(df_evol[df_evol["tipo"] == "Receita"]["valor"].sum())
            total_geral_despesas = float(df_evol[df_evol["tipo"] == "Despesa"]["valor"].sum())
            
            labels_com_total = meses_labels + ["Total"]
            receitas_com_total = receitas_mes + [total_geral_receitas]
            despesas_com_total = despesas_mes + [total_geral_despesas]
            
            fig_barras = go.Figure()
            
            fig_barras.add_trace(go.Bar(
                name="Receitas / Ganhos",
                x=labels_com_total,
                y=receitas_com_total,
                marker=dict(color="#00e676", line=dict(color="rgba(0,230,118,0.3)", width=1)),
                text=[f"R$ {v:,.0f}" if v > 0 else "" for v in receitas_com_total],
                textposition="outside",
                textfont=dict(color="#00e676", size=11, family="Plus Jakarta Sans")
            ))
            
            fig_barras.add_trace(go.Bar(
                name="Despesas / Gastos",
                x=labels_com_total,
                y=despesas_com_total,
                marker=dict(color="#ff5252", line=dict(color="rgba(255,82,82,0.3)", width=1)),
                text=[f"R$ {v:,.0f}" if v > 0 else "" for v in despesas_com_total],
                textposition="outside",
                textfont=dict(color="#ff5252", size=11, family="Plus Jakarta Sans")
            ))
            
            fig_barras.update_layout(
                barmode="group",
                bargap=0.25,
                bargroupgap=0.1,
                paper_bgcolor="#0f1117",
                plot_bgcolor="#0f1117",
                font=dict(color="#e5e5e5", family="Plus Jakarta Sans"),
                legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
                margin=dict(t=40, b=30, l=20, r=20),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.05)",
                    zerolinecolor="rgba(255,255,255,0.1)",
                    tickprefix="R$ "
                ),
                xaxis=dict(
                    showgrid=False
                ),
                height=430
            )
            st.plotly_chart(fig_barras, use_container_width=True)

# ==========================================
# 💬 ABA: CONSULTOR IA (PRO)
# ==========================================
elif menu_selecionado == "chat_ia":
    if not eh_pro:
        st.markdown(
            "<div class='glass-card' style='text-align: center; border: 1px solid #d4af37; padding: 40px 20px;'>"
            "<div class='pro-tag'>Recurso Exclusivo PRO</div>"
            "<h2 style='color: #d4af37; margin: 15px 0 10px 0;'>💬 Consultor Financeiro com IA</h2>"
            "<p style='color: #bbb; max-width: 580px; margin: 0 auto 20px auto; font-size: 0.95rem;'>"
            "Converse em tempo real com seu consultor de patrimônio IA. Ele audita seus extratos, "
            "identifica assinaturas esquecidas, aponta onde você mais gastou e monta seu plano de corte de custos."
            "</p>"
            "<div style='font-size: 1.4rem; color: #00e676; font-weight: 800; margin-bottom: 20px;'>R$ 19,90 / mês</div>"
            "</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div class='glass-card'>"
            "<h2 style='margin:0; color:#d4af37;'>💬 Consultor Financeiro IA</h2>"
            "<p style='color:#aaa; font-size:0.95rem; margin-top:4px;'>"
            "Tire dúvidas estratégicas sobre seus extratos, receba diagnósticos de gastos e planos de economia."
            "</p></div>",
            unsafe_allow_html=True
        )
        
        if not st.session_state["transacoes"]:
            st.info("💡 Dica: Importe seus extratos na aba 'Upload de Extratos' para que o consultor possa auditar suas contas com precisão.")
            
        # Renderizar mensagens anteriores da sessão
        for msg in st.session_state["chat_mensagens"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
        # Captura input do usuário
        if prompt_user := st.chat_input("Ex: Quanto gastei com delivery? Como cortar R$ 400 esse mês?"):
            st.session_state["chat_mensagens"].append({"role": "user", "content": prompt_user})
            with st.chat_message("user"):
                st.markdown(prompt_user)
                
            with st.chat_message("assistant"):
                with st.spinner("Consultor IA analisando suas finanças..."):
                    resposta_ia = responder_chat_consultor(
                        api_key, 
                        st.session_state["transacoes"], 
                        st.session_state["chat_mensagens"][:-1], 
                        prompt_user
                    )
                    st.markdown(resposta_ia)
                    st.session_state["chat_mensagens"].append({"role": "assistant", "content": resposta_ia})

# ==========================================
# 🎯 ABA 4: PLANEJAMENTO ESTRATÉGICO
# ==========================================
elif menu_selecionado == "planejamento":
    if not eh_pro:
        st.markdown(
            "<div class='glass-card' style='text-align: center; border: 1px solid #d4af37; padding: 40px 20px;'>"
            "<div class='pro-tag'>Recurso Exclusivo PRO</div>"
            "<h2 style='color: #d4af37; margin: 15px 0 10px 0;'>🎯 Planejamento Orçamentário</h2>"
            "<p style='color: #bbb; max-width: 550px; margin: 0 auto 20px auto; font-size: 0.95rem;'>"
            "Projete metas para os próximos meses e acompanhe sua capacidade de investimento."
            "</p>"
            "<div style='font-size: 1.4rem; color: #00e676; font-weight: 800; margin-bottom: 15px;'>R$ 19,90 / mês</div>"
            "</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown("<div class='glass-card'><h2 style='margin:0; color:#d4af37;'>🎯 Planejamento Orçamentário Estratégico</h2></div>", unsafe_allow_html=True)
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("#### 🎯 Metas de Gastos")
            renda_est = st.number_input("Renda Prevista (R$)", value=5000.0, step=200.0)
            teto_gasto = st.number_input("Teto Máximo Desejado (R$)", value=3200.0, step=100.0)
            meta_sobra = renda_est - teto_gasto
            st.markdown("<div class='kpi-box' style='margin-top: 15px; text-align: left; border-color: rgba(212,175,55,0.3);'><div class='kpi-label'>Economia Projetada</div><div class='kpi-val' style='color: #00e676;'>R$ {:,.2f}</div><small style='color: #666;'>Capacidade de poupança mensal</small></div>".format(meta_sobra), unsafe_allow_html=True)
        with col_p2:
            st.markdown("#### 💡 Despesas Fixas")
            fixos = st.number_input("Custos Recorrentes", value=1800.0, step=100.0)
            livre_lazer = teto_gasto - fixos
            if livre_lazer > 0:
                st.success("Saldo Livre: R$ {:,.2f}".format(livre_lazer))
            else:
                st.error("Atenção: Os custos fixos superam o teto.")

# ==========================================
# ⭐ ABA 5: ASSINATURA PRO (PRODUÇÃO - R$ 19,90)
# ==========================================
elif menu_selecionado == "assinatura":
    st.markdown(
        "<div style='text-align: center; margin-bottom: 30px;'>"
        "<div class='brand-title' style='font-size: 2.2rem;'>MFC PRO</div>"
        "<p style='color: #888; font-size: 0.95rem; margin-top: 4px;'>Eleve o seu controle patrimonial</p>"
        "</div>",
        unsafe_allow_html=True
    )
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown(
            "<div class='glass-card' style='border-color: rgba(255,255,255,0.06);'>"
            "<h3 style='color:#888 !important; margin-top:0;'>Básico</h3>"
            "<h2 style='color:#fff !important; font-size:1.8rem;'>Grátis</h2>"
            "<hr style='border-color: rgba(255,255,255,0.06);'>"
            "<ul style='color:#888; line-height:2; font-size:0.9rem; list-style:none; padding-left:0;'><li>✔ 1 Upload por vez</li><li>✔ Resumo de entradas e saídas</li><li>✔ Gráficos de proporção e escala</li><li>✖ Consultor Financeiro com IA (Chat)</li><li>✖ Multi-upload simultâneo</li><li>✖ Aba de Planejamento Estratégico</li></ul></div>",
            unsafe_allow_html=True
        )
        
    with col_c2:
        st.markdown(
            "<div class='glass-card' style='border: 2px solid #d4af37;'><div class='pro-tag'>Recomendado</div><h3 style='color:#d4af37 !important; margin: 10px 0 0 0;'>Plano PRO</h3><h2 style='color:#00e676 !important; font-size:1.9rem; margin: 4px 0 0 0;'>R$ 19,90 <span style='font-size:0.9rem; color:#aaa; font-weight:400;'>/ mês</span></h2><hr style='border-color: rgba(212,175,55,0.2);'><ul style='color:#e5e5e5; line-height:2; font-size:0.9rem; list-style:none; padding-left:0;'><li>✔ <b>Consultor Financeiro IA (Chat Interativo)</b></li><li>✔ Upload de múltiplos PDFs</li><li>✔ Módulo de Planejamento Estratégico</li><li>✔ Sem limites de uso</li><li>✔ Processamento acelerado</li></ul></div>",
            unsafe_allow_html=True
        )
        
    if not eh_pro:
        st.write("")
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("💳 Ativação Instantânea com Liberação Automática")
        st.write("Valor da assinatura mensal: **R$ 19,90** (Pix)")
        
        if not mp_access_token:
            st.info("💡 Configure seu `MP_ACCESS_TOKEN` do Mercado Pago nos Secrets para habilitar a aprovação 100% automática.")
        
        if st.button("📱 Gerar QR Code Pix (R$ 19,90)", use_container_width=True):
            if mp_access_token:
                with st.spinner("Gerando cobrança Pix (R$ 19,90)..."):
                    pid, qrb64, copia_cola = criar_cobranca_pix(mp_access_token, user_email, usuario_atual, 19.90)
                    if qrb64:
                        st.session_state["pix_payment_id"] = pid
                        st.session_state["pix_qr_base64"] = qrb64
                        st.session_state["pix_copia_cola"] = copia_cola
                    else:
                        st.error("Erro ao comunicar com Mercado Pago. Verifique o token nos Secrets.")
            else:
                st.warning("Adicione MP_ACCESS_TOKEN nos Secrets para gerar cobranças dinâmicas.")
            
        if st.session_state["pix_qr_base64"]:
            c_qr1, c_qr2, c_qr3 = st.columns([1, 1.2, 1])
            with c_qr2:
                st.markdown("<div style='background:#ffffff; padding:20px; border-radius:14px; text-align:center; margin:20px 0; max-width:280px; margin-left:auto; margin-right:auto; box-shadow:0 8px 24px rgba(0,0,0,0.5);'><img src='data:image/png;base64," + str(st.session_state['pix_qr_base64']) + "' width='220' style='display:block; margin:0 auto;' alt='QR Code Pix' /></div>", unsafe_allow_html=True)
                
            if st.session_state["pix_payment_id"] and mp_access_token:
                status = checar_status_pagamento(mp_access_token, st.session_state["pix_payment_id"])
                if status == "approved":
                    ativar_plano_pro(usuario_atual)
                    st.session_state["pix_qr_base64"] = ""
                    st.session_state["pix_payment_id"] = None
                    st.balloons()
                    st.success("🎉 Pagamento de R$ 19,90 confirmado! Seu Plano PRO foi liberado automaticamente por 30 dias.")
                    st.rerun()
                else:
                    st.info("⏳ Aguardando pagamento do Pix de R$ 19,90... O sistema liberará o acesso automaticamente assim que o banco confirmar.")
                    if st.button("🔄 Atualizar Status Manualmente"):
                        st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='glass-card' style='border-color: #00e676; text-align: center; margin-top: 20px;'><h3 style='color: #00e676 !important; margin: 0;'>✔ Assinatura PRO Ativa</h3><p style='color: #aaa; margin: 5px 0 0 0;'>Você possui acesso a todos os recursos ilimitados do MFC.</p></div>", unsafe_allow_html=True)

# ==========================================
# 👥 ABA 6: GESTÃO DE USUÁRIOS (EXCLUSIVA PARA ADMIN)
# ==========================================
elif menu_selecionado == "usuarios" and eh_admin:
    st.markdown("<div class='glass-card'><h2 style='margin:0; color:#d4af37;'>👥 Painel de Controle de Usuários</h2><p style='color:#aaa; font-size:0.95rem; margin-top:4px;'>Visão administrativa de contas, vigências e controle de planos.</p></div>", unsafe_allow_html=True)
    
    lista_usuarios = []
    hoje = datetime.now().date()
    
    for nome_u, info_u in st.session_state["usuarios_db"].items():
        plano = info_u.get("plano", "Gratuito")
        dt_aquisicao = info_u.get("data_aquisicao") or "-"
        dt_vencimento = info_u.get("data_vencimento") or "-"
        
        status_vigencia = "Sem Plano"
        if plano == "Pro":
            if nome_u == "admin":
                status_vigencia = "🟢 Vitalício (Admin)"
            elif dt_vencimento != "-":
                try:
                    d_venc = datetime.strptime(dt_vencimento, "%d/%m/%Y").date()
                    dias_restantes = (d_venc - hoje).days
                    if dias_restantes >= 0:
                        status_vigencia = f"🟢 Ativo ({dias_restantes} dias)"
                    else:
                        status_vigencia = "🔴 Vencido"
                except Exception:
                    status_vigencia = "🟢 Ativo"
        
        lista_usuarios.append({
            "Usuário": nome_u,
            "E-mail": info_u.get("email", "-"),
            "Senha": info_u.get("senha", "-"),
            "Plano Atual": plano,
            "Data Aquisição": dt_aquisicao,
            "Data Vencimento": dt_vencimento,
            "Vigência": status_vigencia
        })
        
    df_users = pd.DataFrame(lista_usuarios)
    st.dataframe(df_users, use_container_width=True, hide_index=True)
    st.write("")
    st.markdown("### ⚡ Ações Rápidas de Planos")
    
    for u, dados in list(st.session_state["usuarios_db"].items()):
        col_m1, col_m2, col_m3 = st.columns([2.5, 1.2, 1.2])
        status_color = "#00e676" if dados['plano'] == 'Pro' else "#888888"
        venc_texto = f" (Vence: {dados.get('data_vencimento')})" if dados.get('data_vencimento') and u != 'admin' else ""
        
        col_m1.markdown(f"<b>{u}</b> — <span style='color:{status_color}; font-weight:bold;'>{dados['plano']}</span><small style='color:#aaa;'>{venc_texto}</small>", unsafe_allow_html=True)
        col_m1.caption(f"E-mail: {dados.get('email', '-')}")
        
        if dados["plano"] != "Pro":
            if col_m2.button("⭐ Ativar 30 Dias", key="btn_pro_" + str(u)):
                ativar_plano_pro(u)
                st.success(f"{u} agora é PRO por 30 dias!")
                st.rerun()
        else:
            if u not in ["admin"]:
                if col_m3.button("❌ Desativar", key="btn_down_" + str(u)):
                    st.session_state["usuarios_db"][u]["plano"] = "Gratuito"
                    st.session_state["usuarios_db"][u]["data_vencimento"] = None
                    st.info(f"{u} voltou ao Básico.")
                    st.rerun()
                    
        st.markdown("---")
