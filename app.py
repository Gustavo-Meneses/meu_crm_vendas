import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="CRM Inteligente Pro", layout="wide", page_icon="🚀")

# --- INICIALIZAÇÃO DE DADOS (SESSION STATE) ---
if 'df_leads' not in st.session_state:
    st.session_state.df_leads = pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- FUNÇÃO DE INTELIGÊNCIA ARTIFICIAL ---
def processar_com_ia(texto_entrada):
    try:
        # Pega a chave dos Secrets
        api_key = st.secrets.get("GEMINI_KEY")
        if not api_key:
            return "ERRO_CONFIG: Chave GEMINI_KEY não configurada nos Secrets."
        
        genai.configure(api_key=api_key)
        
        # Inicializa o modelo (gemini-1.5-flash)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = (
            "Atue como um analista de CRM. Extraia do texto: nome, empresa, status, historico, score e valor. "
            "Responda APENAS o JSON puro, sem blocos de código markdown. "
            f"Texto: {texto_entrada}"
        )
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"ERRO_API: {str(e)}"

# --- INTERFACE DE LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Acesso ao CRM")
    st.info(f"Versão da Biblioteca: {genai.__version__}") # Para conferirmos se atualizou
    
    usuario = st.text_input("Usuário Admin")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if usuario == "Gustavo Meneses" and senha == "1234":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

# --- APP PRINCIPAL (APÓS LOGIN) ---
else:
    st.sidebar.title(f"👤 Olá, Gustavo")
    st.sidebar.write(f"SDK Version: {genai.__version__}")
    aba = st.sidebar.radio("Navegação", ["Dashboard", "Adicionar Lead (IA)"])
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if aba == "Dashboard":
        st.header("📊 Leads na Sessão Atual")
        if not st.session_state.df_leads.empty:
            st.dataframe(st.session_state.df_leads, use_container_width=True)
            
            # Botão de Exportação para não perder os dados
            csv = st.session_state.df_leads.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Leads (CSV)", csv, "leads.csv", "text/csv")
        else:
            st.info("Nenhum lead capturado ainda.")

    elif aba == "Adicionar Lead (IA)":
        st.header("🪄 Captura Inteligente")
        txt = st.text_area("Cole aqui o e-mail ou conversa do lead:", height=150)
        
        if st.button("🚀 Processar e Salvar"):
            if txt:
                with st.spinner("IA analisando dados..."):
                    resultado = processar_com_ia(txt)
                    
                    if "ERRO_API" in resultado:
                        st.error(f"Erro na IA: {resultado}")
                        st.warning("Se o erro 404 persistir, delete o app no painel do Streamlit e crie de novo.")
                    else:
                        try:
                            # Limpeza de caracteres especiais da resposta da IA
                            json_limpo = resultado.strip().replace('```json', '').replace('```', '')
                            dados = json.loads(json_limpo)
                            
                            # Adiciona ao DataFrame
                            novo_lead = pd.DataFrame([dados])
                            st.session_state.df_leads = pd.concat([st.session_state.df_leads, novo_lead], ignore_index=True)
                            
                            st.success("Lead capturado com sucesso!")
                            st.balloons()
                        except Exception as e:
                            st.error("A IA respondeu, mas não conseguimos ler o formato.")
                            st.code(resultado)
