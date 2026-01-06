import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import hashlib
import json

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Gemini CRM Pro", layout="wide")

# Conectar ao Banco de Dados
conn = sqlite3.connect('crm_data.db', check_same_thread=False)
c = conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS leads (nome TEXT, empresa TEXT, status TEXT, historico TEXT, score INTEGER, valor REAL)')
conn.commit()

# --- FUNÇÕES DE IA (Blindadas) ---
def inicializar_ia():
    try:
        # Pega a chave do campo SECRETS do Streamlit
        api_key = st.secrets["GEMINI_KEY"]
        genai.configure(api_key=api_key)
        # Força o uso do nome estável do modelo
        return genai.GenerativeModel(model_name='models/gemini-1.5-flash')
    except Exception as e:
        st.error(f"Erro ao configurar IA: {e}")
        return None

# --- FUNÇÕES DE SEGURANÇA ---
def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

# --- INTERFACE DE LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🚀 Gemini CRM - Login")
    menu = ["Login", "Registrar"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Registrar":
        new_user = st.text_input("Usuário")
        new_password = st.text_input("Senha", type='password')
        if st.button("Criar Conta"):
            c.execute('INSERT INTO users(username,password) VALUES (?,?)', (new_user, make_hashes(new_password)))
            conn.commit()
            st.success("Conta criada! Vá em Login.")
    elif choice == "Login":
        username = st.sidebar.text_input("Usuário")
        password = st.sidebar.text_input("Senha", type='password')
        if st.sidebar.button("Entrar"):
            c.execute('SELECT * FROM users WHERE username =?', (username,))
            data = c.fetchone()
            if data and check_hashes(password, data[1]):
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Usuário ou Senha incorretos")

# --- APP PRINCIPAL ---
else:
    model = inicializar_ia()
    
    st.sidebar.title("Navegação")
    page = st.sidebar.radio("Ir para:", ["Dashboard", "Adicionar Lead (IA)", "Chat com CRM"])
    
    if st.sidebar.button("Sair"):
        st.session_state['logged_in'] = False
        st.rerun()

    if page == "Dashboard":
        st.header("📊 Painel de Vendas")
        df = pd.read_sql_query("SELECT * FROM leads", conn)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.metric("Total em Propostas", f"R$ {df['valor'].sum():,.2f}")
        else:
            st.info("Nenhum lead cadastrado.")

    elif page == "Adicionar Lead (IA)":
        st.header("✍️ Entrada Inteligente")
        texto = st.text_area("Descreva a interação:")
        if st.button("Processar com Gemini") and model:
            try:
                prompt = f"Retorne APENAS um JSON para: {texto}. Campos: nome, empresa, status, resumo_conversa, score, valor."
                response = model.generate_content(prompt)
                limpo = response.text.replace('```json', '').replace('```', '').strip()
                d = json.loads(limpo)
                c.execute('INSERT INTO leads VALUES (?,?,?,?,?,?)', 
                          (d.get('nome',''), d.get('empresa',''), d.get('status',''), d.get('resumo_conversa',''), d.get('score',0), d.get('valor',0)))
                conn.commit()
                st.success("Lead cadastrado!")
            except Exception as e:
                st.error(f"Erro: {e}")

    elif page == "Chat com CRM":
        st.header("🤖 Pergunte ao CRM")
        pergunta = st.text_input("O que deseja saber?")
        if pergunta and model:
            df = pd.read_sql_query("SELECT * FROM leads", conn)
            resp = model.generate_content(f"Dados: {df.to_string()}. Pergunta: {pergunta}")
            st.write(resp.text)
