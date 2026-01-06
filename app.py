import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import hashlib

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Gemini CRM Pro", layout="wide")

# Conectar ao Banco (Agora persistente)
conn = sqlite3.connect('crm_data.db', check_same_thread=False)
c = conn.cursor()

# Criar tabelas se não existirem
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS leads (nome TEXT, empresa TEXT, status TEXT, historico TEXT, score INTEGER, valor REAL)')
conn.commit()

# --- FUNÇÕES DE SEGURANÇA ---
def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text: return True
    return False

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

# --- APP PRINCIPAL (Após Login) ---
if st.session_state['logged_in']:
    st.sidebar.title("Navegação")
    page = st.sidebar.radio("Ir para:", ["Dashboard", "Adicionar Lead (IA)", "Chat com CRM"])
    
    if st.sidebar.button("Sair"):
        st.session_state['logged_in'] = False
        st.rerun()

    # Configurar Gemini
    genai.configure(api_key=st.secrets["GEMINI_KEY"]) # A chave fica escondida nas configs do site
    model = genai.GenerativeModel('gemini-1.5-flash')

    if page == "Dashboard":
        st.header("📊 Painel de Vendas")
        df = pd.read_sql_query("SELECT * FROM leads", conn)
        st.dataframe(df, use_container_width=True)
        
        # Resumo Financeiro
        total = df['valor'].sum()
        st.metric("Faturamento em Pipeline", f"R$ {total:,.2f}")

    elif page == "Adicionar Lead (IA)":
        st.header("✍️ Entrada Inteligente")
        texto_bruto = st.text_area("Cole aqui a conversa ou nota de reunião:")
        
        if st.button("Processar com Gemini"):
            prompt = f"Extraia nome, empresa, status (Prospecção, Reunião, Proposta, Fechado), resumo_conversa, score (0-100) e valor numérico do texto: {texto_bruto}. Responda APENAS JSON."
            response = model.generate_content(prompt)
            import json
            dados = json.loads(response.text.replace('```json', '').replace('```', ''))
            
            c.execute('INSERT INTO leads VALUES (?,?,?,?,?,?)', 
                      (dados['nome'], dados['empresa'], dados['status'], dados['resumo_conversa'], dados['score'], dados['valor']))
            conn.commit()
            st.success(f"Lead {dados['nome']} adicionado!")

    elif page == "Chat com CRM":
        st.header("🤖 Pergunte ao seu CRM")
        pergunta = st.text_input("O que você quer saber?")
        if pergunta:
            df = pd.read_sql_query("SELECT * FROM leads", conn)
            response = model.generate_content(f"Dados: {df.to_string()}. Pergunta: {pergunta}")
            st.write(response.text)
