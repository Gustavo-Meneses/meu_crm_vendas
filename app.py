import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import hashlib
import json

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Gemini CRM Pro", layout="wide")

conn = sqlite3.connect('crm_data.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS leads (nome TEXT, empresa TEXT, status TEXT, historico TEXT, score INTEGER, valor REAL)')
conn.commit()

# --- FUNÇÃO DE IA BLINDADA ---
def safe_generate_content(prompt_text):
    """Tenta chamar o modelo usando diferentes padrões de nome para evitar o erro 404"""
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    
    # Lista de tentativas de nomes de modelos (do mais comum ao mais específico)
    tentativas = ['gemini-1.5-flash', 'models/gemini-1.5-flash']
    
    last_error = None
    for model_name in tentativas:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt_text)
            return response.text
        except Exception as e:
            last_error = e
            continue
    
    raise Exception(f"Não foi possível conectar ao Gemini. Erro final: {last_error}")

# --- FUNÇÕES DE SEGURANÇA ---
def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

# --- LOGIN ---
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
            st.success("Conta criada!")
    elif choice == "Login":
        username = st.sidebar.text_input("Usuário")
        password = st.sidebar.text_input("Senha", type='password')
        if st.sidebar.button("Entrar"):
            c.execute('SELECT * FROM users WHERE username =?', (username,))
            data = c.fetchone()
            if data and check_hashes(password, data[1]):
                st.session_state['logged_in'] = True
                st.session_state['user'] = username
                st.rerun()
            else:
                st.error("Erro de login")

# --- APP PRINCIPAL ---
else:
    st.sidebar.title(f"Olá, {st.session_state['user']}")
    page = st.sidebar.radio("Ir para:", ["Dashboard", "Adicionar Lead (IA)", "Chat com CRM"])
    
    if st.sidebar.button("Sair"):
        st.session_state['logged_in'] = False
        st.rerun()

    if page == "Dashboard":
        st.header("📊 Painel")
        df = pd.read_sql_query("SELECT * FROM leads", conn)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.metric("Total Pipeline", f"R$ {df['valor'].sum():,.2f}")

    elif page == "Adicionar Lead (IA)":
        st.header("✍️ Novo Lead Inteligente")
        texto = st.text_area("Descreva o lead:")
        if st.button("Processar com IA"):
            try:
                prompt = f"Retorne APENAS um JSON: {{'nome': '...', 'empresa': '...', 'status': '...', 'resumo_conversa': '...', 'score': 0, 'valor': 0}}. Texto: {texto}"
                resultado = safe_generate_content(prompt)
                
                # Limpa e converte JSON
                json_str = resultado.replace('```json', '').replace('```', '').strip()
                d = json.loads(json_str)
                
                c.execute('INSERT INTO leads VALUES (?,?,?,?,?,?)', 
                          (d.get('nome',''), d.get('empresa',''), d.get('status',''), d.get('resumo_conversa',''), d.get('score',0), d.get('valor',0)))
                conn.commit()
                st.success("Lead salvo!")
            except Exception as e:
                st.error(f"Erro: {e}")

    elif page == "Chat com CRM":
        st.header("🤖 Chat com Dados")
        pergunta = st.text_input("Pergunta:")
        if pergunta:
            df = pd.read_sql_query("SELECT * FROM leads", conn)
            resp = safe_generate_content(f"Dados: {df.to_string()}. Pergunta: {pergunta}")
            st.write(resp)
