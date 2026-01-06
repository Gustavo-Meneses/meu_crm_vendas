import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
import hashlib
import json

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Gemini CRM Pro", layout="wide", page_icon="🚀")

# --- CONEXÃO COM GOOGLE SHEETS ---
try:
    # O Streamlit busca as credenciais automaticamente no bloco [connections.gsheets] dos Secrets
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Erro de Configuração nos Secrets: {e}")
    st.info("Certifique-se de usar aspas triplas ( \"\"\" ) na private_key dentro dos Secrets.")
    st.stop()

# --- FUNÇÕES DE MANIPULAÇÃO DE DADOS ---
def get_data(worksheet_name):
    try:
        url = st.secrets.get("gsheets_url")
        # ttl=0 evita que o Streamlit use dados antigos em cache
        return conn.read(spreadsheet=url, worksheet=worksheet_name, ttl=0)
    except Exception as e:
        # Se a aba estiver vazia ou com erro, retorna um esqueleto para não travar o app
        if worksheet_name == "users":
            return pd.DataFrame(columns=["username", "password", "role", "pergunta_seg", "resposta_seg"])
        return pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

def save_data(df, worksheet_name):
    try:
        url = st.secrets.get("gsheets_url")
        conn.update(spreadsheet=url, worksheet=worksheet_name, data=df)
    except Exception as e:
        st.error(f"Falha ao sincronizar com Google Sheets: {e}")

# --- SEGURANÇA ---
def hash_pw(pw): 
    return hashlib.sha256(str.encode(pw)).hexdigest()

# --- INICIALIZAÇÃO DE DADOS ---
df_users = get_data("users")

# Criar Admin Gustavo Meneses se a planilha for nova
if "Gustavo Meneses" not in df_users['username'].values:
    admin_data = pd.DataFrame([{
        "username": "Gustavo Meneses", 
        "password": hash_pw("1234"), 
        "role": "admin", 
        "pergunta_seg": "Qual o nome da sua empresa?", 
        "resposta_seg": hash_pw("crm")
    }])
    df_users = pd.concat([df_users, admin_data], ignore_index=True)
    save_data(df_users, "users")

# --- INTELIGÊNCIA ARTIFICIAL ---
def chamar_ia(prompt_text):
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        # Busca modelos disponíveis na conta
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        modelo_final = next((m for m in models if "gemini-1.5-flash" in m), models[0])
        model = genai.GenerativeModel(modelo_final)
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        raise Exception(f"Erro na IA: {str(e)}")

# --- FLUXO DE ACESSO (LOGIN / CADASTRO) ---
if 'logado' not in st.session_state: 
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🚀 CRM Inteligente - Acesso")
    t_login, t_reg, t_rec = st.tabs(["Entrar", "Novo Cadastro", "Recuperar Senha"])
    
    with t_login:
        u = st.text_input("Usuário", key="login_field")
        p = st.text_input("Senha", type='password', key="pass_field")
        if st.button("Acessar Sistema"):
            # Recarrega usuários para garantir que novos cadastros sejam lidos
            df_users = get_data("users")
            user_row = df_users[df_users['username'] == u]
            if not user_row.empty and user_row.iloc[0]['password'] == hash_pw(p):
                st.session_state.logado = True
                st.session_state.user_name = u
                st.session_state.user_role = user_row.iloc[0]['role']
                st.rerun()
            else: st.error("Credenciais inválidas.")

    with t_reg:
        st.subheader("Cadastro de Usuário")
        new_u = st.text_input("Nome de Usuário")
        new_p = st.text_input("Senha de Acesso", type='password')
        perg = st.selectbox("Pergunta de Segurança", ["Cidade Natal?", "Primeiro Pet?", "Nome da Mãe?"])
        resp = st.text_input("Sua Resposta")
        if st.button("Criar Minha Conta"):
            if new_u and new_p and resp:
                df_users = get_data("users")
                if new_u not in df_users['username'].values:
                    new_row = pd.DataFrame([{
                        "username": new_u, "password": hash_pw(new_p), 
                        "role": "user", "pergunta_seg": perg, 
                        "resposta_seg": hash_pw(resp.lower().strip())
                    }])
                    save_data(pd.concat([df_users, new_row], ignore_index=True), "users")
                    st.success("Conta criada! Mude para a aba 'Entrar'.")
                else: st.error("Este usuário já existe.")
            else: st.warning("Preencha todos os campos.")

    with t_rec:
        u_rec = st.text_input("Usuário para recuperar", key="rec_field")
        if u_rec:
            df_users = get_data("users")
            res_rec = df_users[df_users['username'] == u_rec]
            if not res_rec.empty:
                st.info(f"Pergunta: {res_rec.iloc[0]['pergunta_seg']}")
                r_tentativa = st.text_input("Sua Resposta Secreta")
                n_p = st.text_input("Defina Nova Senha", type="password")
                if st.button("Redefinir Senha"):
                    if hash_pw(r_tentativa.lower().strip()) == res_rec.iloc[0]['resposta_seg']:
                        df_users.loc[df_users['username'] == u_rec, 'password'] = hash_pw(n_p)
                        save_data(df_users, "users")
                        st.success("Senha atualizada com sucesso!")
                    else: st.error("Resposta de segurança incorreta.")

