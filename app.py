import streamlit as st
import pandas as pd
import google.generativeai as genai
import hashlib
import json

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Gemini CRM - Memory Mode", layout="wide", page_icon="🚀")

# --- INICIALIZAÇÃO DA BASE DE DADOS (EM MEMÓRIA) ---
if 'df_users' not in st.session_state:
    admin_pw = hashlib.sha256(str.encode("1234")).hexdigest()
    st.session_state.df_users = pd.DataFrame([{
        "username": "Gustavo Meneses", 
        "password": admin_pw, 
        "role": "admin", 
        "pergunta_seg": "Empresa?", 
        "resposta_seg": hashlib.sha256(str.encode("crm")).hexdigest()
    }])

if 'df_leads' not in st.session_state:
    st.session_state.df_leads = pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

# --- FUNÇÕES DE APOIO ---
def hash_pw(pw): 
    return hashlib.sha256(str.encode(pw)).hexdigest()

def chamar_ia(prompt_text):
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        # Mudança estratégica: Tentando o nome direto do modelo estável
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Forçamos a IA a não usar blocos de código markdown (```json)
        prompt_completo = f"Extraia os dados do texto abaixo e retorne APENAS um objeto JSON puro, sem textos extras ou formatação markdown. Campos: {{'nome','empresa','status','historico','score','valor'}}. Texto: {prompt_text}"
        
        response = model.generate_content(prompt_completo)
        return response.text
    except Exception as e:
        return f"ERRO_SISTEMA: {str(e)}"

# --- INTERFACE DE ACESSO ---
if 'logado' not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🚀 CRM Inteligente - Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type='password')
    if st.button("Acessar"):
        users = st.session_state.df_users
        user_row = users[users['username'] == u]
        if not user_row.empty and user_row.iloc[0]['password'] == hash_pw(p):
            st.session_state.logado = True
            st.session_state.user_name = u
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
else:
    # --- SISTEMA PRINCIPAL ---
    st.sidebar.title(f"👤 {st.session_state.user_name}")
    menu = st.sidebar.radio("Navegação", ["Dashboard", "Adicionar Lead (IA)"])
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if menu == "Dashboard":
        st.header("📊 Painel de Controle")
        if not st.session_state.df_leads.empty:
            st.dataframe(st.session_state.df_leads, use_container_width=True)
            st.write("### Volume por Status")
            st.bar_chart(st.session_state.df_leads['status'].value_counts())
        else:
            st.info("Nenhum lead em memória. Use a aba 'Adicionar Lead' para começar.")

    elif menu == "Adicionar Lead (IA)":
        st.header("🪄 Captura de Lead via IA")
        txt = st.text_area("Cole aqui as notas ou conversa do lead:", height=150)
        
        if st.button("Processar e Salvar"):
            if txt:
                with st.spinner("A IA está analisando os dados..."):
                    res = chamar_ia(txt)
                    
                    if "ERRO_SISTEMA" in res:
                        st.error(f"Erro na API do Google: {res}")
                    else:
                        try:
                            # Limpeza de possíveis formatações markdown extras
                            json_limpo = res.replace('```json', '').replace('```', '').strip()
                            dados = json.loads(json_limpo)
                            
                            # Adiciona ao banco de dados em memória
                            novo_df = pd.DataFrame([dados])
                            st.session_state.df_leads = pd.concat([st.session_state.df_leads, novo_df], ignore_index=True)
                            
                            st.success("Lead processado e salvo com sucesso!")
                            st.balloons()
                        except Exception as e:
                            st.error("A IA retornou os dados, mas não conseguimos processar o formato.")
                            st.text("Resposta da IA:")
                            st.code(res)
            else:
                st.warning("Por favor, insira algum texto antes de processar.")
