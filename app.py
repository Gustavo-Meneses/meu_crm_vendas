import streamlit as st
import pandas as pd
from mistralai import Mistral
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão Comercial Inteligente", layout="wide", page_icon="🏢")

# --- INICIALIZAÇÃO DO BANCO DE DADOS EM MEMÓRIA ---
# Adicionada a coluna 'id' como identificador único
if 'df_leads' not in st.session_state:
    st.session_state.df_leads = pd.DataFrame(columns=["id", "nome", "empresa", "status", "historico", "score", "valor"])

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
            return "ERRO_CONFIG: Chave MISTRAL_API_KEY não encontrada."
        
        client = Mistral(api_key=api_key)
        
        prompt_sistema = (
            "Você é um analista comercial. Extraia do texto e retorne APENAS um JSON puro. "
            "Campos: nome, empresa, status (Prospecção, Reunião, Proposta, Fechado, Perdido), "
            "historico (resumo curto), score (0-100) e valor (numérico puro)."
        )

        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Extraia os dados: {texto_entrada}"}
            ],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERRO_API: {str(e)}"

# --- INTERFACE DE ACESSO ---
if not st.session_state.logado:
    st.markdown("<h2 style='text-align: center;'>Acesso ao Sistema de Gestão Comercial</h2>", unsafe_allow_html=True)
    
    tab_login, tab_cadastro = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
    
    with tab_login:
        _, col_l, _ = st.columns([1, 1, 1])
        with col_l:
            u_login = st.text_input("Usuário")
            p_login = st.text_input("Senha", type="password")
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
            u_novo = st.text_input("Novo Usuário")
            p_novo = st.text_input("Nova Senha", type="password")
            if st.button("Cadastrar", use_container_width=True):
                if u_novo and p_novo:
                    st.session_state.usuarios_db[u_novo] = p_novo
                    st.success("Conta criada!")
                else:
                    st.warning("Preencha os campos.")

# --- APP PRINCIPAL ---
else:
    st.sidebar.title("🏢 Painel de Controle")
    st.sidebar.write(f"Usuário: **{st.session_state.usuario_atual}**")
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard Visual", "➕ Capturar/Atualizar Lead"])
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # --- DASHBOARD ---
    if menu == "📊 Dashboard Visual":
        st.header("📊 Inteligência de Vendas")
        
        if not st.session_state.df_leads.empty:
            df = st.session_state.df_leads.copy()
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
            df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(0)

            m1, m2, m3 = st.columns(3)
            m1.metric("Clientes Únicos", len(df))
            m2.metric("Pipeline Total", f"R$ {df['valor'].sum():,.2f}")
            m3.metric("Score Médio", f"{df['score'].mean():.1f} pts")

            st.divider()
            g1, g2 = st.columns(2)
            with g1:
                st.subheader("🎯 Status por Cliente")
                st.bar_chart(df['status'].value_counts())
            with g2:
                st.subheader("💰 Volume por ID (Top 10)")
                st.bar_chart(data=df.head(10), x='id', y='valor')

            st.divider()
            st.subheader("📋 Base de Clientes")
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exportar CSV", csv, "leads_id.csv", "text/csv")
        else:
            st.info("Nenhum dado processado.")

    # --- CAPTURA COM ID ---
    elif menu == "➕ Capturar/Atualizar Lead":
        st.header("⚡ Captura Inteligente por ID")
        
        c1, c2 = st.columns([1, 3])
        with c1:
            cliente_id = st.number_input("ID do Cliente:", min_value=1, step=1, help="Use o mesmo ID para atualizar um cliente existente.")
        
        with c2:
            st.info(f"O sistema irá somar ou atualizar as informações para o ID: {cliente_id}")

        texto_input = st.text_area("Insira o texto para análise:", height=200)
        
        if st.button("Processar e Salvar"):
            if texto_input:
                with st.spinner("Analisando..."):
                    resultado = processar_com_mistral(texto_input)
                    
                    if "ERRO" not in resultado:
                        dados = json.loads(resultado)
                        dados['id'] = str(cliente_id) # Atribui o ID escolhido
                        
                        # Lógica de Update ou Insert
                        df_atual = st.session_state.df_leads
                        if str(cliente_id) in df_atual['id'].values:
                            # Remove a versão antiga e adiciona a nova (Atualização)
                            st.session_state.df_leads = df_atual[df_atual['id'] != str(cliente_id)]
                            st.session_state.df_leads = pd.concat([st.session_state.df_leads, pd.DataFrame([dados])], ignore_index=True)
                            st.success(f"Dados do Cliente ID {cliente_id} atualizados!")
                        else:
                            # Adiciona novo (Inclusão)
                            st.session_state.df_leads = pd.concat([st.session_state.df_leads, pd.DataFrame([dados])], ignore_index=True)
                            st.success(f"Novo Cliente ID {cliente_id} registrado!")
                        
                        st.json(dados)
                        st.balloons()
                    else:
                        st.error(resultado)
