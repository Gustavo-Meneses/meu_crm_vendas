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

# Criar tabelas
c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS leads (nome TEXT, empresa TEXT, status TEXT, historico TEXT, score INTEGER, valor REAL)')
conn.commit()

# --- FUNÇÕES DE SEGURANÇA ---
def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

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
else:
    # 1. Configuração do Gemini (Busca a chave no cofre do Secrets)
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error("Erro na API Key. Verifique o campo Secrets no Streamlit.")

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
            total = df['valor'].sum()
            st.metric("Faturamento em Pipeline", f"R$ {total:,.2f}")
        else:
            st.info("Nenhum lead cadastrado ainda.")

    elif page == "Adicionar Lead (IA)":
        st.header("✍️ Entrada Inteligente")
        texto_bruto = st.text_area("Descreva a interação (Ex: Falei com Marcos da empresa X, valor 5000...)")
        
        if st.button("Processar com Gemini"):
            if texto_bruto:
                try:
                    prompt = f"""Extraia nome, empresa, status (Prospecção, Reunião, Proposta, Fechado), 
                    resumo_conversa, score (0-100) e valor numérico do texto abaixo. 
                    Responda APENAS um JSON puro. Texto: {texto_bruto}"""
                    
                    response = model.generate_content(prompt)
                    # Limpeza de resposta para garantir JSON puro
                    texto_limpo = response.text.replace('```json', '').replace('```', '').strip()
                    dados = json.loads(texto_limpo)
                    
                    c.execute('INSERT INTO leads VALUES (?,?,?,?,?,?)', 
                              (dados.get('nome', 'N/A'), dados.get('empresa', 'N/A'), 
                               dados.get('status', 'Prospecção'), dados.get('resumo_conversa', ''), 
                               dados.get('score', 0), dados.get('valor', 0)))
                    conn.commit()
                    st.success(f"Lead {dados.get('nome')} adicionado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao processar com IA: {e}")
            else:
                st.warning("Por favor, digite algum texto.")

    elif page == "Chat com CRM":
        st.header("🤖 Pergunte ao seu CRM")
        df = pd.read_sql_query("SELECT * FROM leads", conn)
        pergunta = st.text_input("Ex: Qual meu lead com maior valor?")
        
        if pergunta:
            if not df.empty:
                contexto = f"Dados atuais do CRM: {df.to_string()}. Pergunta: {pergunta}"
                response = model.generate_content(contexto)
                st.write(response.text)
            else:
                st.warning("O banco de dados está vazio.")
