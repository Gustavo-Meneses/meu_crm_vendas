import streamlit as st
import pandas as pd
from mistralai import Mistral
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="CRM Inteligente Mistral", layout="wide", page_icon="⚡")

# --- INICIALIZAÇÃO DE DADOS EM MEMÓRIA ---
if 'df_leads' not in st.session_state:
    st.session_state.df_leads = pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- FUNÇÃO IA (MISTRAL AI) ---
def processar_com_mistral(texto_entrada):
    try:
        api_key = st.secrets.get("MISTRAL_API_KEY")
        if not api_key:
            return "ERRO_CONFIG: Chave MISTRAL_API_KEY não encontrada nos Secrets."
        
        client = Mistral(api_key=api_key)
        
        # Modelo mistral-small é ótimo para tarefas de extração
        model = "mistral-small-latest"
        
        prompt_sistema = (
            "Você é um assistente de CRM. Sua tarefa é extrair dados de textos e retornar APENAS um JSON puro. "
            "Campos: nome, empresa, status (Prospecção, Reunião, Proposta, Fechado, Perdido), "
            "historico (um resumo curto), score (0-100) e valor (numérico). "
            "Não responda nada além do JSON."
        )

        response = client.chat.complete(
            model=model,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Extraia os dados deste lead: {texto_entrada}"}
            ],
            response_format={"type": "json_object"} # Garante o formato JSON
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"ERRO_API: {str(e)}"

# --- INTERFACE DE LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Login CRM - Mistral Edition")
    u = st.text_input("Usuário Admin")
    p = st.text_input("Senha", type="password")
    
    if st.button("Acessar Sistema"):
        if u == "Gustavo Meneses" and p == "1234":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Credenciais inválidas.")

# --- APP PRINCIPAL ---
else:
    st.sidebar.title(f"👤 Gustavo Meneses")
    aba = st.sidebar.radio("Navegação", ["Dashboard", "Adicionar Lead (IA)"])
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if aba == "Dashboard":
        st.header("📊 Funil de Leads")
        if not st.session_state.df_leads.empty:
            # Métricas Básicas
            total_leads = len(st.session_state.df_leads)
            valor_total = pd.to_numeric(st.session_state.df_leads['valor'], errors='coerce').sum()
            
            c1, c2 = st.columns(2)
            c1.metric("Leads Capturados", total_leads)
            c2.metric("Volume em Propostas", f"R$ {valor_total:,.2f}")
            
            st.divider()
            st.dataframe(st.session_state.df_leads, use_container_width=True)
            
            # Download
            csv = st.session_state.df_leads.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exportar para Excel (CSV)", csv, "leads_mistral.csv", "text/csv")
        else:
            st.info("Nenhum lead em memória. Use a captura por IA.")

    elif aba == "Adicionar Lead (IA)":
        st.header("⚡ Captura Inteligente com Mistral AI")
        st.markdown("Cole abaixo o texto (e-mail, nota ou WhatsApp) para converter em lead.")
        
        txt = st.text_area("Texto do Lead:", height=200, placeholder="Ex: Falei com o Carlos da empresa ABC...")
        
        if st.button("🚀 Processar com IA"):
            if txt:
                with st.spinner("Mistral está analisando..."):
                    resultado = processar_com_mistral(txt)
                    
                    if "ERRO_API" in resultado:
                        st.error(f"Erro na conexão com a Mistral: {resultado}")
                    else:
                        try:
                            # Converte a resposta para dicionário Python
                            dados = json.loads(resultado)
                            
                            # Adiciona ao DataFrame da sessão
                            st.session_state.df_leads = pd.concat([
                                st.session_state.df_leads, 
                                pd.DataFrame([dados])
                            ], ignore_index=True)
                            
                            st.success("Lead identificado e salvo na memória!")
                            st.balloons()
                            st.json(dados)
                        except Exception as e:
                            st.error("A IA respondeu, mas não conseguimos processar o JSON.")
                            st.code(resultado)
            else:
                st.warning("Por favor, insira o texto antes de processar.")
