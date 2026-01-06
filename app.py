import streamlit as st
import pandas as pd
import google.generativeai as genai
import hashlib
import json

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Gemini CRM - Memory Mode", layout="wide", page_icon="🚀")

# --- INICIALIZAÇÃO DA BASE DE DADOS (EM MEMÓRIA) ---
if 'df_users' not in st.session_state:
    admin_pw = hashlib.sha256(str.encode("1234")).hexdigest()
    st.session_state.df_users = pd.DataFrame([{
        "username": "Gustavo Meneses", 
        "password": admin_pw, 
        "role": "admin", 
        "pergunta_seg": "Empresa?", 
        "resposta_seg": hashlib.sha256(str.encode("crm")).hexdigest()
    }])

if 'df_leads' not in st.session_state:
    st.session_state.df_leads = pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

# --- FUNÇÕES DE APOIO ---
def hash_pw(pw): 
    return hashlib.sha256(str.encode(pw)).hexdigest()

def chamar_ia(prompt_text):
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        # Correção do modelo: Usamos 'gemini-1.5-flash' sem o prefixo 'models/' se necessário
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prompt reforçado para evitar erros de formato
        system_prompt = "Você é um assistente de CRM. Extraia os dados do texto e responda APENAS com um objeto JSON puro, sem marcações de markdown ou blocos de código. "
        response = model.generate_content(system_prompt + prompt_text)
        return response.text
    except Exception as e:
        return f"ERRO_IA: {str(e)}"

# --- INTERFACE DE ACESSO ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🚀 CRM Inteligente - Acesso")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type='password')
    if st.button("Acessar"):
        users = st.session_state.df_users
        user_row = users[users['username'] == u]
        if not user_row.empty and user_row.iloc[0]['password'] == hash_pw(p):
            st.session_state.logado = True
            st.session_state.user_name = u
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

# --- SISTEMA PRINCIPAL ---
else:
    st.sidebar.title(f"👤 {st.session_state.user_name}")
    menu = st.sidebar.radio("Navegação", ["Dashboard", "Adicionar Lead (IA)"])
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if menu == "Dashboard":
        st.header("📊 Leads em Memória")
        if not st.session_state.df_leads.empty:
            st.dataframe(st.session_state.df_leads, use_container_width=True)
            st.bar_chart(st.session_state.df_leads['status'].value_counts())
        else:
            st.info("Sua lista de leads está vazia nesta sessão.")

    elif menu == "Adicionar Lead (IA)":
        st.header("🪄 Captura por IA")
        txt = st.text_area("Notas do lead (Teste 1):")
        if st.button("Processar com Gemini"):
            with st.spinner("Analisando..."):
                res = chamar_ia(f"Extraia para JSON: {{'nome','empresa','status','historico','score','valor'}}. Texto: {txt}")
                
                if "ERRO_IA" in res:
                    st.error(f"Erro na comunicação com o Google: {res}")
                else:
                    try:
                        # Limpa possíveis sujeiras de texto da IA
                        json_clean = res.strip().replace('```json', '').replace('```', '')
                        dados = json.loads(json_clean)
                        
                        # Converte para DataFrame e adiciona
                        novo_lead = pd.DataFrame([dados])
                        st.session_state.df_leads = pd.concat([st.session_state.df_leads, novo_lead], ignore_index=True)
                        st.success("Lead identificado e adicionado com sucesso!")
                        st.balloons()
                    except Exception as e:
                        st.error("A IA respondeu, mas o formato não foi reconhecido. Tente simplificar o texto.")
                        st.code(res) # Mostra o que a IA mandou para debug
