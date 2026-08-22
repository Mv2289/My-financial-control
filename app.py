import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
import json
import smtplib
import mercadopago
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pypdf import PdfReader

st.set_page_config(
    page_title="MFC | My Financial Control",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo institucional XP com bloqueio de escrita em select e menus de tabela
css_style = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    html, body, [class*='css'], .stApp { font-family: 'Inter', sans-serif !important; background-color: #08090b !important; color: #e5e5e5 !important; }
    section[data-testid='stSidebar'] { background-color: #0d0f14 !important; border-right: 1px solid rgba(212, 175, 55, 0.12) !important; }
    .brand-title { font-size: 2.8rem; font-weight: 900; letter-spacing: 2px; color: #d4af37; margin: 0; line-height: 1; text-align: center; }
    .brand-subtitle { font-size: 0.78rem; letter-spacing: 4px; text-transform: uppercase; color: #9e9575; margin-top: 4px; font-weight: 600; text-align: center; margin-bottom: 20px; }
    .glass-card { background: rgba(18, 20, 26, 0.7); border: 1px solid rgba(212, 175, 55, 0.15); border-radius: 14px; padding: 24px; margin-bottom: 20px; }
    .kpi-box { background: #0f1117; border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 20px; text-align: center; }
    .kpi-label { font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #a89f81; margin-bottom: 6px; }
    .kpi-val { font-size: 1.7rem; font-weight: 800; margin: 0; }
    div.stButton > button { background: #d4af37 !important; color: #08090b !important; border: 1px solid #d4af37 !important; border-radius: 8px !important; padding: 10px 20px !important; font-weight: 700 !important; }
    div.stButton > button:hover { background: #e6c35c !important; border-color: #e6c35c !important; color: #000000 !important; }
    .pro-tag { background: rgba(212, 175, 55, 0.15); color: #d4af37; border: 1px solid #d4af37; font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 20px; display: inline-block; }
    .pending-tag { background: rgba(255, 193, 7, 0.15); color: #ffc107; border: 1px solid #ffc107; font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 20px; display: inline-block; }
    
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
</style>
<script>
    const inputs = window.parent.document.querySelectorAll('div[data-baseweb="select"] input');
    inputs.forEach(input => {
        input.setAttribute('readonly', 'readonly');
    });
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

# Banco de dados e sessão
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
if "chat_mensagens" not in st.session_state:
    st.session_state["chat_mensagens"] = []
if "pix_payment_id" not in st.session_state:
    st.session_state["pix_payment_id"] = None
if "pix_qr_base64" not in st.session_state:
    st.session_state["pix_qr_base64"] = ""
if "pix_copia_cola" not in st.session_state:
    st.session_state["pix_copia_cola"] = ""

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
                        "plano": "Gratuito"
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
    st.markdown("<div style='padding: 10px 0 20px 0; text-align: center;'><div class='brand-title' style='font-size: 2.2rem;'>MFC</div><div class='brand-subtitle' style='font-size: 0.65rem;'>MY FINANCIAL CONTROL</div></div>", unsafe_allow_html=True)
    
    badge_html = '<span class="pro-tag">⭐ PLANO PRO</span>' if eh_pro else '<span style="background:#1a1c24; color:#777; font-size:0.72rem; padding:3px 8px; border-radius:4px;">PLANO BÁSICO</span>'
    st.markdown("<div style='background: #11131a; padding: 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 20px;'><div style='font-size: 0.72rem; color: #777; text-transform: uppercase;'>Usuário</div><div style='font-weight: 700; font-size: 1.05rem; color: #ffffff;'>" + str(usuario_atual) + "</div><div style='font-size: 0.75rem; color: #a89f81; margin: 2px 0 10px 0;'>" + str(user_email) + "</div>" + badge_html + "</div>", unsafe_allow_html=True)
    
    rotas_chaves = ["upload", "dashboard", "chat_ia", "planejamento", "assinatura"]
    mapa_titulos = {
        "upload": "📥 Upload de Extratos",
        "dashboard": "📊 Dashboard & Métricas",
        "chat_ia": "💬 Consultor IA (PRO)",
        "planejamento": "🔮 Planejamento Futuro",
        "assinatura": "⭐ Assinatura PRO"
    }
    
    if eh_admin:
        rotas_chaves.append("usuarios")
        mapa_titulos["usuarios"] = "👥 Gestão de Usuários"
        
    menu_selecionado = st.radio("Menu", rotas_chaves, format_func=lambda x: mapa_titulos[x], label_visibility="collapsed")
    st.markdown("---")
        
    if not api_key:
        with st.expander("⚙️ Chave de Integração"):
            api_key = st.text_input("Chave de Acesso", type="password")

    if st.session_state["transacoes"]:
        if st.button("🗑️ Limpar Dados Atuais", use_container_width=True):
            st.session_state["transacoes"] = []
            st.session_state["chat_mensagens"] = []
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
    prompt = "Analise o extrato financeiro e retorne EXCLUSIVAMENTE um array JSON contendo objetos no formato: [{\"data\":\"DD/MM/AAAA\",\"descricao\":\"Nome\",\"tipo\":\"Receita\" ou \"Despesa\",\"valor\":150.50}]. EXTRATO: " + texto_extrato
    
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

# Motor IA para Chat Consultor Financeiro
def responder_chat_consultor(chave_api, transacoes_lista, historico_chat, pergunta_usuario):
    genai.configure(api_key=chave_api)
    
    contexto_financeiro = json.dumps(transacoes_lista, ensure_ascii=False)
    system_instruction = (
        "Você é o Consultor Financeiro Oficial do MFC (My Financial Control). "
        "Seu tom é executivo, direto, analítico e de alto nível (estilo private banker / wealth management). "
        "Você tem acesso total aos lançamentos bancários conciliados do cliente neste JSON: " + contexto_financeiro + ". "
        "Analise esses dados para responder às perguntas do usuário com números exatos, insights de corte de custos, "
        "identificação de gastos invisíveis/supérfluos e recomendações estratégicas de investimento e poupança. "
        "Seja cordial, use formatação em tópicos e valores em R$."
    )
    
    modelos = ["models/gemini-3.6-flash", "gemini-3.6-flash", "models/gemini-2.0-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    
    # Montar histórico em texto
    prompt_conversa = system_instruction + "\n\nHISTÓRICO DA CONVERSA:\n"
    for msg in historico_chat:
        prompt_conversa += f"{msg['role'].upper()}: {msg['content']}\n"
    prompt_conversa += f"USER: {pergunta_usuario}\nASSISTANT:"
    
    for mod in modelos:
        try:
            m = genai.GenerativeModel(model_name=mod)
            res = m.generate_content(prompt_conversa)
            if res and res.text:
                return res.text.strip()
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
        
        df_rec = df_raw[df_raw["tipo"] == "Receita"]
        df_des = df_raw[df_raw["tipo"] == "Despesa"]
        
        total_entradas = float(df_rec["valor"].sum())
        total_saidas = float(df_des["valor"].sum())
        saldo_liquido = total_entradas - total_saidas
        taxa_poupanca = ((saldo_liquido / total_entradas) * 100.0) if total_entradas > 0 else 0.0
        cor_saldo = "#00e676" if saldo_liquido >= 0 else "#ff5252"

        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f"<div class='kpi-box'><div class='kpi-label'>Receitas</div><div class='kpi-val' style='color: #00e676;'>+ R$ {total_entradas:,.2f}</div></div>", unsafe_allow_html=True)
        k2.markdown(f"<div class='kpi-box'><div class='kpi-label'>Despesas</div><div class='kpi-val' style='color: #ff5252;'>- R$ {total_saidas:,.2f}</div></div>", unsafe_allow_html=True)
        k3.markdown(f"<div class='kpi-box'><div class='kpi-label'>Saldo Líquido</div><div class='kpi-val' style='color: {cor_saldo};'>R$ {saldo_liquido:,.2f}</div></div>", unsafe_allow_html=True)
        k4.markdown(f"<div class='kpi-box'><div class='kpi-label'>Taxa de Poupança</div><div class='kpi-val' style='color: #d4af37;'>{taxa_poupanca:.1f}%</div></div>", unsafe_allow_html=True)
        
        st.write("")
        st.write("")
        c_tab, c_graf = st.columns([1.4, 1.0])
        
        with c_tab:
            st.markdown("### 📋 Lançamentos Conciliados")
            
            f1, f2, f3, f4 = st.columns([1.2, 0.9, 0.9, 1.2])
            with f1:
                busca = st.text_input("🔍 Buscar lançamento", placeholder="Nome ou comércio...")
            with f2:
                filtro_tipo = st.selectbox("Tipo", ["Todos", "Receitas", "Despesas"])
            with f3:
                ordem = st.selectbox("Ordenar por", ["Mais Recentes", "Mais Antigos", "Maior Valor", "Menor Valor"])
            with f4:
                min_dt = df_raw["data_dt"].min()
                max_dt = df_raw["data_dt"].max()
                if pd.isna(min_dt) or pd.isna(max_dt):
                    min_val, max_val = datetime.today().date(), datetime.today().date()
                else:
                    min_val, max_val = min_dt.date(), max_dt.date()
                    
                intervalo_data = st.date_input("Período", value=(min_val, max_val), format="DD/MM/YYYY")

            df_filtrado = df_raw.copy()
            
            if busca:
                df_filtrado = df_filtrado[df_filtrado["descricao"].str.contains(busca, case=False, na=False)]
            if filtro_tipo == "Receitas":
                df_filtrado = df_filtrado[df_filtrado["tipo"] == "Receita"]
            elif filtro_tipo == "Despesas":
                df_filtrado = df_filtrado[df_filtrado["tipo"] == "Despesa"]

            if isinstance(intervalo_data, (tuple, list)) and len(intervalo_data) == 2:
                d_ini, d_fim = intervalo_data
                df_filtrado = df_filtrado[(df_filtrado["data_dt"].dt.date >= d_ini) & (df_filtrado["data_dt"].dt.date <= d_fim)]

            if ordem == "Mais Recentes":
                df_filtrado = df_filtrado.sort_values(by="data_dt", ascending=False)
            elif ordem == "Mais Antigos":
                df_filtrado = df_filtrado.sort_values(by="data_dt", ascending=True)
            elif ordem == "Maior Valor":
                df_filtrado = df_filtrado.sort_values(by="valor", ascending=False)
            elif ordem == "Menor Valor":
                df_filtrado = df_filtrado.sort_values(by="valor", ascending=True)

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
            
        with c_graf:
            st.markdown("### 📊 Proporção de Fluxo")
            total_vol = total_entradas + total_saidas
            fig = go.Figure(data=[go.Pie(
                labels=["Receitas", "Despesas"],
                values=[total_entradas, total_saidas],
                hole=0.62,
                marker=dict(colors=["#00e676", "#ff5252"], line=dict(color="#08090b", width=3)),
                textinfo="percent",
                textfont=dict(size=14, color="#ffffff", family="Inter")
            )])
            fig.update_layout(
                paper_bgcolor="#0f1117",
                plot_bgcolor="#0f1117",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(color="#e5e5e5", size=12)),
                annotations=[dict(text=f"<span style='font-size:11px; color:#888;'>TOTAL</span><br><b style='font-size:16px; color:#fff;'>R$ {total_vol:,.2f}</b>", x=0.5, y=0.5, font_size=14, showarrow=False)],
                margin=dict(t=10, b=30, l=10, r=10),
                height=450
            )
            st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 💬 ABA NOVIDADE: CONSULTOR IA (PRO)
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
            
        # Renderizar mensagens anteriores
        for msg in st.session_state["chat_mensagens"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
        # Input do chat
        if prompt_user := st.chat_input("Ex: Quanto gastei com delivery? Como cortar R$ 400 esse mês?"):
            # Adiciona mensagem do usuário
            st.session_state["chat_mensagens"].append({"role": "user", "content": prompt_user})
            with st.chat_message("user"):
                st.markdown(prompt_user)
                
            # Gera resposta da IA
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
# 🔮 ABA 4: PLANEJAMENTO FUTURO
# ==========================================
elif menu_selecionado == "planejamento":
    if not eh_pro:
        st.markdown("<div class='glass-card' style='text-align: center; border: 1px solid #d4af37; padding: 40px 20px;'><div class='pro-tag'>Recurso Exclusivo PRO</div><h2 style='color: #d4af37; margin: 15px 0 10px 0;'>🔮 Planejamento Orçamentário</h2><p style='color: #bbb; max-width: 550px; margin: 0 auto 20px auto; font-size: 0.95rem;'>Projete metas para os próximos meses e acompanhe sua capacidade de investimento.</p><div style='font-size: 1.4rem; color: #00e676; font-weight: 800; margin-bottom: 15px;'>R$ 19,90 / mês</div></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='glass-card'><h2 style='margin:0; color:#d4af37;'>🔮 Planejamento Orçamentário Estratégico</h2></div>", unsafe_allow_html=True)
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("#### 🎯 Metas de Gastos")
            renda_est = st.number_input("Renda Prevista (R$)", value=5000.0, step=200.0)
            teto_gasto = st.number_input("Teto Máximo Desejado (R$)", value=3200.0, step=100.0)
            meta_sobra = renda_est - teto_gasto
            st.markdown(f"<div class='kpi-box' style='margin-top: 15px; text-align: left; border-color: rgba(212,175,55,0.3);'><div class='kpi-label'>Economia Projetada</div><div class='kpi-val' style='color: #00e676;'>R$ {meta_sobra:,.2f}</div><small style='color: #666;'>Capacidade de poupança mensal</small></div>", unsafe_allow_html=True)
        with col_p2:
            st.markdown("#### 💡 Despesas Fixas")
            fixos = st.number_input("Custos Recorrentes", value=1800.0, step=100.0)
            livre_lazer = teto_gasto - fixos
            if livre_lazer > 0:
                st.success(f"Saldo Livre: R$ {livre_lazer:,.2f}")
            else:
                st.error("Atenção: Os custos fixos superam o teto.")

# ==========================================
# ⭐ ABA 5: ASSINATURA PRO (PRODUÇÃO - R$ 19,90)
# ==========================================
elif menu_selecionado == "assinatura":
    st.markdown("<div style='text-align: center; margin-bottom: 30px;'><div class='brand-title' style='font-size: 2.2rem;'>MFC PRO</div><p style='color: #888
