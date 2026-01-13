import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="CRM Inteligente Pro", layout="wide", page_icon="🚀")

# --- INICIALIZAÇÃO DE DADOS ---
if 'df_leads' not in st.session_state:
    st.session_state.df_leads = pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- FUNÇÃO IA REVISADA ---
def processar_ia(texto_entrada):
    try:
        # Configura a chave vinda dos Secrets
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        
        # Usamos apenas o nome do modelo sem prefixos para evitar o erro 404 de versão
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = (
            "Extraia os dados comerciais do texto para JSON puro. "
            "Campos: nome, empresa, status, historico, score, valor. "
            f"Texto: {texto_entrada}"
        )
        
        # Chamada simplificada
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"ERRO_API: {str(e)}"

# --- LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Login CRM")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Acessar"):
        if u == "Gustavo Meneses" and p == "1234":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Dados incorretos.")

# --- APP PRINCIPAL ---
else:
    menu = st.sidebar.radio("Navegação", ["Dashboard", "Adicionar Lead"])
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if menu == "Dashboard":
        st.header("📊 Leads na Memória")
        if not st.session_state.df_leads.empty:
            st.dataframe(st.session_state.df_leads, use_container_width=True)
            csv = st.session_state.df_leads.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar CSV", csv, "leads.csv")
        else:
            st.info("Nenhum lead capturado.")

    elif menu == "Adicionar Lead":
        st.header("🪄 Captura Inteligente")
        txt = st.text_area("Notas do lead:", height=150)
        
        if st.button("Processar e Salvar"):
            with st.spinner("IA Analisando..."):
                resultado = processar_ia(txt)
                
                if "ERRO_API" in resultado:
                    st.error(f"Erro na API: {resultado}")
                else:
                    try:
                        # Limpa qualquer formatação markdown (```json ...)
                        limpo = resultado.strip().replace('```json', '').replace('```', '')
                        dados = json.loads(limpo)
                        
                        # Adiciona à tabela na memória
                        st.session_state.df_leads = pd.concat([
                            st.session_state.df_leads, 
                            pd.DataFrame([dados])
                        ], ignore_index=True)
                        
                        st.success("Lead salvo com sucesso!")
                        st.balloons()
                    except:
                        st.error("A IA respondeu, mas os dados não estão no formato correto.")
                        st.code(resultado)
