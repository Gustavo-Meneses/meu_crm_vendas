import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
import hashlib
import json

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Gemini CRM Pro", layout="wide")

# Conexão com Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Erro na conexão. Verifique os Secrets.")
    st.stop()

def get_data(worksheet_name):
    try:
        # Forçamos o recarregamento dos dados para evitar cache antigo
        return conn.read(spreadsheet=st.secrets["gsheets_url"], worksheet=worksheet_name, ttl=0)
    except Exception as e:
        # Se a aba estiver vazia ou não existir, criamos o esqueleto
        if worksheet_name == "users":
            return pd.DataFrame(columns=["username", "password", "role", "pergunta_seg", "resposta_seg"])
        return pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

def save_data(df, worksheet_name):
    try:
        conn.update(spreadsheet=st.secrets["gsheets_url"], worksheet=worksheet_name, data=df)
        st.cache_data.clear() # Limpa o cache para a próxima leitura ser atualizada
    except Exception as e:
        st.error(f"Erro ao salvar no Sheets: {e}")

# --- FUNÇÕES DE SEGURANÇA ---
def hash_pw(pw): return hashlib.sha256(str.encode(pw)).hexdigest()

# Carregar usuários
df_users = get_data("users")

# Criar Gustavo Meneses automaticamente se a planilha estiver limpa
if "Gustavo Meneses" not in df_users['username'].values:
    admin_data = pd.DataFrame([{
        "username": "Gustavo Meneses", 
        "password": hash_pw("1234"), 
        "role": "admin", 
        "pergunta_seg": "Qual o nome da sua empresa?", 
        "resposta_seg": hash_pw("CRM")
    }])
    df_users = pd.concat([df_users, admin_data], ignore_index=True)
    save_data(df_users, "users")

# ... (restante do código de login e IA)
