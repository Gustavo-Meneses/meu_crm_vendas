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

# --- FUNÇÃO DE IA AUTO-DESCOBERTA ---
def processar_com_ia(prompt_text):
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        
        # LISTA OS MODELOS DISPONÍVEIS NA SUA CONTA
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if not models:
            raise Exception("Sua chave API não tem acesso a nenhum modelo de geração de conteúdo.")
        
        # TENTA O FLASH, SE NÃO TIVER, PEGA O PRIMEIRO DA LISTA
        modelo_escolhido = next((m for m in models if "gemini-1.5-flash" in m), models[0])
        
        model = genai.GenerativeModel(modelo_escolhido)
        response = model.generate_content(prompt_text)
        return response.text
        
    except Exception as e:
        raise Exception(f"Erro na API: {str(e)}")

# --- SEGURANÇA ---
def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

# --- LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🚀 Gemini CRM - Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type='password')
    if st.button("Entrar"):
        c.execute('SELECT password FROM users WHERE username =?', (u,))
        data = c.fetchone()
        if data and check_hashes(p, data[0]):
            st.session_state['logged_in'] = True
            st.rerun()
        else: st.error("Erro de login")
    if st.button("Registrar novo"):
        c.execute('INSERT INTO users VALUES (?,?)', (u, make_hashes(p)))
        conn.commit()
        st.success("Registrado!")

# --- APP PRINCIPAL ---
else:
    page = st.sidebar.radio("Menu", ["Dashboard", "Adicionar Lead (IA)"])

    if page == "Dashboard":
        df = pd.read_sql_query("SELECT * FROM leads", conn)
        st.dataframe(df, use_container_width=True)

    elif page == "Adicionar Lead (IA)":
        texto = st.text_area("Descreva o lead:")
        if st.button("Analisar"):
            try:
                prompt = f"Retorne JSON puro: {{'nome': '...', 'empresa': '...', 'status': '...', 'resumo_conversa': '...', 'score': 0, 'valor': 0}}. Texto: {texto}"
                res = processar_com_ia(prompt)
                d = json.loads(res.replace('```json', '').replace('```', '').strip())
                c.execute('INSERT INTO leads VALUES (?,?,?,?,?,?)', (d.get('nome',''), d.get('empresa',''), d.get('status',''), d.get('resumo_conversa',''), d.get('score',0), d.get('valor',0)))
                conn.commit()
                st.success("Salvo!")
            except Exception as e:
                st.error(f"{e}")
