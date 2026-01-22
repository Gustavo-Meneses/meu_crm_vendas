import streamlit as st
import pandas as pd
from mistralai import Mistral
import json
import re  # Importação necessária para fatiar o texto

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão Comercial Inteligente", layout="wide", page_icon="🏢")

# --- INICIALIZAÇÃO DE DADOS ---
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
    st.markdown("<h2 style='text-align: center;'>Portal de Gestão Comercial</h2>", unsafe_allow_html=True)
    
    tab_login, tab_cadastro = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
    
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
            u_novo = st.text_input("Novo Usuário", key="new_user")
            p_novo = st.text_input("Nova Senha", type="password", key="new_pass")
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
    
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard Visual", "➕ Capturar (Lote)"])
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # --- ABA: DASHBOARD ---
    if menu == "📊 Dashboard Visual":
        st.header("📊 Inteligência de Vendas")
        
        if not st.session_state.df_leads.empty:
            df = st.session_state.df_leads.copy()
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
            df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(0)
            
            # Ordena por ID numérico se possível
            try:
                df['id_num'] = pd.to_numeric(df['id'])
                df = df.sort_values('id_num')
            except:
                pass

            m1, m2, m3 = st.columns(3)
            m1.metric("Clientes Únicos", len(df))
            m2.metric("Pipeline Total", f"R$ {df['valor'].sum():,.2f}")
            m3.metric("Score Médio", f"{df['score'].mean():.1f} pts")

            st.divider()
            g1, g2 = st.columns(2)
            with g1:
                st.subheader("🎯 Status do Funil")
                st.bar_chart(df['status'].value_counts(), color="#2980B9")
            with g2:
                st.subheader("💰 Top 10 Oportunidades")
                st.bar_chart(data=df.head(10), x='id', y='valor', color="#27AE60")

            st.divider()
            st.subheader("📋 Base de Dados Consolidada")
            st.dataframe(df.drop(columns=['id_num'], errors='ignore'), use_container_width=True)
            
            csv = df.drop(columns=['id_num'], errors='ignore').to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exportar CSV", csv, "leads_lote.csv", "text/csv")
        else:
            st.info("Nenhum dado encontrado. Vá em 'Capturar (Lote)' para começar.")

    # --- ABA: CAPTURA EM LOTE ---
    elif menu == "➕ Capturar (Lote)":
        st.header("⚡ Processamento em Massa")
        st.markdown("""
        Cole todos os seus leads abaixo. O sistema identificará automaticamente a separação através do padrão **"ID do Cliente: X"**.
        """)
        
        texto_input = st.text_area("Cole aqui sua lista de leads:", height=400, placeholder="ID do Cliente: 1\nTexto do lead 1...\n\nID do Cliente: 2\nTexto do lead 2...")
        
        if st.button("🚀 Processar Lista Completa"):
            if texto_input:
                # Regex para encontrar "ID do Cliente" seguido de número
                # Padrão flexível: aceita "ID do Cliente 1", "ID do Cliente: 1", "ID do Cliente - 1"
                padrao = r"(ID do Cliente\s*[:\-\s]?\s*)(\d+)"
                matches = list(re.finditer(padrao, texto_input, re.IGNORECASE))
                
                if not matches:
                    st.error("Nenhum 'ID do Cliente' encontrado. Verifique a formatação do texto.")
                else:
                    total_leads = len(matches)
                    progresso = st.progress(0)
                    log_sucesso = 0
                    
                    st.write(f"🔍 Identificados {total_leads} blocos de leads. Iniciando processamento...")

                    for i, match in enumerate(matches):
                        # Extrai o ID
                        id_cliente = match.group(2)
                        
                        # Define o início e fim do texto deste cliente
                        inicio_txt = match.end()
                        if i + 1 < total_leads:
                            fim_txt = matches[i+1].start()
                        else:
                            fim_txt = len(texto_input)
                        
                        conteudo_lead = texto_input[inicio_txt:fim_txt].strip()
                        
                        # Processa com a IA
                        resultado = processar_com_mistral(f"Lead ID {id_cliente}: {conteudo_lead}")
                        
                        if "ERRO" not in resultado:
                            try:
                                dados = json.loads(resultado)
                                dados['id'] = str(id_cliente) # Garante que o ID é o capturado no texto
                                
                                # Lógica de Upsert (Atualizar se existe, Adicionar se novo)
                                df_atual = st.session_state.df_leads
                                if str(id_cliente) in df_atual['id'].values:
                                    st.session_state.df_leads = df_atual[df_atual['id'] != str(id_cliente)]
                                    st.session_state.df_leads = pd.concat([st.session_state.df_leads, pd.DataFrame([dados])], ignore_index=True)
                                else:
                                    st.session_state.df_leads = pd.concat([st.session_state.df_leads, pd.DataFrame([dados])], ignore_index=True)
                                
                                log_sucesso += 1
                            except:
                                st.error(f"Erro ao ler JSON do ID {id_cliente}")
                        else:
                            st.error(f"Erro na API para o ID {id_cliente}: {resultado}")
                        
                        # Atualiza barra de progresso
                        progresso.progress((i + 1) / total_leads)
                    
                    st.success(f"✅ Processamento finalizado! {log_sucesso} de {total_leads} leads processados com sucesso.")
                    st.balloons()
            else:
                st.warning("A área de texto está vazia.")
