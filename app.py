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
        
        # Modelo estável para extração de JSON
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
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"ERRO_API: {str(e)}"

# --- INTERFACE DE LOGIN (USUÁRIO ADM) ---
if not st.session_state.logado:
    st.title("🔐 Login CRM - Acesso Restrito")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    
    if st.button("Acessar Sistema"):
        # Alterado para usuário 'ADM' conforme solicitado
        if u == "ADM" and p == "1234":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Credenciais inválidas. Verifique usuário e senha.")

# --- APP PRINCIPAL (SISTEMA LOGADO) ---
else:
    st.sidebar.title(f"👤 Painel ADM")
    aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Adicionar Lead (IA)"])
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Sair do Sistema"):
        st.session_state.logado = False
        st.rerun()

    if aba == "📊 Dashboard":
        st.header("📊 Funil de Leads")
        if not st.session_state.df_leads.empty:
            # Métricas no topo
            total_leads = len(st.session_state.df_leads)
            valor_total = pd.to_numeric(st.session_state.df_leads['valor'], errors='coerce').sum()
            
            c1, c2 = st.columns(2)
            c1.metric("Leads Capturados", total_leads)
            c2.metric("Volume Financeiro", f"R$ {valor_total:,.2f}")
            
            st.divider()
            st.dataframe(st.session_state.df_leads, use_container_width=True)
            
            # Exportação de segurança
            csv = st.session_state.df_leads.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exportar Leads (CSV)", csv, "meus_leads_mistral.csv", "text/csv")
        else:
            st.info("O pipeline está vazio. Utilize a aba de captura para registrar novos leads.")

    elif aba == "➕ Adicionar Lead (IA)":
        st.header("⚡ Captura de Lead com Mistral AI")
        st.markdown("Cole o texto bruto (e-mail, WhatsApp ou notas) para estruturar o lead.")
        
        txt = st.text_area("Notas do Lead:", height=200, placeholder="Ex: O Carlos da ABC S.A. quer fechar um projeto de 10k...")
        
        if st.button("🚀 Processar com IA"):
            if txt:
                with st.spinner("Analisando com Mistral AI..."):
                    resultado = processar_com_mistral(txt)
                    
                    if "ERRO_API" in resultado:
                        st.error(f"Erro: {resultado}")
                    else:
                        try:
                            dados = json.loads(resultado)
                            # Salva no DataFrame da sessão
                            st.session_state.df_leads = pd.concat([
                                st.session_state.df_leads, 
                                pd.DataFrame([dados])
                            ], ignore_index=True)
                            
                            st.success("Lead identificado e adicionado ao Dashboard!")
                            st.balloons()
                            st.json(dados)
                        except Exception:
                            st.error("A IA respondeu, mas os dados vieram em formato corrompido.")
                            st.code(resultado)
            else:
                st.warning("Por favor, preencha o campo de texto.")