# --- APP PRINCIPAL (PÓS-LOGIN) ---
else:
    st.sidebar.title(f"👤 {st.session_state.user_name}")
    st.sidebar.write(f"Nível: {st.session_state.user_role.upper()}")
    
    pages = ["Dashboard", "Adicionar Lead (IA)", "Editar Leads"]
    if st.session_state.user_role == "admin":
        pages.append("Painel Admin")
    
    menu = st.sidebar.radio("Navegação", pages)
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # --- DASHBOARD ---
    if menu == "Dashboard":
        st.header("📊 Inteligência de Vendas")
        df_leads = get_data("leads")
        if not df_leads.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Leads", len(df_leads))
            # Converte valores para numérico para evitar erros de soma
            df_leads['valor'] = pd.to_numeric(df_leads['valor'], errors='coerce').fillna(0)
            c2.metric("Pipeline Total", f"R$ {df_leads['valor'].sum():,.2f}")
            c3.metric("Conversão Média", f"{pd.to_numeric(df_leads['score'], errors='coerce').mean():.1f}%")

            st.write("### Distribuição por Status")
            st.bar_chart(df_leads['status'].value_counts())
            
            st.write("### Tabela de Dados")
            st.dataframe(df_leads, use_container_width=True)
            
            st.download_button("📥 Baixar Relatório (CSV)", df_leads.to_csv(index=False).encode('utf-8'), "crm_export.csv")
        else: st.info("Nenhum lead encontrado na base de dados.")

    # --- ADICIONAR LEAD (IA) ---
    elif menu == "Adicionar Lead (IA)":
        st.header("🪄 Captura Automática por IA")
        txt = st.text_area("Descreva a conversa ou cole as notas do lead:", height=150)
        if st.button("Analisar e Salvar"):
            if txt:
                try:
                    prompt = f"Converta em JSON puro: {{'nome','empresa','status','historico','score','valor'}}. Use status como 'Prospecção' se não souber. Texto: {txt}"
                    res_ia = chamar_ia(prompt)
                    # Limpa o markdown da IA
                    json_str = res_ia.replace('```json', '').replace('```', '').strip()
                    d_json = json.loads(json_str)
                    
                    df_leads = get_data("leads")
                    save_data(pd.concat([df_leads, pd.DataFrame([d_json])], ignore_index=True), "leads")
                    st.success("Lead salvo no Google Sheets com sucesso!")
                except Exception as e: st.error(f"Erro no processamento da IA: {e}")
            else: st.warning("Por favor, insira um texto para análise.")

    # --- EDIÇÃO MANUAL ---
    elif menu == "Editar Leads":
        st.header("✏️ Edição Manual de Leads")
        df_e = get_data("leads")
        if not df_e.empty:
            idx = st.selectbox("Selecione o Lead:", df_e.index, format_func=lambda x: f"{df_e.iloc[x]['nome']} ({df_e.iloc[x]['empresa']})")
            with st.form("form_edit_manual"):
                st.write(f"Editando: **{df_e.iloc[idx]['nome']}**")
                n_st = st.selectbox("Status Atual", ["Prospecção", "Reunião", "Proposta", "Fechado", "Perdido"], 
                                   index=["Prospecção", "Reunião", "Proposta", "Fechado", "Perdido"].index(df_e.iloc[idx]['status']) if df_e.iloc[idx]['status'] in ["Prospecção", "Reunião", "Proposta", "Fechado", "Perdido"] else 0)
                n_val = st.number_input("Valor do Negócio", value=float(df_e.iloc[idx]['valor']))
                if st.form_submit_button("Sincronizar Alterações"):
                    df_e.at[idx, 'status'] = n_st
                    df_e.at[idx, 'valor'] = n_val
                    save_data(df_e, "leads")
                    st.success("Dados atualizados!")
                    st.rerun()
        else: st.info("A base de leads está vazia.")

    # --- PAINEL ADMIN ---
    elif menu == "Painel Admin" and st.session_state.user_role == "admin":
        st.header("🛡️ Gestão Administrativa")
        df_adm = get_data("users")
        st.dataframe(df_adm[["username", "role", "pergunta_seg"]], use_container_width=True)
        
        st.write("---")
        u_sel = st.selectbox("Selecione o Usuário para gerenciar:", df_adm['username'])
        
        c_adm1, c_adm2 = st.columns(2)
        with c_adm1:
            n_r = st.selectbox("Novo Nível de Acesso", ["user", "admin"])
            if st.button("Confirmar Mudança de Cargo"):
                df_adm.loc[df_adm['username'] == u_sel, 'role'] = n_r
                save_data(df_adm, "users")
                st.success(f"{u_sel} agora é {n_r}!")
        
        with c_adm2:
            n_s = st.text_input("Resetar Senha do Usuário", type="password")
            if st.button("Forçar Nova Senha"):
                if n_s:
                    df_adm.loc[df_adm['username'] == u_sel, 'password'] = hash_pw(n_s)
                    save_data(df_adm, "users")
                    st.success(f"Senha de {u_sel} alterada!")
