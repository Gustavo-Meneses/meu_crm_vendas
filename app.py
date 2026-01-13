import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="CRM Inteligente Pro", layout="wide", page_icon="🚀")

# --- INICIALIZAÇÃO (SESSION STATE) ---
if 'df_leads' not in st.session_state:
    st.session_state.df_leads = pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- FUNÇÃO IA INTELIGENTE (COM FALLBACK) ---
def processar_lead_com_ia(texto_usuario):
    # Configuração da API
    if "GEMINI_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
    else:
        return "ERRO_CONFIG: Chave GEMINI_KEY não encontrada."

    # Prompt Padrão
    prompt_sistema = (
        "Analise o texto e extraia para JSON puro: nome, empresa, status (Prospecção/Fechado/etc), "
        "historico (resumo), score (0-100) e valor (número). "
        f"Texto: {texto_usuario}"
    )

    # TENTATIVA 1: Modelo Rápido (Gemini 1.5 Flash)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt_sistema)
        return response.text
    except Exception as e_flash:
        # TENTATIVA 2: Modelo Compatível (Gemini Pro - Funciona em versões antigas)
        try:
            # st.warning(f"Tentando modelo de backup... Erro original: {e_flash}") # Opcional para debug
            model_backup = genai.GenerativeModel('gemini-pro')
            response = model_backup.generate_content(prompt_sistema)
            return response.text
        except Exception as e_pro:
            return f"ERRO_TOTAL: Falha em ambos os modelos. Flash: {e_flash} | Pro: {e_pro}"

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Acesso CRM (Versão Híbrida)")
    st.info(f"Versão da Biblioteca Google Instalada: {genai.__version__}") # Isso vai nos mostrar se atualizou ou não
    
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if usuario == "Gustavo Meneses" and senha == "1234":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Dados incorretos.")

# --- TELA PRINCIPAL ---
else:
    st.sidebar.title("Navegação")
    menu = st.sidebar.radio("Ir para:", ["Dashboard", "Adicionar Lead"])
    st.sidebar.write(f"Lib Google: {genai.__version__}") # Debug visual
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if menu == "Dashboard":
        st.header("📊 Pipeline de Vendas")
        if not st.session_state.df_leads.empty:
            st.dataframe(st.session_state.df_leads, use_container_width=True)
            csv = st.session_state.df_leads.to_csv(index=False).encode('utf-8')
            st.download_button("💾 Baixar CSV", csv, "leads.csv")
        else:
            st.info("Lista vazia.")

    elif menu == "Adicionar Lead":
        st.header("⚡ Captura de Lead")
        txt = st.text_area("Texto do Lead:", height=150)
        
        if st.button("Processar"):
            if txt:
                with st.spinner("IA processando..."):
                    res = processar_lead_com_ia(txt)
                    
                    if "ERRO_" in res:
                        st.error("Erro na IA. Veja detalhes abaixo:")
                        st.code(res)
                    else:
                        try:
                            # Limpeza agressiva do JSON
                            json_str = res.replace("```json", "").replace("```", "").strip()
                            if json_str.startswith("json"): json_str = json_str[4:] # Remove prefixo solto
                            
                            dados = json.loads(json_str)
                            st.session_state.df_leads = pd.concat([pd.DataFrame([dados]), st.session_state.df_leads], ignore_index=True)
                            st.success("Lead salvo!")
                            st.balloons()
                        except:
                            st.error("IA respondeu, mas formato inválido.")
                            st.code(res)
