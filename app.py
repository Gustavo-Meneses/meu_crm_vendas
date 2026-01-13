import streamlit as st
import pandas as pd
import google.generativeai as genai
import hashlib
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="CRM Inteligente Pro", layout="wide", page_icon="🚀")

# --- INICIALIZAÇÃO DO BANCO DE DADOS EM MEMÓRIA ---
if 'df_leads' not in st.session_state:
    st.session_state.df_leads = pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- FUNÇÃO DE INTELIGÊNCIA ARTIFICIAL ---
def processar_com_gemini(texto_bruto):
    try:
        # Configura a API com a chave dos Secrets
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        
        # Seleciona o modelo (nome simplificado para evitar erro 404)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prompt ultra-específico para garantir retorno JSON puro
        prompt = (
            "Você é um assistente de CRM especializado. Extraia as seguintes informações do texto: "
            "nome, empresa, status (escolha entre: Prospecção, Reunião, Proposta, Fechado, Perdido), "
            "historico (resumo curto), score (0 a 100) e valor (numérico). "
            "Responda APENAS um objeto JSON puro, sem marcações de markdown ou blocos de código. "
            f"Texto para analisar: {texto_bruto}"
        )
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"ERRO_SISTEMA: {str(e)}"

# --- LÓGICA DE LOGIN SIMPLIFICADA ---
if not st.session_state.logado:
    st.title("🔐 Acesso ao CRM")
    usuario = st.text_input("Usuário Admin")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        # Login padrão para teste rápido
        if usuario == "Gustavo Meneses" and senha == "1234":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
else:
    # --- INTERFACE PRINCIPAL ---
    st.sidebar.title(f"👤 Olá, Gustavo")
    aba = st.sidebar.radio("Navegação", ["Dashboard", "Adicionar Lead (IA)"])
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if aba == "Dashboard":
        st.header("📊 Funil de Vendas (Sessão Atual)")
        
        if not st.session_state.df_leads.empty:
            # Métricas rápidas
            col1, col2 = st.columns(2)
            total_valor = pd.to_numeric(st.session_state.df_leads['valor'], errors='coerce').sum()
            col1.metric("Pipeline Total", f"R$ {total_valor:,.2f}")
            col2.metric("Total de Leads", len(st.session_state.df_leads))
            
            # Tabela de Dados
            st.dataframe(st.session_state.df_leads, use_container_width=True)
            
            # Gráfico simples
            st.bar_chart(st.session_state.df_leads['status'].value_counts())
            
            # Botão de Exportação (Importante para não perder os dados da sessão)
            csv = st.session_state.df_leads.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Planilha (CSV)", csv, "meus_leads.csv", "text/csv")
        else:
            st.info("Nenhum lead cadastrado nesta sessão. Vá para 'Adicionar Lead' para começar!")

    elif aba == "Adicionar Lead (IA)":
        st.header("🪄 Captura de Lead com Inteligência Artificial")
        st.write("Cole abaixo e-mails, conversas ou notas de reuniões.")
        
        input_texto = st.text_area("Texto do Lead:", height=200, placeholder="Ex: Falei com o Marcos da TechSolutions hoje. Ele quer uma consultoria de 5000 reais...")
        
        if st.button("🚀 Processar com Gemini"):
            if input_texto:
                with st.spinner("Analisando dados com IA..."):
                    resposta_ia = processar_com_gemini(input_texto)
                    
                    if "ERRO_SISTEMA" in resposta_ia:
                        st.error(f"Erro na comunicação: {resposta_ia}")
                    else:
                        try:
                            # Limpeza de possíveis caracteres extras da resposta
                            dados_json = json.loads(resposta_ia.replace('```json', '').replace('```', '').strip())
                            
                            # Adicionar ao DataFrame
                            novo_lead = pd.DataFrame([dados_json])
                            st.session_state.df_leads = pd.concat([st.session_state.df_leads, novo_lead], ignore_index=True)
                            
                            st.success("Lead identificado e salvo com sucesso!")
                            st.balloons()
                            st.json(dados_json) # Mostra o que foi extraído
                        except Exception as e:
                            st.error("A IA respondeu, mas não conseguimos processar o formato dos dados.")
                            st.code(resposta_ia)
            else:
                st.warning("Por favor, insira um texto para análise.")
