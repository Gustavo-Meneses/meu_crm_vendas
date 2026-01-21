import streamlit as st
import pandas as pd
from mistralai import Mistral
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão Comercial Inteligente", layout="wide", page_icon="🏢")

# --- INICIALIZAÇÃO DE DADOS EM MEMÓRIA ---
if 'df_leads' not in st.session_state:
    st.session_state.df_leads = pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- FUNÇÃO IA (MISTRAL AI) ---
def processar_com_mistral(texto_entrada):
    try:
        api_key = st.secrets.get("MISTRAL_API_KEY")
        if not api_key:
            return "ERRO_CONFIG: Chave MISTRAL_API_KEY não encontrada."
        
        client = Mistral(api_key=api_key)
        model = "mistral-small-latest"
        
        prompt_sistema = (
            "Você é um analista comercial. Extraia do texto e retorne APENAS um JSON puro. "
            "Campos: nome, empresa, status, historico, score (0-100) e valor (numérico)."
        )

        response = client.chat.complete(
            model=model,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Extraia os dados: {texto_entrada}"}
            ],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERRO_API: {str(e)}"

# --- INTERFACE DE LOGIN ---
if not st.session_state.logado:
    # CORREÇÃO AQUI: O parâmetro correto é unsafe_allow_html
    st.markdown("<h2 style='text-align: center;'>Acesso ao Sistema de Gestão Comercial</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Insira as credenciais administrativas.</p>", unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        
        if st.button("Autenticar", use_container_width=True):
            if u == "ADM" and p == "1234":
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Credenciais inválidas.")

# --- APP PRINCIPAL ---
else:
    st.sidebar.title("🏢 Painel Administrativo")
    aba = st.sidebar.radio("Menu", ["📊 Dashboard", "➕ Capturar Lead"])
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if aba == "📊 Dashboard":
        st.header("📊 Performance de Vendas")
        if not st.session_state.df_leads.empty:
            v_total = pd.to_numeric(st.session_state.df_leads['valor'], errors='coerce').sum()
            st.metric("Total em Propostas", f"R$ {v_total:,.2f}")
            st.dataframe(st.session_state.df_leads, use_container_width=True)
        else:
            st.info("Nenhum lead capturado.")

    elif aba == "➕ Capturar Lead":
        st.header("⚡ Inteligência de Dados")
        txt = st.text_area("Texto do Lead (E-mail/WhatsApp):", height=200)
        
        if st.button("Processar com IA"):
            if txt:
                with st.spinner("Analisando..."):
                    res = processar_com_mistral(txt)
                    if "ERRO" not in res:
                        dados = json.loads(res)
                        st.session_state.df_leads = pd.concat([st.session_state.df_leads, pd.DataFrame([dados])], ignore_index=True)
                        st.success("Lead salvo!")
                    else:
                        st.error(res)
