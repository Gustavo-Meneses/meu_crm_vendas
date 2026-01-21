import streamlit as st
import pandas as pd
from mistralai import Mistral
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão Comercial Inteligente", layout="wide", page_icon="🏢")

# --- INICIALIZAÇÃO DE SISTEMA (BANCO DE DADOS EM MEMÓRIA) ---
if 'df_leads' not in st.session_state:
    st.session_state.df_leads = pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

# Dicionário de usuários (Começa com o ADM padrão)
if 'usuarios_db' not in st.session_state:
    st.session_state.usuarios_db = {"ADM": "1234"}

if 'logado' not in st.session_state:
    st.session_state.logado = False

if 'usuario_atual' not in st.session_state:
    st.session_state.usuario_atual = None

# --- FUNÇÃO IA (MISTRAL AI) ---
def processar_com_mistral(texto_entrada):
    try:
        api_key = st.secrets.get("MISTRAL_API_KEY")
        if not api_key:
            return "ERRO_CONFIG: Chave MISTRAL_API_KEY não encontrada."
        
        client = Mistral(api_key=api_key)
        prompt_sistema = (
            "Você é um analista comercial. Extraia do texto e retorne APENAS um JSON puro. "
            "Campos: nome, empresa, status, historico, score (0-100) e valor (numérico)."
        )

        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Extraia os dados: {texto_entrada}"}
            ],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERRO_API: {str(e)}"

# --- INTERFACE DE ACESSO (LOGIN / CADASTRO) ---
if not st.session_state.logado:
    st.markdown("<h2 style='text-align: center;'>Portal de Gestão Comercial</h2>", unsafe_allow_html=True)
    
    tab_login, tab_cadastro = st.tabs(["🔐 Entrar", "📝 Cadastrar Novo Usuário"])
    
    with tab_login:
        _, col_l, _ = st.columns([1, 1, 1])
        with col_l:
            u_login = st.text_input("Usuário", key="login_user")
            p_login = st.text_input("Senha", type="password", key="login_pass")
            if st.button("Acessar Sistema", use_container_width=True):
                if u_login in st.session_state.usuarios_db and st.session_state.usuarios_db[u_login] == p_login:
                    st.session_state.logado = True
                    st.session_state.usuario_atual = u_login
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

    with tab_cadastro:
        _, col_c, _ = st.columns([1, 1, 1])
        with col_c:
            u_novo = st.text_input("Defina um Usuário", key="new_user")
            p_novo = st.text_input("Defina uma Senha", type="password", key="new_pass")
            p_conf = st.text_input("Confirme a Senha", type="password", key="conf_pass")
            
            if st.button("Criar Conta", use_container_width=True):
                if not u_novo or not p_novo:
                    st.warning("Preencha todos os campos.")
                elif u_novo in st.session_state.usuarios_db:
                    st.error("Este usuário já existe.")
                elif p_novo != p_conf:
                    st.error("As senhas não coincidem.")
                else:
                    st.session_state.usuarios_db[u_novo] = p_novo
                    st.success("Usuário cadastrado com sucesso! Vá para a aba Entrar.")

# --- APP PRINCIPAL ---
else:
    st.sidebar.title("🏢 Painel de Gestão")
    st.sidebar.write(f"Conectado como: **{st.session_state.usuario_atual}**")
    
    aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Capturar Lead"])
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if aba == "📊 Dashboard":
        st.header("📊 Performance de Vendas")
        if not st.session_state.df_leads.empty:
            v_total = pd.to_numeric(st.session_state.df_leads['valor'], errors='coerce').sum()
            st.metric("Total em Propostas", f"R$ {v_total:,.2f}")
            st.dataframe(st.session_state.df_leads, use_container_width=True)
            
            csv = st.session_state.df_leads.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Relatório", csv, "leads.csv", "text/csv")
        else:
            st.info("Nenhum lead capturado nesta sessão.")

    elif aba == "➕ Capturar Lead":
        st.header("⚡ Extração Inteligente")
        txt = st.text_area("Cole aqui a conversa ou e-mail:", height=200)
        
        if st.button("Processar Lead"):
            if txt:
                with st.spinner("Mistral AI analisando dados..."):
                    res = processar_com_mistral(txt)
                    if "ERRO" not in res:
                        try:
                            dados = json.loads(res)
                            st.session_state.df_leads = pd.concat([st.session_state.df_leads, pd.DataFrame([dados])], ignore_index=True)
                            st.success("Lead adicionado ao pipeline!")
                            st.json(dados)
                        except:
                            st.error("Erro ao formatar resposta.")
                    else:
                        st.error(res)
