import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pypdf import PdfReader

st.set_page_config(page_title="Gestor Financeiro Inteligente", page_icon="💵", layout="wide")

# --- PALETA DE CORES DARK & GOLD (PLANILHA) ---
st.markdown("""
<style>
    .stApp {
        background-color: #121212;
        color: #F3E5AB;
    }
    section[data-testid="stSidebar"] {
        background-color: #1A1A1A;
        border-right: 1px solid #2A2415;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #D4AF37 !important;
        font-family: 'Segoe UI', sans-serif;
    }
    button[data-baseweb="tab"] {
        color: #CCCCCC !important;
        background-color: transparent !important;
    }
    button[aria-selected="true"] {
        color: #D4AF37 !important;
        border-bottom-color: #D4AF37 !important;
        font-weight: bold;
    }
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        border: 1px solid #2A2415;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.4);
    }
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
    input, textarea, select {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÃO PARA ENVIO DE E-MAIL DE BOAS-VINDAS ---
def enviar_email_boas_vindas(destinatario_email, nome_usuario):
    remetente = st.secrets.get("EMAIL_REMETENTE", "")
    senha_remetente = st.secrets.get("EMAIL_SENHA", "")
    
    # Se as credenciais estiverem configuradas nos secrets do Streamlit
    if remetente and senha_remetente:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "🚀 Bem-vindo ao seu Gestor Financeiro Inteligente!"
            msg["From"] = f"Gestor Financeiro <{remetente}>"
            msg["To"] = destinatario_email
            
            html = f"""
            <div style="font-family: Arial, sans-serif; background-color: #121212; color: #F3E5AB; padding: 25px; border-radius: 10px; border: 1px solid #D4AF37;">
                <h2 style="color: #D4AF37;">Olá, {nome_usuario}! 👋</h2>
                <p>Sua conta no <b>Gestor Financeiro Inteligente</b> foi criada com sucesso.</p>
                <p>Agora você pode subir seus extratos bancários em PDF para ter uma visão completa das suas receitas, despesas e projeção financeira.</p>
                <br>
                <a href="https://share.streamlit.io" style="background-color: #D4AF37; color: #121212; padding: 10px 20px; text-decoration: none; font-weight: bold; border-radius: 5px;">Acessar Meu Painel</a>
                <br><br>
                <small style="color: #888888;">Mensagem automática gerada pelo Gestor Financeiro.</small>
            </div>
            """
            msg.attach(MIMEText(html, "html"))
            
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
                servidor.login(remetente, senha_remetente)
                servidor.sendmail(remetente, destinatario_email, msg.as_string())
            return True, "E-mail de boas-vindas enviado com sucesso!"
        except Exception as e:
            return False, f"Conta criada, mas ocorreu um erro no envio do e-mail: {e}"
    else:
        return True, "Conta criada! (Configure EMAIL_REMETENTE e EMAIL_SENHA nos Secrets para disparo real)."

# --- 1. GERENCIAMENTO DE USUÁRIOS, PLANOS E SESSÃO ---
if "usuarios_db" not in st.session_state:
    st.session_state["usuarios_db"] = {
        "admin": {"email": "admin@gestor.com", "senha": "admin123", "plano": "Pro"},
        "Marcos": {"email": "marcos@gestor.com", "senha": "1234", "plano": "Pro"}
    }

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""
if "transacoes" not in st.session_state:
    st.session_state["transacoes"] = []

def tela_autenticacao():
    st.markdown("<h2 style='text-align: center; color: #D4AF37;'>💵 PAINEL DE CONTROLE FINANCEIRO</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #F3E5AB;'>Gerenciamento e análise inteligente de extratos</p>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        aba_login, aba_cadastro = st.tabs(["🔑 Entrar", "📝 Criar Conta"])
        
        with aba_login:
            st.subheader("Acesse sua conta")
            usuario = st.text_input("Usuário", key="login_user")
            senha = st.text_input("Senha", type="password", key="login_pass")
            
            if st.button("Entrar", use_container_width=True):
                if usuario in st.session_state["usuarios_db"] and st.session_state["usuarios_db"][usuario]["senha"] == senha:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_logado"] = usuario
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
                    
        with aba_cadastro:
            st.subheader("Novo Cadastro")
            novo_usuario = st.text_input("Nome de Usuário", key="cad_user")
            novo_email = st.text_input("E-mail", placeholder="seuemail@exemplo.com", key="cad_email")
            nova_senha = st.text_input("Senha", type="password", key="cad_pass")
            confirma_senha = st.text_input("Confirme sua Senha", type="password", key="cad_pass_conf")
            
            if st.button("Cadastrar", use_container_width=True):
                if not novo_usuario or not novo_email or not nova_senha:
                    st.warning("Preencha todos os campos (Nome, E-mail e Senha).")
                elif "@" not in novo_email or "." not in novo_email:
                    st.error("Por favor, insira um e-mail válido.")
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
                    sucesso_email, msg_email = enviar_email_boas_vindas(novo_email, novo_usuario)
                    st.success(f"🎉 Conta criada com sucesso para **{novo_usuario}**! {msg_email}")

if not st.session_state["autenticado"]:
    tela_autenticacao()
    st.stop()

# Recupera dados do usuário logado
usuario_atual = st.session_state.get("usuario_logado", "")
dados_usuario = st.session_state["usuarios_db"].get(usuario_atual, {"plano": "Gratuito", "email": ""})
plano_atual = dados_usuario.get("plano", "Gratuito")
eh_pro = (plano_atual == "Pro")

# --- GESTÃO DA CHAVE DE API ---
api_key = ""
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown(f"### 👤 {usuario_atual}")
    st.caption(f"📧 {dados_usuario.get('email', '')}")
    if eh_pro:
        st.markdown("<span style='background-color:#2A2415; color:#D4AF37; padding:4px 8px; border-radius:6px; border:1px solid #D4AF37; font-weight:bold;'>⭐ Plano PRO</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='background-color:#222222; color:#AAAAAA; padding:4px 8px; border-radius:6px; border:1px solid #444444;'>Plano Básico (Gratuito)</span>", unsafe_allow_html=True)
    
    if usuario_atual == "admin":
        st.markdown("---")
        st.caption("🛡️ Painel do Administrador")
        with st.expander("👥 Gerenciar Usuários & Planos"):
            for u, dados in list(st.session_state["usuarios_db"].items()):
                col_u1, col_u2 = st.columns([2, 1])
                col_u1.write(f"**{u}**\n*{dados.get('email','')}* ({dados['plano']})")
                if dados["plano"] == "Gratuito":
                    if col_u2.button("Virar Pro", key=f"btn_pro_{u}"):
                        st.session_state["usuarios_db"][u]["plano"] = "Pro"
                        st.rerun()
                else:
                    if u != "admin" and col_u2.button("Downgrade", key=f"btn_down_{u}"):
                        st.session_state["usuarios_db"][u]["plano"] = "Gratuito"
                        st.rerun()

    st.markdown("---")
    
    if not api_key:
        st.subheader("⚙️ Configurações de IA")
        api_key = st.text_input("Gemini API Key", type="password", help="Pegue gratuitamente em aistudio.google.com")
        st.markdown("---")
    
    if st.session_state["transacoes"]:
        if st.button("🗑️ Limpar Transações Atuais", use_container_width=True):
            st.session_state["transacoes"] = []
            st.rerun()
        st.markdown("---")
        
    if st.button("Sair da Conta", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.rerun()

# --- 2. FUNÇÃO INTELIGENTE PARA LER EXTRATO COM GEMINI ---
def processar_extrato_pdf(file, chave_api):
    reader = PdfReader(file)
    texto_extrato = ""
    for page in reader.pages:
        texto_extrato += page.extract_text() or ""
        
    if not texto_extrato.strip():
        raise Exception("Não foi possível extrair texto do PDF. O arquivo pode ser uma imagem escaneada.")

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
    
    candidatos = [m for m in preferencias if m in modelos_disponiveis]
    if not candidatos:
        candidatos = modelos_disponiveis if modelos_disponiveis else ["gemini-2.5-flash", "gemini-2.0-flash"]

    prompt = f"""
    Você é um assistente financeiro especialista. Analise o extrato bancário abaixo e extraia TODAS as transações.
    Retorne EXCLUSIVAMENTE um array JSON contendo objetos com os seguintes campos:
    - "data": string (formato DD/MM/AAAA)
    - "descricao": string (nome da pessoa, loja ou serviço)
    - "tipo": string ("Receita" para entradas/rendimentos ou "Despesa" para pagamentos/débitos/saídas)
    - "valor": float (valor numérico positivo com ponto, ex: 35.50)

    EXTRATO:
    {texto_extrato}
    """
    
    response = None
    ultimo_erro = None
    
    for modelo_escolhido in candidatos:
        try:
            model = genai.GenerativeModel(
                model_name=modelo_escolhido,
                generation_config={"response_mime_type": "application/json"}
            )
            response = model.generate_content(prompt)
            if response and response.text:
                break
        except Exception as e:
            ultimo_erro = e
            continue
            
    if response is None:
        raise ultimo_erro
    
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

tab_upload, tab_dashboard, tab_planejamento, tab_assinatura = st.tabs([
    "📥 Upload de Extratos", 
    "📊 Resumo e Gráficos", 
    "🔮 Planejamento Futuro",
    "⭐ Assinatura PRO"
])

# --- ABA 1: UPLOAD DE EXTRATOS ---
with tab_upload:
    st.subheader("Suba seus extratos bancários em PDF")
    
    if eh_pro:
        st.info("⭐ **Modo PRO Ativo:** Você pode selecionar e enviar múltiplos arquivos PDF simultaneamente.")
        uploaded_files = st.file_uploader("Selecione um ou mais arquivos PDF", type=["pdf"], accept_multiple_files=True)
    else:
        st.info("ℹ️ **Plano Básico:** Upload limitado a 1 extrato por vez. Para enviar múltiplos extratos juntos, assine o plano PRO.")
        uploaded_single = st.file_uploader("Selecione o arquivo PDF do extrato", type=["pdf"], accept_multiple_files=False)
        uploaded_files = [uploaded_single] if uploaded_single else []

    if uploaded_files and st.button("Processar Extrato(s) com IA", use_container_width=True):
        if not api_key:
            st.error("Chave de API não configurada. Salve nos Secrets do Streamlit ou informe na barra lateral.")
        else:
            novas_transacoes = []
            with st.spinner(f"Processando {len(uploaded_files)} arquivo(s)..."):
                for file in uploaded_files:
                    try:
                        dados = processar_extrato_pdf(file, api_key)
                        novas_transacoes.extend(dados)
                    except Exception as e:
                        st.error(f"Erro ao processar '{file.name}': {e}")
                
                if novas_transacoes:
                    st.session_state["transacoes"].extend(novas_transacoes)
                    st.success(f"Sucesso! {len(novas_transacoes)} transações importadas no total. Acesse a aba 'Resumo e Gráficos'.")

# --- PROCESSAMENTO DOS DADOS ---
df = pd.DataFrame(st.session_state["transacoes"])

# --- ABA 2: RESUMO E DASHBOARD ---
with tab_dashboard:
    if df.empty:
        st.warning("⚠️ Nenhuma movimentação cadastrada ainda. Suba um extrato em PDF na aba 'Upload de Extratos'.")
    else:
        df["valor"] = pd.to_numeric(df["valor"])
        df["data_dt"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
        df = df.sort_values(by="data_dt", ascending=False)
        
        total_entradas = df[df["tipo"] == "Receita"]["valor"].sum()
        total_saidas = df[df["tipo"] == "Despesa"]["valor"].sum()
        saldo_liquido = total_entradas - total_saidas
        taxa_poupanca = ((saldo_liquido / total_entradas) * 100) if total_entradas > 0 else 0
        
        # Cards de KPIs
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"""
            <div style="background-color: #1E1E1E; border: 1px solid #2A2415; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="color: #C5A059; margin: 0; font-weight: bold; font-size: 0.9rem;">RECEITAS (ENTRADAS) 💰</p>
                <h3 style="color: #00B050 !important; margin: 5px 0 0 0;">+ R$ {total_entradas:,.2f}</h3>
            </div>
        """, unsafe_allow_html=True)
        
        c2.markdown(f"""
            <div style="background-color: #1E1E1E; border: 1px solid #2A2415; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="color: #C5A059; margin: 0; font-weight: bold; font-size: 0.9rem;">DESPESAS (SAÍDAS) 💸</p>
                <h3 style="color: #FF5252 !important; margin: 5px 0 0 0;">- R$ {total_saidas:,.2f}</h3>
            </div>
        """, unsafe_allow_html=True)
        
        c3.markdown(f"""
            <div style="background-color: #1E1E1E; border: 1px solid #2A2415; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="color: #C5A059; margin: 0; font-weight: bold; font-size: 0.9rem;">SALDO LÍQUIDO</p>
                <h3 style="color: {'#00B050' if saldo_liquido >= 0 else '#FF5252'} !important; margin: 5px 0 0 0;">R$ {saldo_liquido:,.2f}</h3>
            </div>
        """, unsafe_allow_html=True)
        
        c4.markdown(f"""
            <div style="background-color: #1E1E1E; border: 1px solid #2A2415; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="color: #C5A059; margin: 0; font-weight: bold; font-size: 0.9rem;">TAXA DE POUPANÇA</p>
                <h3 style="color: #D4AF37 !important; margin: 5px 0 0 0;">{taxa_poupanca:.1f}%</h3>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Tabela com Cores
        st.subheader("📋 Transações do Extrato")
        df_exibicao = df.copy()
        df_exibicao["valor_numerico"] = df_exibicao.apply(
            lambda row: row["valor"] if row["tipo"] == "Receita" else -row["valor"], axis=1
        )
        
        df_tabela = df_exibicao[["data", "descricao", "valor_numerico"]].rename(
            columns={
                "data": "Data da Transação",
                "descricao": "Descrição",
                "valor_numerico": "Valor (R$)"
            }
        )
        
        def estilo_valor(val):
            if val > 0:
                return 'color: #00B050; font-weight: bold;'
            elif val < 0:
                return 'color: #FF5252; font-weight: bold;'
            return 'color: #F3E5AB;'

        st.dataframe(
            df_tabela.style
                .format({"Valor (R$)": lambda x: f"+ R$ {x:,.2f}" if x > 0 else f"- R$ {abs(x):,.2f}"})
                .map(estilo_valor, subset=["Valor (R$)"]),
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gráfico Comparativo
        st.subheader("📊 Análise Gráfica: Fluxo Financeiro")
        col_graf_centro, col_graf_vazia = st.columns([2, 1])
        with col_graf_centro:
            total_movimentado = total_entradas + total_saidas
            fig = go.Figure(data=[go.Pie(
                labels=["Entradas (Receitas)", "Saídas (Despesas)"],
                values=[total_entradas, total_saidas],
                hole=0.55,
                marker=dict(
                    colors=["#00B050", "#FF5252"],
                    line=dict(color="#121212", width=3)
                ),
                textinfo="percent+label",
                textposition="outside",
                textfont=dict(size=14, color="#F3E5AB", family="Segoe UI"),
                hovertemplate="<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Proporção: %{percent}<extra></extra>"
            )])
            
            fig.update_layout(
                paper_bgcolor="#1E1E1E",
                plot_bgcolor="#1E1E1E",
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.15,
                    xanchor="center",
                    x=0.5,
                    font=dict(color="#F3E5AB", size=13)
                ),
                annotations=[
                    dict(
                        text=f"<span style='font-size:12px; color:#C5A059;'>Total Movimentado</span><br><b style='font-size:16px; color:#FFFFFF;'>R$ {total_movimentado:,.2f}</b>",
                        x=0.5, y=0.5,
                        font_size=14,
                        showarrow=False
                    )
                ],
                margin=dict(t=30, b=50, l=20, r=20),
                height=450
            )
            st.plotly_chart(fig, use_container_width=True)

# --- ABA 3: PLANEJAMENTO FUTURO (EXCLUSIVO PRO) ---
with tab_planejamento:
    if not eh_pro:
        st.markdown(f"""
            <div style="background-color: #1E1E1E; border: 1px solid #D4AF37; padding: 30px; border-radius: 12px; text-align: center;">
                <h3 style="color: #D4AF37 !important;">🔒 Recurso Exclusivo do Plano PRO</h3>
                <p style="color: #F3E5AB; font-size: 1.05rem;">
                    A ferramenta de <b>Planejamento e Margem Futura</b> é reservada para assinantes PRO.<br>
                    Defina tetos de gastos, projete custos fixos e acompanhe sua meta de economia mensal.
                </p>
                <p style="color: #00B050; font-size: 1.2rem; font-weight: bold;">Apenas R$ 19,90 / mês</p>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("👉 Quero Desbloquear o Plano PRO Agora", use_container_width=True):
            st.info("Vá até a aba **'⭐ Assinatura PRO'** para ativar o seu acesso!")
    else:
        st.subheader("🎯 Metas e Projeção de Gastos (PRO)")
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            renda_prevista = st.number_input("Renda Prevista para o Próximo Mês (R$)", value=4000.0, step=100.0)
            teto_gastos = st.number_input("Teto Máximo de Gastos Desejado (R$)", value=2500.0, step=100.0)
            meta_poupanca = renda_prevista - teto_gastos
            
            st.markdown(f"""
                <div style="background-color: #1E1E1E; border: 1px solid #2A2415; padding: 15px; border-radius: 10px; margin-top: 15px;">
                    <p style="color: #C5A059; margin: 0; font-weight: bold;">Margem / Economia Projetada</p>
                    <h3 style="color: #00B050 !important; margin: 5px 0 0 0;">R$ {meta_poupanca:,.2f}</h3>
                </div>
            """, unsafe_allow_html=True)
        
        with col_p2:
            st.markdown("#### 💡 Simulação de Gastos Fixos")
            gastos_fixos = st.number_input("Contas Fixas (Aluguel, Luz, Internet, etc.)", value=1200.0, step=50.0)
            limite_lazer = teto_gastos - gastos_fixos
            
            if limite_lazer > 0:
                st.success(f"Você terá livre para gastos variáveis (Lazer/Alimentação): **R$ {limite_lazer:,.2f}**")
            else:
                st.error("Atenção: Suas contas fixas estão ultrapassando o teto desejado!")

# --- ABA 4: ASSINATURA PRO ---
with tab_assinatura:
    st.subheader("⭐ Planos & Assinatura")
    
    col_card1, col_card2 = st.columns(2)
    
    with col_card1:
        st.markdown("""
            <div style="background-color: #1A1A1A; border: 1px solid #333333; padding: 20px; border-radius: 10px; height: 100%;">
                <h3 style="color: #CCCCCC !important; margin-top:0;">Plano Básico</h3>
                <h2 style="color: #FFFFFF !important;">Grátis</h2>
                <ul style="color: #AAAAAA; line-height: 1.8;">
                    <li>Upload de 1 extrato por vez</li>
                    <li>Resumo de entradas e saídas</li>
                    <li>Tabela com valores coloridos</li>
                    <li>Gráfico de fluxo financeiro</li>
                    <li><strike>Upload múltiplo de extratos</strike></li>
                    <li><strike>Aba de Planejamento Futuro</strike></li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        
    with col_card2:
        st.markdown("""
            <div style="background-color: #1E1E1E; border: 2px solid #D4AF37; padding: 20px; border-radius: 10px; height: 100%;">
                <h3 style="color: #D4AF37 !important; margin-top:0;">Plano PRO ⭐</h3>
                <h2 style="color: #00B050 !important;">R$ 19,90 <span style="font-size: 1rem; color: #F3E5AB;">/ mês</span></h2>
                <ul style="color: #F3E5AB; line-height: 1.8;">
                    <li><b>Upload ilimitado de múltiplos PDFs simultâneos</b></li>
                    <li><b>Acesso completo à aba de Planejamento Futuro</b></li>
                    <li>Consolidação de múltiplos bancos/cartões</li>
                    <li>Metas de gastos e projeção de economia</li>
                    <li>Suporte prioritário e novidades em primeira mão</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if not eh_pro:
        st.subheader("💳 Assinar o Plano PRO")
        st.markdown("Escolha a forma de pagamento e ative o seu plano instantaneamente:")
        
        col_pag1, col_pag2 = st.columns(2)
        with col_pag1:
            st.markdown("#### ⚡ Pix Instantâneo")
            st.info("Chave Pix de Pagamento: `financeiro@seusite.com` (Valor: R$ 19,90)")
            if st.button("✅ Confirmar Pagamento Pix e Ativar PRO", use_container_width=True):
                st.session_state["usuarios_db"][usuario_atual]["plano"] = "Pro"
                st.success("🎉 Parabéns! Sua assinatura PRO foi ativada com sucesso.")
                st.rerun()
                
        with col_pag2:
            st.markdown("#### 💳 Cartão de Crédito")
            st.text_input("Número do Cartão", placeholder="0000 0000 0000 0000")
            col_v1, col_v2 = st.columns(2)
            col_v1.text_input("Validade", placeholder="MM/AA")
            col_v2.text_input("CVV", type="password", placeholder="123")
            if st.button("Pagar R$ 19,90 e Assinar", use_container_width=True):
                st.session_state["usuarios_db"][usuario_atual]["plano"] = "Pro"
                st.success("🎉 Pagamento aprovado! Sua conta agora é PRO.")
                st.rerun()
    else:
        st.success("✅ Você já é um assinante PRO ativo! Aproveite todos os recursos liberados.")
