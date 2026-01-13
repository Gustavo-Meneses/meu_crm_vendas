import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="CRM Inteligente Pro", layout="wide", page_icon="🚀")

# --- INICIALIZAÇÃO DE DADOS (SESSION STATE) ---
# Garante que as variáveis existam na memória do navegador
if 'df_leads' not in st.session_state:
    st.session_state.df_leads = pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- FUNÇÃO DE INTELIGÊNCIA ARTIFICIAL ---
def processar_lead_com_ia(texto_usuario):
    try:
        # Configuração da API usando a chave dos Secrets
        if "GEMINI_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_KEY"])
        else:
            return "ERRO_CONFIG: Chave GEMINI_KEY não encontrada nos Secrets."

        # Inicializa o modelo (Versão Flash é mais rápida e barata)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prompt otimizado para JSON
        prompt_sistema = (
            "Você é um assistente de vendas. Analise o texto abaixo e extraia os dados para um CRM. "
            "Retorne APENAS um objeto JSON válido, sem crases (```) e sem a palavra json. "
            "Campos obrigatórios: 'nome', 'empresa', 'status' (ex: Prospecção, Negociação, Fechado), "
            "'historico' (resumo de 1 frase), 'score' (inteiro 0-100) e 'valor' (número decimal ou 0). "
            f"Texto do usuário: {texto_usuario}"
        )
        
        # Chamada à API
        response = model.generate_content(prompt_sistema)
        return response.text

    except Exception as e:
        return f"ERRO_IA: {str(e)}"

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.title("🔐 Acesso CRM")
        st.markdown("---")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        
        if st.button("Entrar no Sistema", use_container_width=True):
            # Validação simples (Pode ser alterada conforme necessidade)
            if usuario == "Gustavo Meneses" and senha == "1234":
                st.session_state.logado = True
                st.success("Login realizado!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

# --- TELA DO SISTEMA (DASHBOARD) ---
else:
    # Barra Lateral
    st.sidebar.title(f"👤 Olá, Gustavo")
    st.sidebar.markdown("---")
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Adicionar Lead (IA)", "⚙️ Configurações"])
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # Aba: Dashboard
    if menu == "📊 Dashboard":
        st.header("Pipeline de Vendas")
        
        if not st.session_state.df_leads.empty:
            df = st.session_state.df_leads
            
            # Cards de Métricas
            c1, c2, c3 = st.columns(3)
            val_total = pd.to_numeric(df['valor'], errors='coerce').fillna(0).sum()
            ticket_medio = val_total / len(df) if len(df) > 0 else 0
            
            c1.metric("💰 Valor em Pipeline", f"R$ {val_total:,.2f}")
            c2.metric("👥 Total de Leads", len(df))
            c3.metric("📈 Ticket Médio", f"R$ {ticket_medio:,.2f}")
            
            st.divider()
            
            # Tabela Principal
            st.subheader("Lista de Leads")
            st.dataframe(df, use_container_width=True)
            
            # Botão de Download (Backup)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Backup (CSV)",
                data=csv,
                file_name="meus_leads.csv",
                mime="text/csv",
            )
        else:
            st.info("Nenhum lead cadastrado nesta sessão. Vá para a aba 'Adicionar Lead' para começar.")

    # Aba: Adicionar Lead
    elif menu == "➕ Adicionar Lead (IA)":
        st.header("Captura Inteligente de Leads")
        st.markdown("Cole abaixo a transcrição de uma reunião, e-mail ou conversa de WhatsApp.")
        
        texto_input = st.text_area("Texto do Lead:", height=200, placeholder="Ex: O cliente João da Silva da Padaria Central quer comprar 2 fornos...")
        
        col_btn1, col_btn2 = st.columns([1, 4])
        if col_btn1.button("⚡ Processar", type="primary"):
            if texto_input:
                with st.spinner("A Inteligência Artificial está analisando..."):
                    resultado = processar_lead_com_ia(texto_input)
                    
                    # Tratamento de Erros e Sucesso
                    if "ERRO_" in resultado:
                        st.error("Falha no processamento.")
                        st.warning("Verifique se o arquivo 'requirements.txt' foi criado no GitHub com 'google-generativeai>=0.7.0'")
                        st.code(resultado)
                    else:
                        try:
                            # Limpeza da resposta da IA para evitar erros de formatação
                            json_limpo = resultado.replace("```json", "").replace("```", "").strip()
                            dados_lead = json.loads(json_limpo)
                            
                            # Adiciona o novo lead ao topo da tabela
                            novo_df = pd.DataFrame([dados_lead])
                            st.session_state.df_leads = pd.concat([novo_df, st.session_state.df_leads], ignore_index=True)
                            
                            st.success("Lead capturado com sucesso!")
                            st.balloons()
                        except json.JSONDecodeError:
                            st.error("A IA entendeu o texto, mas não retornou um formato válido.")
                            st.expander("Ver resposta bruta").text(resultado)
            else:
                st.warning("Por favor, digite ou cole um texto primeiro.")

    # Aba: Configurações (Apenas Informativo)
    elif menu == "⚙️ Configurações":
        st.header("Status do Sistema")
        st.success("Sistema Operando em Modo Memória (Rápido)")
        st.info("Nota: Os dados são apagados ao recarregar a página (F5). Lembre-se de baixar o CSV no Dashboard.")
