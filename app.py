import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import hashlib
import json

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Gemini CRM Pro", layout="wide")

# Conexão com Banco de Dados
conn = sqlite3.connect('crm_data.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS leads (nome TEXT, empresa TEXT, status TEXT, historico TEXT, score INTEGER, valor REAL)')
conn.commit()

# --- FUNÇÃO DE IA REVISADA ---
def processar_com_ia(prompt_text):
    try:
        # Pega a chave dos Secrets
        api_key = st.secrets["GEMINI_KEY"]
        genai.configure(api_key=api_key)
        
        # Tentamos usar o modelo estável mais recente
        # Se gemini-1.5-flash falhar, o código tentará o gemini-pro automaticamente
        modelos_para_testar = ['gemini-1.5-flash', 'gemini-1.5-pro']
        
        for nome_modelo in modelos_para_testar:
            try:
                model = genai.GenerativeModel(nome_modelo)
                response = model.generate_content(prompt_text)
                return response.text
            except Exception:
                continue
        
        raise Exception("Nenhum modelo (Flash ou Pro) respondeu nesta região.")
        
    except Exception as e:
        raise Exception(f"Falha na comunicação: {str(e)}")

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
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type='password')
        if st.button("Criar Conta"):
            c.execute('INSERT INTO users VALUES (?,?)', (u, make_hashes(p)))
            conn.commit()
            st.success("Conta criada!")
    else:
        u = st.sidebar.text_input("Usuário")
        p = st.sidebar.text_input("Senha", type='password')
        if st.sidebar.button("Entrar"):
            c.execute('SELECT password FROM users WHERE username =?', (u,))
            data = c.fetchone()
            if data and check_hashes(p, data[0]):
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Usuário ou Senha incorretos")

# --- APP PRINCIPAL ---
else:
    st.sidebar.button("Sair", on_click=lambda: st.session_state.update({'logged_in': False}))
    page = st.sidebar.radio("Menu", ["Dashboard", "Adicionar Lead (IA)", "Chat"])

    if page == "Dashboard":
        st.header("📊 Seus Leads")
        df = pd.read_sql_query("SELECT * FROM leads", conn)
        st.dataframe(df, use_container_width=True)

    elif page == "Adicionar Lead (IA)":
        st.header("✍️ Captura Inteligente")
        texto = st.text_area("Descreva o lead ou a reunião:")
        if st.button("Analisar com Gemini"):
            try:
                prompt = f"Retorne APENAS um JSON: {{'nome': '...', 'empresa': '...', 'status': '...', 'resumo_conversa': '...', 'score': 0, 'valor': 0}}. Texto: {texto}"
                res = processar_com_ia(prompt)
                
                # Limpeza de resposta
                json_str = res.replace('```json', '').replace('```', '').strip()
                d = json.loads(json_str)
                
                c.execute('INSERT INTO leads VALUES (?,?,?,?,?,?)', 
                          (d.get('nome',''), d.get('empresa',''), d.get('status',''), d.get('resumo_conversa',''), d.get('score',0), d.get('valor',0)))
                conn.commit()
                st.success("Lead salvo!")
            except Exception as e:
                st.error(f"Erro: {e}")

    elif page == "Chat":
        st.header("🤖 Chat com CRM")
        pergunta = st.text_input("Sua pergunta:")
        if pergunta:
            df = pd.read_sql_query("SELECT * FROM leads", conn)
            res = processar_com_ia(f"Dados: {df.to_string()}. Pergunta: {pergunta}")
            st.write(res)
