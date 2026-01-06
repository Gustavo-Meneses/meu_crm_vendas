import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import hashlib
import json

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Gemini CRM Pro", layout="wide")

# Conectar ao Banco de Dados (SQLite)
conn = sqlite3.connect('crm_data.db', check_same_thread=False)
c = conn.cursor()

# Criar tabelas se não existirem
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
c.execute('''CREATE TABLE IF NOT EXISTS leads 
             (nome TEXT, empresa TEXT, status TEXT, historico TEXT, score INTEGER, valor REAL)''')
conn.commit()

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
            st.success("Conta criada! Vá em Login na barra lateral.")
            
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
                st.error("Usuário ou Senha incorretos")

# --- APP PRINCIPAL (SÓ ACESSA SE LOGADO) ---
else:
    # Configuração Estabilizada da IA
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        # Chamada simplificada para evitar erro v1beta/NotFound
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Erro na configuração da IA: {e}")
        model = None

    st.sidebar.title(f"Bem-vindo, {st.session_state['user']}")
    page = st.sidebar.radio("Navegação:", ["Dashboard", "Adicionar Lead (IA)", "Chat com CRM", "Admin"])
    
    if st.sidebar.button("Sair"):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- PÁGINA DASHBOARD ---
    if page == "Dashboard":
        st.header("📊 Painel de Vendas")
        df = pd.read_sql_query("SELECT * FROM leads", conn)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            col1, col2 = st.columns(2)
            col1.metric("Leads Ativos", len(df))
            col2.metric("Total em Propostas", f"R$ {df['valor'].sum():,.2f}")
        else:
            st.info("Nenhum lead cadastrado ainda.")

    # --- PÁGINA ADICIONAR LEAD ---
    elif page == "Adicionar Lead (IA)":
        st.header("✍️ Entrada Inteligente")
        texto_bruto = st.text_area("Descreva a reunião ou interação com o lead:")
        
        if st.button("Processar com Gemini"):
            if model and texto_bruto:
                try:
                    prompt = f"""Extraia os dados deste texto no formato JSON puro com os campos: 
                    nome, empresa, status, resumo_conversa, score, valor. Texto: {texto_bruto}"""
                    
                    response = model.generate_content(prompt)
                    # Limpeza de Markdown
                    res_text = response.text.replace('```json', '').replace('```', '').strip()
                    d = json.loads(res_text)
                    
                    c.execute('''INSERT INTO leads (nome, empresa, status, historico, score, valor) 
                                 VALUES (?, ?, ?, ?, ?, ?)''', 
                              (d.get('nome','N/A'), d.get('empresa','N/A'), d.get('status','Prospecção'), 
                               d.get('resumo_conversa',''), d.get('score',0), d.get('valor',0)))
                    conn.commit()
                    st.success(f"Lead {d.get('nome')} salvo com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao processar: {e}")
            else:
                st.warning("Verifique se a IA está configurada ou se o texto foi preenchido.")

    # --- PÁGINA CHAT ---
    elif page == "Chat com CRM":
        st.header("🤖 Inteligência de Vendas")
        df = pd.read_sql_query("SELECT * FROM leads", conn)
        pergunta = st.text_input("Faça uma pergunta sobre seus leads:")
        if pergunta and model:
            if not df.empty:
                contexto = f"Dados do CRM: {df.to_string()}. Pergunta: {pergunta}"
                resp = model.generate_content(contexto)
                st.write(resp.text)
            else:
                st.info("O banco de dados está vazio.")

    # --- PÁGINA ADMIN ---
    elif page == "Admin":
        st.header("👥 Gestão de Usuários")
        df_u = pd.read_sql_query("SELECT username FROM users", conn)
        st.table(df_u)
