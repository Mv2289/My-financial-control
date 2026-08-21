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
    page_title="MVPC Financial | Gestão Inteligente",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PALETA DARK & NOBLE GOLD (DESIGN SAAS PREMIUM) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background-color: #0d0e12;
        color: #f1e6b8;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #12141a !important;
        border-right: 1px solid rgba(212, 175, 55, 0.15);
    }
    
    /* Headers & Títulos */
    h1, h2, h3, h4 {
        color: #d4af37 !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }

    /* Hero Banner */
    .hero-box {
        background: linear-gradient(135deg, rgba(26,29,38,0.9) 0%, rgba(18,20,26,0.95) 100%);
        border: 1px solid rgba(212, 175, 55, 0.25);
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }

    /* Metric Cards */
    .kpi-card {
        background: linear-gradient(180deg, #181b24 0%, #12141c 100%);
        border: 1px solid rgba(212, 175, 55, 0.18);
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        border-color: #d4af37;
    }
    .kpi-title {
        color: #c5a059;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 1.65rem;
        font-weight: 800;
        margin: 0;
    }

    /* Botões Modernos */
    div.stButton > button {
        background: linear-gradient(135deg, #242014 0%, #15140d 100%) !important;
        color: #d4af37 !important;
        border: 1px solid #d4af37 !important;
        border-radius: 10px !important;
        padding: 10px 24px !important;
        font-weight: 700 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.1) !important;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #d4af37 0%, #aa8520 100%) !important;
        color: #0d0e12 !important;
        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.35) !important;
        transform: scale(1.02);
    }

    /* Planos Cards */
    .plan-card {
        background: #141720;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 30px;
        height: 100%;
        position: relative;
    }
    .plan-card-pro {
        background: linear-gradient(180deg, #1d1b14 0%, #13141a 100%);
        border: 2px solid #d4af37;
        box-shadow: 0 12px 35px rgba(212, 175, 55, 0.15);
    }
    .badge-pro {
        background: linear-gradient(90deg, #d4af37, #f3e5ab);
        color: #000;
        font-weight: 800;
        font-size: 0.75rem;
        padding: 4px 12px;
        border-radius: 20px;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 12px;
    }

    /* Inputs */
    input, textarea, select {
        background-color: #161922 !important;
        color: #ffffff !important;
        border: 1px solid #2a2e3d !important;
        border-radius: 8px !important;
    }
    input:focus {
        border-color: #d4af37 !important;
    }

    /* Dataframe / Tabela */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(212, 175, 55, 0.15);
        border-radius: 12px;
        overflow: hidden;
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
            msg["Subject"] = "👑 Acesso Liberado | MVPC Financial"
            msg["From"] = f"MVPC Financial <{remetente}>"
            msg["To"] = destinatario_email
            
            html = f"""
            <div style="background-color:#0d0e12; color:#f1e6b8; padding:35px; border-radius:14px; border:1px solid #d4af37; font-family:'Segoe UI', sans-serif;">
                <h2 style="color:#d4af37; margin-top:0;">Bem-vindo ao MVPC Financial, {nome_usuario}! 🚀</h2>
                <p style="font-size:15px; line-height:1.6; color:#dedede;">Sua conta foi ativada com sucesso no gestor financeiro mais completo para análise de extratos bancários.</p>
                <div style="background:#171922; border-left:4px solid #d4af37; padding:15px; margin:20px 0; border-radius:4px;">
                    <p style="margin:0; font-size:14px;"><b>Usuário:</b> {nome_usuario}</p>
                    <p style="margin:0; font-size:14px;"><b>Plano Inicial:</b> Básico (Gratuito)</p>
                </div>
                <br>
                <small style="color:#777;">Mensagem automática emitida por MVPC Intelligence.</small>
            </div>
            """
            msg.attach(MIMEText(html, "html"))
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
                servidor.login(remetente, senha_remetente)
                servidor.sendmail(remetente, destinatario_email, msg.as_string())
            return True, "E-mail de confirmação enviado."
        except Exception as e:
            return False, f"Erro no envio do e-mail: {e}"
    return True, "(Configure credenciais no Secrets para disparo em tempo real)."

# --- BANCO DE DADOS & SESSÃO ---
if "usuarios_db" not in st.session_state:
    st.session_state["usuarios_db"] = {
        "admin": {"email": "admin@mvpc.com", "senha": "admin", "plano": "Pro"},
        "Marcos": {"email": "marcos@mvpc.com", "senha": "123", "plano": "Pro"}
    }

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = ""
if "transacoes" not in st.session_state:
    st.session_state["transacoes"] = []

# --- TELA DE AUTENTICAÇÃO ESTILIZADA ---
def tela_autenticacao():
    col_l1, col_l2, col_l3 = st.columns([1, 1.4, 1])
    with col_l2:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 25px;">
                <h1 style="font-size: 2.2rem; margin:0;">👑 MVPC FINANCIAL</h1>
                <p style="color: #a89f81; font-size: 0.95rem; margin-top: 5px;">Sua inteligência financeira automatizada</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.image("https://images.unsplash.com/photo-1642543492481-44e81e3914a7?q=80&w=1000&auto=format&fit=crop", use_container_width=True)
        st.write("")

        aba_login, aba_cadastro = st.tabs(["🔑 Acessar Painel", "✨ Criar Nova Conta"])
        
        with aba_login:
            st.write("")
            usuario = st.text_input("Usuário", key="login_user")
            senha = st.text_input("Senha", type="password", key="login_pass")
            st.write("")
            if st.button("Entrar no Sistema", use_container_width=True):
                if usuario in st.session_state["usuarios_db"] and st.session_state["usuarios_db"][usuario]["senha"] == senha:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_logado"] = usuario
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
                    
        with aba_cadastro:
            st.write("")
            novo_usuario = st.text_input("Nome de Usuário", key="cad_user")
            novo_email = st.text_input("E-mail Profissional", placeholder="seu@email.com", key="cad_email")
            nova_senha = st.text_input("Definir Senha", type="password", key="cad_pass")
            confirma_senha = st.text_input("Confirmar Senha", type="password", key="cad_pass_conf")
            st.write("")
            if st.button("Concluir Cadastro", use_container_width=True):
                if not novo_usuario or not novo_email or not nova_senha:
                    st.warning("Preencha todos os campos.")
                elif "@" not in novo_email or "." not in novo_email:
                    st.error("Insira um e-mail válido.")
                elif novo_usuario in st.session_state["usuarios_db"]:
                    st.error("Este nome de usuário já está em uso.")
                elif nova_senha != confirma_senha:
                    st.error("As senhas não coincidem.")
                else:
                    st.session_state["usuarios_db"][novo_usuario] = {
                        "email": novo_email,
                        "senha": nova_senha,
                        "plano": "Gratuito"
                    }
                    _, msg_email = enviar_email_boas_vindas(novo_email, novo_usuario)
                    st.success(f"Conta registrada! {msg_email} Acesse a aba 'Acessar Painel'.")

if not st.session_state["autenticado"]:
    tela_autenticacao()
    st.stop()

# --- USUÁRIO LOGADO & PLANO ---
usuario_atual = st.session_state.get("usuario_logado", "")
dados_usuario = st.session_state["usuarios_db"].get(usuario_atual, {"plano": "Gratuito", "email": ""})
plano_atual = dados_usuario.get("plano", "Gratuito")
eh_pro = (plano_atual == "Pro")

api_key = st.secrets.get("GEMINI_API_KEY", "")

# --- BARRA LATERAL MODERNA ---
with st.sidebar:
    st.markdown("""
        <div style="padding: 10px 0 20px 0; text-align: center;">
            <h2 style="font-size: 1.4rem; margin:0;">👑 MVPC FINANCIAL</h2>
            <small style="color: #888;">Inteligência de Extratos</small>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style="background:#181b24; padding:15px; border-radius:10px; border:1px solid #232734; margin-bottom: 20px;">
            <p style="margin:0; font-size:0.8rem; color:#888;">CONECTADO COMO</p>
            <p style="margin:0; font-weight:700; font-size:1.1rem; color:#f1e6b8;">{usuario_atual}</p>
            <p style="margin:4px 0 0 0; font-size:0.75rem; color:#c5a059;">{dados_usuario.get('email', '')}</p>
            <div style="margin-top: 10px;">
                <span class="{ 'badge-pro' if eh_pro else '' }" style="{ '' if eh_pro else 'background:#262a36; color:#aaa; font-size:0.75rem; padding:3px 8px; border-radius:4px;' }">
                    { '⭐ PLANO PRO ATIVO' if eh_pro else 'PLANO BÁSICO' }
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Navegação Profissional por Rádio Estilizado
    menu_selecionado = st.radio(
        "Navegação Principal",
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
                    if c_a1.button("Tornar Pro", key=f"ad_pro_{u}"):
                        st.session_state["usuarios_db"][u]["plano"] = "Pro"
                        st.rerun()
                else:
                    if u != "admin" and c_a2.button("Downgrade", key=f"ad_down_{u}"):
                        st.session_state["usuarios_db"][u]["plano"] = "Gratuito"
                        st.rerun()
        st.markdown("---")
        
    if not api_key:
        with st.expander("⚙️ Configurar API Key"):
            api_key = st.text_input("Gemini API Key", type="password")

    if st.session_state["transacoes"]:
        if st.button("🗑️ Limpar Dados Importados", use_container_width=True):
            st.session_state["transacoes"] = []
            st.rerun()

    if st.button("🚪 Encerrar Sessão", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.rerun()

# --- MOTOR DE LEITURA IA GEMINI ---
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
    Você é o motor de conciliação financeira do MVPC Financial. Analise o extrato abaixo e extraia rigorosamente todas as movimentações.
    Retorne EXCLUSIVAMENTE um array JSON contendo objetos no formato:
    - "data": string (DD/MM/AAAA)
    - "descricao": string (nome claro da transação, pessoa, banco ou comércio)
    - "tipo": string ("Receita" ou "Despesa")
    - "valor": float (valor absoluto positivo com duas casas decimais, ex: 150.50)

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
    if res_text.startswith("```json"): res_text = res_text[7:]
    if res_text.startswith("```"): res_text = res_text[3:]
    if res_text.endswith("```"): res_text = res_text[:-3]
    return json.loads(res_text.strip())

# ==========================================
# 📥 ABA 1: UPLOAD DE EXTRATOS
# ==========================================
if menu_selecionado == "📥 Upload de Extratos":
    st.markdown("""
        <div class="hero-box">
            <h1 style="margin:0; font-size:2rem;">📥 Central de Importação de Extratos</h1>
            <p style="color:#d5cca6; font-size:1.05rem; margin-top:8px; line-height:1.5;">
                Carregue seus extratos bancários em formato PDF (PicPay, Nubank, Itaú, Bradesco, etc.).<br>
                Nossa inteligência artificial estrutura e concilia suas receitas e despesas automaticamente.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    c_up1, c_up2 = st.columns([1.8, 1.2])
    
    with c_up1:
        if eh_pro:
            st.markdown("##### 🌟 Upload Ilimitado Multi-Arquivos (PRO)")
            arquivos = st.file_uploader("Arraste um ou múltiplos PDFs bancários", type=["pdf"], accept_multiple_files=True)
        else:
            st.markdown("##### 📄 Upload Individual (Plano Básico)")
            arquivo_unico = st.file_uploader("Arraste o seu extrato em PDF", type=["pdf"], accept_multiple_files=False)
            arquivos = [arquivo_unico] if arquivo_unico else []
            
        st.write("")
        if arquivos and st.button("🚀 Processar e Gerar Dashboard", use_container_width=True):
            if not api_key:
                st.error("Chave de API não detectada. Adicione aos Secrets ou configure na barra lateral.")
            else:
                todas_transacoes = []
                with st.spinner(f"Processando {len(arquivos)} documento(s) com IA..."):
                    for arq in arquivos:
                        try:
                            res = processar_extrato_pdf(arq, api_key)
                            todas_transacoes.extend(res)
                        except Exception as err:
                            st.error(f"Falha ao ler {arq.name}: {err}")
                    
                    if todas_transacoes:
                        st.session_state["transacoes"].extend(todas_transacoes)
                        st.success(f"✨ Sucesso! {len(todas_transacoes)} transações extraídas e consolidadas!")
                        st.info("👉 Vá para a aba **📊 Dashboard & Métricas** para ver a conciliação completa.")
    
    with c_up2:
        st.image("[https://images.unsplash.com/photo-1551836022-d5d88e9218df?q=80&w=800&auto=format&fit=crop](https://images.unsplash.com/photo-1551836022-d5d88e9218df?q=80&w=800&auto=format&fit=crop)", use_container_width=True)

# ==========================================
# 📊 ABA 2: DASHBOARD & MÉTRICAS
# ==========================================
elif menu_selecionado == "📊 Dashboard & Métricas":
    df_raw = pd.DataFrame(st.session_state["transacoes"])
    
    if df_raw.empty:
        st.markdown("""
            <div class="hero-box" style="text-align:center; padding: 50px 20px;">
                <h2>📊 Nenhum Lançamento Encontrado</h2>
                <p style="color:#bbb; max-width:550px; margin: 0 auto 20px auto;">
                    Você ainda não importou nenhum extrato. Faça o upload de um arquivo PDF para carregar seus dados e visualizar gráficos detalhados.
                </p>
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

        # --- CARDS DE KPIS PREMIUM ---
        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Receitas (Entradas) 💰</div>
                <div class="kpi-value" style="color: #00e676;">+ R$ {total_entradas:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
        
        k2.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Despesas (Saídas) 💸</div>
                <div class="kpi-value" style="color: #ff5252;">- R$ {total_saidas:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
        
        k3.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Saldo Líquido ⚖️</div>
                <div class="kpi-value" style="color: {'#00e676' if saldo_liquido >= 0 else '#ff5252'};">R$ {saldo_liquido:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
        
        k4.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Taxa de Poupança 📈</div>
                <div class="kpi-value" style="color: #d4af37;">{taxa_poupanca:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.write("")
        
        # --- TABELA E GRÁFICO LADO A LADO ---
        c_tab, c_graf = st.columns([1.3, 1.1])
        
        with c_tab:
            st.markdown("### 📋 Transações Conciliadas")
            df_table = df_raw.copy()
            df_table["valor_num"] = df_table.apply(lambda r: r["valor"] if r["tipo"] == "Receita" else -r["valor"], axis=1)
            
            df_render = df_table[["data", "descricao", "valor_num"]].rename(
                columns={"data": "Data", "descricao": "Descrição", "valor_num": "Valor (R$)"}
            )
            
            def cor_transacao(val):
                return 'color: #00e676; font-weight: bold;' if val > 0 else 'color: #ff5252; font-weight: bold;'

            st.dataframe(
                df_render.style
                    .format({"Valor (R$)": lambda x: f"+ R$ {x:,.2f}" if x > 0 else f"- R$ {abs(x):,.2f}"})
                    .map(cor_transacao, subset=["Valor (R$)"]),
                use_container_width=True,
                hide_index=True,
                height=460
            )
            
        with c_graf:
            st.markdown("### 🍩 Proporção do Fluxo")
            total_vol = total_entradas + total_saidas
            
            fig = go.Figure(data=[go.Pie(
                labels=["Entradas (Receitas)", "Saídas (Despesas)"],
                values=[total_entradas, total_saidas],
                hole=0.62,
                marker=dict(
                    colors=["#00e676", "#ff5252"],
                    line=dict(color="#0d0e12", width=3)
                ),
                textinfo="percent",
                textfont=dict(size=14, color="#ffffff", family="Plus Jakarta Sans"),
                hovertemplate="<b>%{label}</b><br>Montante: R$ %{value:,.2f}<br>Participação: %{percent}<extra></extra>"
            )])
            
            fig.update_layout(
                paper_bgcolor="#141720",
                plot_bgcolor="#141720",
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.15,
                    xanchor="center",
                    x=0.5,
                    font=dict(color="#f1e6b8", size=12)
                ),
                annotations=[
                    dict(
                        text=f"<span style='font-size:12px; color:#c5a059;'>Volume Total</span><br><b style='font-size:17px; color:#ffffff;'>R$ {total_vol:,.2f}</b>",
                        x=0.5, y=0.5,
                        font_size=14,
                        showarrow=False
                    )
                ],
                margin=dict(t=10, b=30, l=10, r=10),
                height=460
            )
            st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 🔮 ABA 3: PLANEJAMENTO FUTURO
# ==========================================
elif menu_selecionado == "🔮 Planejamento Futuro":
    if not eh_pro:
        st.markdown("""
            <div class="hero-box" style="text-align: center; border: 2px solid #d4af37; padding: 45px 25px;">
                <div class="badge-pro">Recurso Exclusivo PRO</div>
                <h1 style="font-size: 2.2rem; margin: 10px 0;">🔮 Planejamento & Projeções de Gastos</h1>
                <p style="color: #f1e6b8; max-width: 620px; margin: 0 auto 25px auto; font-size: 1.05rem; line-height: 1.6;">
                    Antecipe seus meses futuros, simule gastos fixos, defina tetos orçamentários por categorias e saiba exatamente quanto vai sobrar na sua reserva.
                </p>
                <img src="[https://images.unsplash.com/photo-1559526324-4b87b5e36e44?q=80&w=900&auto=format&fit=crop](https://images.unsplash.com/photo-1559526324-4b87b5e36e44?q=80&w=900&auto=format&fit=crop)" style="border-radius:12px; max-width: 500px; width: 100%; border: 1px solid rgba(212,175,55,0.3); margin-bottom: 25px;">
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="hero-box">
                <h1 style="margin:0; font-size:2rem;">🔮 Planejamento Orçamentário Estratégico</h1>
                <p style="color:#d5cca6; margin-top:6px;">Simulação preditiva de fluxo de caixa para os próximos períodos.</p>
            </div>
        """, unsafe_allow_html=True)
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("#### 🎯 Metas & Tetos de Gastos")
            renda_est = st.number_input("Renda Prevista (R$)", value=5000.0, step=200.0)
            teto_gasto = st.number_input("Teto Máximo de Gastos Mensal (R$)", value=3200.0, step=100.0)
            meta_sobra = renda_est - teto_gasto
            
            st.markdown(f"""
                <div class="kpi-card" style="margin-top: 20px; text-align: left; padding: 20px;">
                    <div class="kpi-title">Margem de Economia Projetada</div>
                    <div class="kpi-value" style="color: #00e676;">R$ {meta_sobra:,.2f}</div>
                    <small style="color: #888;">Capacidade estimada de investimento no período</small>
                </div>
            """, unsafe_allow_html=True)
            
        with col_p2:
            st.markdown("#### 💡 Simulação de Contas Fixas")
            fixos = st.number_input("Despesas Fixas (Aluguel, Luz, Assinaturas)", value=1800.0, step=100.0)
            livre_lazer = teto_gasto - fixos
            
            if livre_lazer > 0:
                st.success(f"Saldo Livre para Lazer & Imprevistos: **R$ {livre_lazer:,.2f}**")
            else:
                st.error("Atenção: Os custos fixos estão superando o teto orçamentário pretendido!")

# ==========================================
# ⭐ ABA 4: ASSINATURA PRO & CHECKOUT
# ==========================================
elif menu_selecionado == "⭐ Assinatura PRO":
    st.markdown("""
        <div style="text-align: center; margin-bottom: 35px;">
            <h1 style="font-size: 2.3rem; margin:0;">⭐ Escolha a Melhor Experiência Financeira</h1>
            <p style="color: #b5ac91; font-size: 1.05rem; margin-top:6px;">Automatize sua conciliação com ferramentas profissionais sem limites</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown("""
            <div class="plan-card">
                <h3 style="color:#aaa !important; margin-top:0;">Plano Básico</h3>
                <h2 style="color:#fff !important; font-size:2rem;">Grátis</h2>
                <p style="color:#777; font-size:0.9rem;">Para quem precisa de análises pontuais</p>
                <hr style="border-color:#2a2e3d;">
                <ul style="color:#aaa; line-height:2; font-size:0.95rem; list-style:none; padding-left:0;">
                    <li>✔ 1 Upload de extrato por vez</li>
                    <li>✔ Resumo de entradas e saídas</li>
                    <li>✔ Gráfico de fluxo em donut</li>
                    <li>✖ <strike>Upload de múltiplos extratos juntos</strike></li>
                    <li>✖ <strike>Planejamento de gastos futuros</strike></li>
                    <li>✖ <strike>Suporte com IA dedicado</strike></li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        
    with col_c2:
        st.markdown("""
            <div class="plan-card plan-card-pro">
                <div class="badge-pro">Recomendado</div>
                <h3 style="color:#d4af37 !important; margin-top:0;">Plano PRO ⭐</h3>
                <h2 style="color:#00e676 !important; font-size:2.2rem; margin:0;">
                    R$ 19,90 <span style="font-size:1rem; color:#f1e6b8; font-weight:400;">/ mês</span>
                </h2>
                <p style="color:#c5a059; font-size:0.9rem;">Controle financeiro avançado e ilimitado</p>
                <hr style="border-color:rgba(212,175,55,0.2);">
                <ul style="color:#f1e6b8; line-height:2; font-size:0.95rem; list-style:none; padding-left:0;">
                    <li>✔ <b>Upload ilimitado de múltiplos PDFs simultâneos</b></li>
                    <li>✔ <b>Acesso total à aba de Planejamento Futuro</b></li>
                    <li>✔ Consolidação multi-bancos sem limites</li>
                    <li>✔ Algoritmo com prioridade máxima de IA</li>
                    <li>✔ Suporte VIP via canal direto</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        
    st.write("")
    st.write("")
    
    if not eh_pro:
        st.markdown("### 💳 Concluir Assinatura PRO")
        st.image("[https://images.unsplash.com/photo-1563013544-824ae1b704d3?q=80&w=900&auto=format&fit=crop](https://images.unsplash.com/photo-1563013544-824ae1b704d3?q=80&w=900&auto=format&fit=crop)", use_container_width=True)
        
        tab_px, tab_cc = st.tabs(["⚡ Pix Instantâneo", "💳 Cartão de Crédito"])
        
        with tab_px:
            st.info("Pague via Pix e sua conta será promovida para PRO imediatamente.")
            st.code("financeiro@mvpc.com.br", language="text")
            if st.button("✅ Confirmar Pagamento Pix de R$ 19,90", use_container_width=True):
                st.session_state["usuarios_db"][usuario_atual]["plano"] = "Pro"
                st.success("🎉 Pagamento confirmado! Seu plano PRO está ativo.")
                st.rerun()
                
        with tab_cc:
            c_num = st.text_input("Número do Cartão", placeholder="0000 0000 0000 0000")
            c_cc1, c_cc2 = st.columns(2)
            c_cc1.text_input("Validade", placeholder="MM/AA")
            c_cc2.text_input("CVC", type="password", placeholder="123")
            if st.button("Pagar R$ 19,90 e Ativar Acesso Imediato", use_container_width=True):
                st.session_state["usuarios_db"][usuario_atual]["plano"] = "Pro"
                st.success("🎉 Transação aprovada! Sua conta agora é PRO.")
                st.rerun()
    else:
        st.markdown("""
            <div class="kpi-card" style="border:1px solid #00e676; margin-top:20px;">
                <h3 style="color:#00e676 !important; margin:0;">🎉 Sua Assinatura PRO está Ativa!</h3>
                <p style="color:#f1e6b8; margin:5px 0 0 0;">Você tem acesso ilimitado a todos os módulos e funcionalidades do MVPC Financial.</p>
            </div>
        """, unsafe_allow_html=True)
