import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
import hashlib
import json

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Gemini CRM Sheets", layout="wide")

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data(worksheet):
    return conn.read(spreadsheet=st.secrets["gsheets_url"], worksheet=worksheet)

def save_data(df, worksheet):
    conn.update(spreadsheet=st.secrets["gsheets_url"], worksheet=worksheet, data=df)

# --- FUNÇÕES DE SEGURANÇA ---
def hash_pw(pw): return hashlib.sha256(str.encode(pw)).hexdigest()

# Inicializar Usuários (Garantir que Gustavo Admin existe)
df_users = get_data("users")
if "Gustavo Meneses" not in df_users['username'].values:
    new_admin = pd.DataFrame([{
        "username": "Gustavo Meneses", 
        "password": hash_pw("1234"), 
        "role": "admin", 
        "pergunta_seg": "Qual o nome da sua empresa?", 
        "resposta_seg": hash_pw("CRM")
    }])
    df_users = pd.concat([df_users, new_admin], ignore_index=True)
    save_data(df_users, "users")

# --- IA: CONFIGURAÇÃO ---
def chamar_ia(prompt_text):
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model.generate_content(prompt_text).text

# --- INTERFACE DE ACESSO ---
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🚀 CRM Google Sheets")
    tab1, tab2, tab3 = st.tabs(["Entrar", "Novo Cadastro", "Recuperar"])
    
    with tab1:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type='password')
        if st.button("Acessar"):
            user_row = df_users[df_users['username'] == u]
            if not user_row.empty and user_row.iloc[0]['password'] == hash_pw(p):
                st.session_state.logado = True
                st.session_state.user_name = u
                st.session_state.user_role = user_row.iloc[0]['role']
                st.rerun()
            else: st.error("Erro no login.")

    with tab2:
        new_u = st.text_input("Novo Usuário")
        new_p = st.text_input("Senha ", type='password')
        perg = st.selectbox("Pergunta", ["Cidade natal?", "Nome do pet?"])
        resp = st.text_input("Resposta")
        if st.button("Cadastrar"):
            if new_u not in df_users['username'].values:
                new_row = pd.DataFrame([{"username": new_u, "password": hash_pw(new_p), "role": "user", "pergunta_seg": perg, "resposta_seg": hash_pw(resp.lower())}])
                save_data(pd.concat([df_users, new_row]), "users")
                st.success("Cadastrado!")
            else: st.error("Usuário já existe.")

# --- SISTEMA PRINCIPAL ---
else:
    st.sidebar.title(f"👤 {st.session_state.user_name}")
    menu = st.sidebar.radio("Navegação", ["Dashboard", "Adicionar Lead (IA)", "Painel Admin"])
    
    if menu == "Dashboard":
        df_leads = get_data("leads")
        st.header("📊 Leads na Nuvem")
        st.dataframe(df_leads)
        st.bar_chart(df_leads['status'].value_counts())
        
        csv = df_leads.to_csv(index=False).encode('utf-8')
        st.download_button("Baixar CSV", csv, "leads.csv")

    elif menu == "Adicionar Lead (IA)":
        texto = st.text_area("Notas do lead:")
        if st.button("Analisar"):
            res = chamar_ia(f"Extraia JSON: {{'nome','empresa','status','historico','score','valor'}}. Texto: {texto}")
            d = json.loads(res.replace('```json', '').replace('```', '').strip())
            df_leads = get_data("leads")
            save_data(pd.concat([df_leads, pd.DataFrame([d])]), "leads")
            st.success("Salvo no Google Sheets!")

    elif menu == "Painel Admin" and st.session_state.user_role == "admin":
        st.header("🔐 Admin")
        df_users = get_data("users")
        u_alvo = st.selectbox("Usuário", df_users['username'])
        nova_s = st.text_input("Nova Senha Admin", type="password")
        if st.button("Resetar Senha"):
            df_users.loc[df_users['username'] == u_alvo, 'password'] = hash_pw(nova_s)
            save_data(df_users, "users")
            st.success("Senha alterada!")
