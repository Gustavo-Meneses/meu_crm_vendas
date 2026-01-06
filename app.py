import streamlit as st
import pandas as pd
import google.generativeai as genai
import hashlib
import json

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Meneses CRM - Memory Mode", layout="wide", page_icon="🧠")

# --- INICIALIZAÇÃO DA BASE DE DADOS (EM MEMÓRIA) ---
# O st.session_state mantém os dados durante a navegação do usuário
if 'df_users' not in st.session_state:
    # Criando o Admin padrão
    admin_pw = hashlib.sha256(str.encode("1234")).hexdigest()
    st.session_state.df_users = pd.DataFrame([{
        "username": "Gustavo Meneses", 
        "password": admin_pw, 
        "role": "admin", 
        "pergunta_seg": "Qual o nome da sua empresa?", 
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
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        return f"Erro na IA: {str(e)}"

# --- INTERFACE DE ACESSO ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🚀 CRM Inteligente (Modo Local)")
    tab_login, tab_reg = st.tabs(["Entrar", "Novo Cadastro"])
    
    with tab_login:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type='password')
        if st.button("Acessar"):
            users = st.session_state.df_users
            user_row = users[users['username'] == u]
            if not user_row.empty and user_row.iloc[0]['password'] == hash_pw(p):
                st.session_state.logado = True
                st.session_state.user_name = u
                st.session_state.user_role = user_row.iloc[0]['role']
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    with tab_reg:
        new_u = st.text_input("Novo Usuário")
        new_p = st.text_input("Defina uma Senha", type='password')
        if st.button("Cadastrar"):
            if new_u and new_p:
                new_row = pd.DataFrame([{"username": new_u, "password": hash_pw(new_p), "role": "user"}])
                st.session_state.df_users = pd.concat([st.session_state.df_users, new_row], ignore_index=True)
                st.success("Cadastrado com sucesso! Vá para a aba Entrar.")

# --- SISTEMA PRINCIPAL ---
else:
    st.sidebar.title(f"👤 {st.session_state.user_name}")
    menu = st.sidebar.radio("Navegação", ["Dashboard", "Adicionar Lead (IA)", "Exportar"])
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if menu == "Dashboard":
        st.header("📊 Leads Atuais")
        if not st.session_state.df_leads.empty:
            st.dataframe(st.session_state.df_leads, use_container_width=True)
            st.bar_chart(st.session_state.df_leads['status'].value_counts())
        else:
            st.info("Nenhum lead cadastrado nesta sessão.")

    elif menu == "Adicionar Lead (IA)":
        st.header("🪄 Captura por IA")
        txt = st.text_area("Notas do lead:")
        if st.button("Processar com Gemini"):
            res = chamar_ia(f"Extraia JSON: {{'nome','empresa','status','historico','score','valor'}}. Texto: {txt}")
            try:
                # Limpando a resposta da IA para garantir JSON puro
                json_str = res.replace('```json', '').replace('```', '').strip()
                dados = json.loads(json_str)
                # Adicionando ao DataFrame na memória
                st.session_state.df_leads = pd.concat([st.session_state.df_leads, pd.DataFrame([dados])], ignore_index=True)
                st.success("Lead adicionado à memória!")
            except:
                st.error("A IA não retornou um formato válido. Tente novamente.")
                st.write(res)

    elif menu == "Exportar":
        st.header("💾 Salvar Dados")
        st.write("Como este app não tem banco de dados, baixe o arquivo abaixo antes de fechar a aba.")
        csv = st.session_state.df_leads.to_csv(index=False).encode('utf-8')
        st.download_button("Baixar Leads (CSV)", csv, "meus_leads.csv", "text/csv")
