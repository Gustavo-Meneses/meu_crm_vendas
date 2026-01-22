import streamlit as st
import pandas as pd
from mistralai import Mistral
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão Comercial Inteligente", layout="wide", page_icon="🏢")

# --- INICIALIZAÇÃO DO BANCO DE DADOS EM MEMÓRIA ---
if 'df_leads' not in st.session_state:
    st.session_state.df_leads = pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

if 'usuarios_db' not in st.session_state:
    st.session_state.usuarios_db = {"ADM": "1234"}

if 'logado' not in st.session_state:
    st.session_state.logado = False

if 'usuario_atual' not in st.session_state:
    st.session_state.usuario_atual = None

# --- FUNÇÃO IA (MISTRAL AI) ---
def processar_com_mistral(texto_entrada):
    try:
        api_key = st.secrets.get("MISTRAL_API_KEY")
        if not api_key:
            return "ERRO_CONFIG: Chave MISTRAL_API_KEY não encontrada nos Secrets."
        
        client = Mistral(api_key=api_key)
        
        prompt_sistema = (
            "Você é um analista de dados comerciais experiente. Sua tarefa é extrair informações de leads e retornar APENAS um JSON puro. "
            "Campos obrigatórios: nome, empresa, status (Prospecção, Reunião, Proposta, Fechado, Perdido), "
            "historico (resumo executivo), score (0-100) e valor (numérico puro). "
            "Não adicione texto explicativo, apenas o objeto JSON."
        )

        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Extraia os dados deste lead: {texto_entrada}"}
            ],
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"ERRO_API: {str(e)}"

# --- INTERFACE DE ACESSO (LOGIN E CADASTRO) ---
if not st.session_state.logado:
    st.markdown("<h2 style='text-align: center;'>Acesso ao Sistema de Gestão Comercial</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Portal Administrativo de Alta Performance</p>", unsafe_allow_html=True)
    
    tab_login, tab_cadastro = st.tabs(["🔐 Entrar", "📝 Criar Nova Conta"])
    
    with tab_login:
        _, col_l, _ = st.columns([1, 1, 1])
        with col_l:
            u_login = st.text_input("Usuário", key="login_user")
            p_login = st.text_input("Senha", type="password", key="login_pass")
            if st.button("Autenticar", use_container_width=True):
                if u_login in st.session_state.usuarios_db and st.session_state.usuarios_db[u_login] == p_login:
                    st.session_state.logado = True
                    st.session_state.usuario_atual = u_login
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")

    with tab_cadastro:
        _, col_c, _ = st.columns([1, 1, 1])
        with col_c:
            st.info("O cadastro é válido apenas para a sessão atual.")
            u_novo = st.text_input("Defina um Usuário", key="new_user")
            p_novo = st.text_input("Defina uma Senha", type="password", key="new_pass")
            p_conf = st.text_input("Confirme a Senha", type="password", key="conf_pass")
            
            if st.button("Finalizar Cadastro", use_container_width=True):
                if not u_novo or not p_novo:
                    st.warning("Preencha todos os campos obrigatórios.")
                elif u_novo in st.session_state.usuarios_db:
                    st.error("Este usuário já está registrado.")
                elif p_novo != p_conf:
                    st.error("As senhas digitadas não coincidem.")
                else:
                    st.session_state.usuarios_db[u_novo] = p_novo
                    st.success("Conta criada! Você já pode realizar o login.")

# --- APP PRINCIPAL (SISTEMA LOGADO) ---
else:
    st.sidebar.title("🏢 Painel de Controle")
    st.sidebar.markdown(f"Conectado como: **{st.session_state.usuario_atual}**")
    
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard Visual", "➕ Capturar Lead (IA)"])
    
    st.sidebar.divider()
    if st.sidebar.button("Encerrar Sessão"):
        st.session_state.logado = False
        st.rerun()

    # --- ABA: DASHBOARD ---
    if menu == "📊 Dashboard Visual":
        st.header("📊 Inteligência e Performance de Vendas")
        
        if not st.session_state.df_leads.empty:
            df = st.session_state.df_leads.copy()
            # Conversão para garantir funcionamento dos gráficos
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
            df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(0)

            # --- LINHA 1: MÉTRICAS DE IMPACTO ---
            m1, m2, m3 = st.columns(3)
            m1.metric("Leads Totais", len(df))
            m2.metric("Pipeline Financeiro", f"R$ {df['valor'].sum():,.2f}")
            m3.metric("Qualidade Média", f"{df['score'].mean():.1f} pts")

            st.divider()

            # --- LINHA 2: ANÁLISE GRÁFICA (PARA PRINTS E APRESENTAÇÃO) ---
            g1, g2 = st.columns(2)

            with g1:
                st.subheader("🎯 Saúde do Funil (Status)")
                status_dist = df['status'].value_counts()
                st.bar_chart(status_dist, color="#2E86C1")

            with g2:
                st.subheader("💰 Maiores Oportunidades (R$)")
                df_top = df.sort_values('valor', ascending=False).head(8)
                st.bar_chart(data=df_top, x='empresa', y='valor', color="#28B463")

            st.divider()
            
            # --- TABELA DE DADOS ---
            st.subheader("📋 Relatório Detalhado")
            st.dataframe(df, use_container_width=True)
            
            # Exportação para Power BI / Excel
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exportar para Power BI (CSV)", csv, "relatorio_crm_ia.csv", "text/csv")
        else:
            st.info("O sistema ainda não possui dados. Capture um lead via IA para gerar os indicadores.")

    # --- ABA: CAPTURA IA ---
    elif menu == "➕ Capturar Lead (IA)":
        st.header("⚡ Extração de Dados com IA")
        st.write("Insira textos de reuniões, e-mails ou WhatsApp para converter em dados estruturados.")
        
        texto_input = st.text_area("Notas do Lead:", height=250, placeholder="Ex: Falei com o João da Empresa X, ele quer um projeto de 10 mil...")
        
        if st.button("Processar e Registrar"):
            if texto_input:
                with st.spinner("A Mistral AI está estruturando os dados..."):
                    resultado = processar_com_mistral(texto_input)
                    
                    if "ERRO" in resultado:
                        st.error(f"Falha na captura: {resultado}")
                    else:
                        try:
                            dados_json = json.loads(resultado)
                            # Adiciona ao histórico da sessão
                            st.session_state.df_leads = pd.concat([
                                st.session_state.df_leads, 
                                pd.DataFrame([dados_json])
                            ], ignore_index=True)
                            
                            st.success("Lead registrado com sucesso no Dashboard!")
                            st.balloons()
                            st.json(dados_json)
                        except:
                            st.error("Erro ao converter resposta da IA em tabela.")
                            st.code(resultado)
            else:
                st.warning("Por favor, insira algum texto para análise.")
