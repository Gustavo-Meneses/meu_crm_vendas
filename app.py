import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import hashlib
import json

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Gemini CRM Pro", layout="wide")

# Banco de Dados
conn = sqlite3.connect('crm_data.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS leads (nome TEXT, empresa TEXT, status TEXT, historico TEXT, score INTEGER, valor REAL)')
conn.commit()

# --- IA: AUTO-DESCOBERTA DE MODELO ---
def chamar_ia(prompt_text):
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        
        # Lista modelos que permitem gerar conteúdo
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if not models:
            raise Exception("Nenhum modelo disponível para esta chave API.")
            
        # Tenta achar o flash na lista, se não achar, usa o primeiro disponível
        modelo_final = next((m for m in models if "gemini-1.5-flash" in m), models[0])
        
        model = genai.GenerativeModel(modelo_final)
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        raise Exception(f"Erro na IA: {str(e)}")

# --- SEGURANÇA ---
def hash_pw(pw): return hashlib.sha256(str.encode(pw)).hexdigest()

# --- LOGIN ---
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🚀 CRM Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type='password')
    col1, col2 = st.columns(2)
    if col1.button("Entrar"):
        c.execute('SELECT * FROM users WHERE username=?', (u,))
        user = c.fetchone()
        if user and user[1] == hash_pw(p):
            st.session_state.logado = True
            st.rerun()
        else: st.error("Incorreto")
    if col2.button("Registrar"):
        c.execute('INSERT INTO users VALUES (?,?)', (u, hash_pw(p)))
        conn.commit()
        st.success("Registrado!")

# --- APP ---
else:
    page = st.sidebar.radio("Menu", ["Dashboard", "Adicionar Lead (IA)"])
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if page == "Dashboard":
        df = pd.read_sql_query("SELECT * FROM leads", conn)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.metric("Total", f"R$ {df['valor'].sum():,.2f}")

    elif page == "Adicionar Lead (IA)":
        texto = st.text_area("Descreva a interação:")
        if st.button("Analisar"):
            try:
                # Prompt simplificado para evitar erros de parsing
                prompt = f"Converta em JSON (nome, empresa, status, resumo_conversa, score, valor): {texto}. Responda apenas o JSON."
                res = chamar_ia(prompt)
                limpo = res.replace('```json', '').replace('```', '').strip()
                d = json.loads(limpo)
                c.execute('INSERT INTO leads VALUES (?,?,?,?,?,?)', 
                          (d.get('nome',''), d.get('empresa',''), d.get('status',''), d.get('resumo_conversa',''), d.get('score',0), d.get('valor',0)))
                conn.commit()
                st.success("Salvo!")
            except Exception as e:
                st.error(f"{e}")
