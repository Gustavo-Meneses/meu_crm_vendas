import streamlit as st
import pandas as pd
import google.generativeai as genai
import hashlib
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gemini CRM - Estável", layout="wide", page_icon="🚀")

# --- DATABASE EM MEMÓRIA ---
if 'df_leads' not in st.session_state:
    st.session_state.df_leads = pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

# --- FUNÇÃO IA (CORREÇÃO DO ERRO 404) ---
def extrair_dados_ia(texto_entrada):
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        # Usamos apenas o nome do modelo. A biblioteca resolve o caminho 'models/' internamente.
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = (
            "Extraia os dados comerciais do texto abaixo para um formato JSON. "
            "Responda APENAS o JSON puro, sem markdown ou explicações. "
            "Campos: {'nome', 'empresa', 'status', 'historico', 'score', 'valor'}. "
            f"Texto: {texto_entrada}"
        )
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"ERRO_API: {str(e)}"

# --- INTERFACE ---
st.title("🚀 CRM Inteligente - Modo Estável")

menu = st.sidebar.radio("Navegação", ["Dashboard", "Adicionar Lead (IA)"])

if menu == "Dashboard":
    st.header("📊 Leads na Sessão Atual")
    if not st.session_state.df_leads.empty:
        st.dataframe(st.session_state.df_leads, use_container_width=True)
        # Botão para não perder os dados de teste
        csv = st.session_state.df_leads.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Leads em CSV", csv, "leads_teste.csv", "text/csv")
    else:
        st.info("Nenhum lead capturado ainda. Vá em 'Adicionar Lead' para testar.")

elif menu == "Adicionar Lead (IA)":
    st.header("🪄 Captura Inteligente")
    txt = st.text_area("Cole o texto do lead aqui:", height=150)
    
    if st.button("Processar e Salvar"):
        if txt:
            with st.spinner("IA analisando..."):
                resultado = extrair_dados_ia(txt)
                
                if "ERRO_API" in resultado:
                    st.error(f"Erro de Conexão/API: {resultado}")
                    st.info("Dica: Verifique se sua GEMINI_KEY nos Secrets está correta.")
                else:
                    try:
                        # Limpeza de caracteres que a IA às vezes envia por engano
                        json_limpo = resultado.strip().replace('```json', '').replace('```', '')
                        dados = json.loads(json_limpo)
                        
                        # Adiciona ao DataFrame em memória
                        novo_lead = pd.DataFrame([dados])
                        st.session_state.df_leads = pd.concat([st.session_state.df_leads, novo_lead], ignore_index=True)
                        
                        st.success("Lead adicionado com sucesso!")
                        st.balloons()
                    except Exception as e:
                        st.error("A IA respondeu, mas os dados vieram em formato inválido.")
                        st.code(resultado)
