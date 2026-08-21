import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
import json
from pypdf import PdfReader

st.set_page_config(page_title="Gestor Financeiro Inteligente", page_icon="💵", layout="wide")

# --- 1. CONFIGURAÇÃO DE USUÁRIO / AUTENTICAÇÃO SIMPLES ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "transacoes" not in st.session_state:
    st.session_state["transacoes"] = []

def login():
    st.markdown("### 🔐 Acesso ao Gestor Financeiro")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        usuario = st.text_input("Usuario")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            # Usuário e senha padrão configuráveis
            if usuario == "Marcos" and senha == "1234":
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

if not st.session_state["autenticado"]:
    login()
    st.stop()

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("⚙️ Configurações")
    api_key = st.text_input("Gemini API Key (Google AI Studio)", type="password", help="Pegue gratuitamente em aistudio.google.com")
    if st.button("Sair da Conta"):
        st.session_state["autenticado"] = False
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
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    
    return json.loads(response.text)

# --- 3. INTERFACE PRINCIPAL ---
st.title("💵 Painel de Controle Financeiro")

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
        # Formatação
        df["valor"] = pd.to_numeric(df["valor"])
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
        df = df.sort_values(by="data", ascending=False)
        
        total_entradas = df[df["tipo"] == "Receita"]["valor"].sum()
        total_saidas = df[df["tipo"] == "Despesa"]["valor"].sum()
        saldo_liquido = total_entradas - total_saidas
        taxa_poupanca = ((saldo_liquido / total_entradas) * 100) if total_entradas > 0 else 0
        
        # Cards de KPI
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total de Entradas", f"R$ {total_entradas:,.2f}")
        c2.metric("Total de Saídas", f"R$ {total_saidas:,.2f}")
        c3.metric("Saldo Líquido", f"R$ {saldo_liquido:,.2f}", delta=f"{saldo_liquido:,.2f}")
        c4.metric("Taxa de Poupança", f"{taxa_poupanca:.1f}%")
        
        st.markdown("---")
        
        # Gráficos
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            df_despesas = df[df["tipo"] == "Despesa"]
            if not df_despesas.empty:
                fig_pie = px.pie(df_despesas, names="categoria", values="valor", title="Distribuição de Despesas por Categoria", hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_g2:
            fig_bar = px.bar(df, x="tipo", y="valor", color="tipo", title="Comparativo Entradas vs Saídas", text_auto=True)
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
        
        st.metric("Margem / Economia Projetada", f"R$ {meta_poupanca:,.2f}")
    
    with col_p2:
        st.markdown("#### 💡 Simulação de Gastos Fixos")
        gastos_fixos = st.number_input("Contas Fixas (Aluguel, Luz, Internet, etc.)", value=1200.0, step=50.0)
        limite_lazer = teto_gastos - gastos_fixos
        
        if limite_lazer > 0:
            st.success(f"Você terá livre para gastos variáveis (Lazer/Alimentação): **R$ {limite_lazer:,.2f}**")
        else:
            st.error("Atenção: Suas contas fixas estão ultrapassando o teto desejado!")
