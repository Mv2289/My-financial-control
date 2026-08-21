import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google import genai
import json
from pypdf import PdfReader

st.set_page_config(page_title="Gestor Financeiro Inteligente", page_icon="💵", layout="wide")

# --- PALETA DE CORES DA SUA PLANILHA (CSS PERSONALIZADO) ---
st.markdown("""
<style>
    /* Fundo geral e fontes */
    .stApp {
        background-color: #121212;
        color: #F3E5AB;
    }
    
    /* Barra Lateral */
    section[data-testid="stSidebar"] {
        background-color: #1A1A1A;
        border-right: 1px solid #2A2415;
    }
    
    /* Títulos e Cabeçalhos */
    h1, h2, h3, h4, h5, h6 {
        color: #D4AF37 !important;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Abas / Tabs */
    button[data-baseweb="tab"] {
        color: #CCCCCC !important;
        background-color: transparent !important;
    }
    button[aria-selected="true"] {
        color: #D4AF37 !important;
        border-bottom-color: #D4AF37 !important;
        font-weight: bold;
    }
    
    /* Cards de Métricas / KPIs */
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        border: 1px solid #2A2415;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.4);
    }
    div[data-testid="stMetricLabel"] p {
        color: #C5A059 !important;
        font-size: 0.95rem !important;
        font-weight: bold;
    }
    div[data-testid="stMetricValue"] div {
        color: #FFFFFF !important;
        font-weight: bold;
    }
    
    /* Botões */
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
    
    /* Inputs */
    input, textarea, select {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. GERENCIAMENTO DE USUÁRIOS E SESSÃO ---
if "usuarios" not in st.session_state:
    st.session_state["usuarios"] = {
        "admin": "admin123",
        "Marcos": "1234"
    }

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""
if "transacoes" not in st.session_state:
    st.session_state["transacoes"] = []

def tela_autenticacao():
    st.markdown("<h2 style='text-align: center; color: #D4AF37;'>💵 PAINEL DE CONTROLE FINANCEIRO</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #F3E5AB;'>Gerenciamento e análise de gastos</p>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        aba_login, aba_cadastro = st.tabs(["🔑 Entrar", "📝 Criar Conta"])
        
        with aba_login:
            st.subheader("Acesse sua conta")
            usuario = st.text_input("Usuário", key="login_user")
            senha = st.text_input("Senha", type="password", key="login_pass")
            
            if st.button("Entrar", use_container_width=True):
                if usuario in st.session_state["usuarios"] and st.session_state["usuarios"][usuario] == senha:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_logado"] = usuario
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
                    
        with aba_cadastro:
            st.subheader("Novo Cadastro")
            novo_usuario = st.text_input("Escolha um Nome de Usuário", key="cad_user")
            nova_senha = st.text_input("Crie uma Senha", type="password", key="cad_pass")
            confirma_senha = st.text_input("Confirme sua Senha", type="password", key="cad_pass_conf")
            
            if st.button("Cadastrar", use_container_width=True):
                if not novo_usuario or not nova_senha:
                    st.warning("Preencha todos os campos.")
                elif novo_usuario in st.session_state["usuarios"]:
                    st.error("Este nome de usuário já existe.")
                elif nova_senha != confirma_senha:
                    st.error("As senhas não coincidem.")
                else:
                    st.session_state["usuarios"][novo_usuario] = nova_senha
                    st.success("Conta criada com sucesso! Acesse na aba 'Entrar'.")

if not st.session_state["autenticado"]:
    tela_autenticacao()
    st.stop()

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['usuario_logado']}")
    if st.session_state["usuario_logado"] == "admin":
        st.caption("🛡️ Perfil: Administrador")
        with st.expander("👥 Usuários Cadastrados"):
            st.write(list(st.session_state["usuarios"].keys()))
            
    st.markdown("---")
    st.subheader("⚙️ Configurações de IA")
    api_key = st.text_input("Gemini API Key", type="password", help="Pegue gratuitamente em aistudio.google.com")
    
    st.markdown("---")
    if st.button("Sair da Conta", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.rerun()

# --- 2. FUNÇÃO PARA LER EXTRATO COM GEMINI ---
def processar_extrato_pdf(file, chave_api):
    reader = PdfReader(file)
    texto_extrato = ""
    for page in reader.pages:
        texto_extrato += page.extract_text() or ""
        
    client = genai.Client(api_key=chave_api)
    
    prompt = f"""
    Você é um assistente financeiro especialista. Analise o extrato bancário abaixo e extraia TODAS as transações.
    Retorne EXCLUSIVAMENTE um array JSON contendo objetos com os seguintes campos:
    - "data": string (formato DD/MM/AAAA)
    - "descricao": string (nome da pessoa, loja ou serviço)
    - "tipo": string ("Receita" para entradas/rendimentos ou "Despesa" para pagamentos/débitos/saídas)
    - "categoria": string (escolha entre: Alimentação, Transporte, Lazer / Outros, Cartão de credito, Salário, Investimento, Vendas, Conta Mensal)
    - "valor": float (valor numérico positivo com ponto, ex: 35.50)

    EXTRATO:
    {texto_extrato}
    """
    
    # Modelos prioritários aceitos pelo Google AI Studio
    modelos = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-exp",
        "gemini-2.5-pro"
    ]
    
    # Tenta descobrir os modelos disponíveis na conta dinamicamente
    try:
        modelos_disponiveis = [m.name.replace("models/", "") for m in client.models.list()]
        modelos = [m for m in modelos if m in modelos_disponiveis] + modelos_disponiveis
    except Exception:
        pass

    response = None
    ultimo_erro = None
    
    for modelo in modelos:
        try:
            response = client.models.generate_content(
                model=modelo,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            if response and response.text:
                break
        except Exception as e:
            ultimo_erro = e
            continue
            
    if response is None:
        raise ultimo_erro
        
    return json.loads(response.text)
# --- 3. INTERFACE PRINCIPAL ---
st.markdown("<h2 style='color: #D4AF37;'>💵 PAINEL DE CONTROLE FINANCEIRO</h2>", unsafe_allow_html=True)

tab_upload, tab_dashboard, tab_planejamento = st.tabs([
    "📥 Upload de Extratos", 
    "📊 Resumo de Gastos", 
    "🔮 Planejamento Futuro"
])

# --- ABA 1: UPLOAD DE EXTRATO ---
with tab_upload:
    st.subheader("Suba o extrato bancário em PDF")
    st.info("Envie o PDF de qualquer banco (PicPay, Nubank, Itaú, etc.). A IA fará a leitura e classificação automática.")
    
    uploaded_file = st.file_uploader("Selecione o arquivo PDF do extrato", type=["pdf"])
    
    if uploaded_file and st.button("Processar Extrato com IA", use_container_width=True):
        if not api_key:
            st.error("Por favor, insira sua chave da Gemini API na barra lateral.")
        else:
            with st.spinner("Lendo e categorizando lançamentos..."):
                try:
                    novos_dados = processar_extrato_pdf(uploaded_file, api_key)
                    st.session_state["transacoes"].extend(novos_dados)
                    st.success(f"Sucesso! {len(novos_dados)} transações importadas.")
                except Exception as e:
                    st.error(f"Erro ao processar arquivo: {e}")

# --- PREPARAÇÃO DOS DADOS ---
df = pd.DataFrame(st.session_state["transacoes"])

# --- ABA 2: RESUMO E DASHBOARD ---
with tab_dashboard:
    if df.empty:
        st.warning("Nenhuma movimentação cadastrada. Suba um extrato na aba 'Upload de Extratos'.")
    else:
        df["valor"] = pd.to_numeric(df["valor"])
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
        df = df.sort_values(by="data", ascending=False)
        
        total_entradas = df[df["tipo"] == "Receita"]["valor"].sum()
        total_saidas = df[df["tipo"] == "Despesa"]["valor"].sum()
        saldo_liquido = total_entradas - total_saidas
        taxa_poupanca = ((saldo_liquido / total_entradas) * 100) if total_entradas > 0 else 0
        
        # Cards de KPI com cores personalizadas
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"""
            <div style="background-color: #1E1E1E; border: 1px solid #2A2415; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="color: #C5A059; margin: 0; font-weight: bold;">RECEITAS 💰</p>
                <h3 style="color: #00B050 !important; margin: 5px 0 0 0;">R$ {total_entradas:,.2f}</h3>
            </div>
        """, unsafe_allow_html=True)
        
        c2.markdown(f"""
            <div style="background-color: #1E1E1E; border: 1px solid #2A2415; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="color: #C5A059; margin: 0; font-weight: bold;">DESPESAS 💸</p>
                <h3 style="color: #FF5252 !important; margin: 5px 0 0 0;">R$ {total_saidas:,.2f}</h3>
            </div>
        """, unsafe_allow_html=True)
        
        c3.markdown(f"""
            <div style="background-color: #1E1E1E; border: 1px solid #2A2415; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="color: #C5A059; margin: 0; font-weight: bold;">SALDO LÍQUIDO</p>
                <h3 style="color: {'#00B050' if saldo_liquido >= 0 else '#FF5252'} !important; margin: 5px 0 0 0;">R$ {saldo_liquido:,.2f}</h3>
            </div>
        """, unsafe_allow_html=True)
        
        c4.markdown(f"""
            <div style="background-color: #1E1E1E; border: 1px solid #2A2415; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="color: #C5A059; margin: 0; font-weight: bold;">TAXA DE POUPANÇA</p>
                <h3 style="color: #D4AF37 !important; margin: 5px 0 0 0;">{taxa_poupanca:.1f}%</h3>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gráficos na paleta Dark & Gold
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            df_despesas = df[df["tipo"] == "Despesa"]
            if not df_despesas.empty:
                fig_pie = px.pie(
                    df_despesas, 
                    names="categoria", 
                    values="valor", 
                    title="Distribuição de Despesas por Categoria",
                    hole=0.45,
                    color_discrete_sequence=['#D4AF37', '#FF5252', '#E67E22', '#3498DB', '#9B59B6', '#1ABC9C', '#F39C12']
                )
                fig_pie.update_layout(
                    paper_bgcolor="#1E1E1E",
                    plot_bgcolor="#1E1E1E",
                    font=dict(color="#F3E5AB"),
                    title_font=dict(color="#D4AF37", size=16),
                    legend=dict(font=dict(color="#F3E5AB"))
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_g2:
            fig_bar = px.bar(
                df, 
                x="tipo", 
                y="valor", 
                color="tipo", 
                title="Comparativo Entradas vs Saídas", 
                text_auto=True,
                color_discrete_map={"Receita": "#00B050", "Despesa": "#FF5252"}
            )
            fig_bar.update_layout(
                paper_bgcolor="#1E1E1E",
                plot_bgcolor="#1E1E1E",
                font=dict(color="#F3E5AB"),
                title_font=dict(color="#D4AF37", size=16),
                xaxis=dict(color="#F3E5AB", gridcolor="#2A2415"),
                yaxis=dict(color="#F3E5AB", gridcolor="#2A2415"),
                showlegend=False
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
        st.subheader("📋 Tabela de Lançamentos")
        st.dataframe(df, use_container_width=True)

# --- ABA 3: PLANEJAMENTO FUTURO ---
with tab_planejamento:
    st.subheader("🎯 Metas e Projeção de Gastos")
    
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
