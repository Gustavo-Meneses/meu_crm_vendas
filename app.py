import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
import hashlib
import json

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Gemini CRM Pro - Enterprise", layout="wide")

# Conexão Oficial via Service Account
try:
    # O Streamlit busca automaticamente as configurações em [connections.gsheets]
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Erro Crítico: Não foi possível carregar as credenciais da Service Account nos Secrets.")
    st.stop()

# --- FUNÇÕES DE DADOS (SIMPLIFICADAS PARA SERVICE ACCOUNT) ---
def get_data(worksheet_name):
    try:
        # Lê os dados usando as configurações globais do Secrets
        return conn.read(worksheet=worksheet_name, ttl=0)
    except Exception:
        # Caso a aba não exista, retorna estrutura básica
        if worksheet_name == "users":
            return pd.DataFrame(columns=["username", "password", "role", "pergunta_seg", "resposta_seg"])
        return pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

def save_data(df, worksheet_name):
    try:
        # Atualiza a planilha usando a Conta de Serviço
        conn.update(worksheet=worksheet_name, data=df)
    except Exception as e:
        st.error(f"Erro ao salvar no Google Sheets: {e}")

# --- FUNÇÕES DE SEGURANÇA ---
def hash_pw(pw): 
    return hashlib.sha256(str.encode(pw)).hexdigest()

# --- INICIALIZAÇÃO E ADMIN PADRÃO ---
df_users = get_data("users")

# Verifica se Gustavo Meneses existe, senão cria no primeiro acesso
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

# --- CONFIGURAÇÃO DA IA ---
def chamar_ia(prompt_text):
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        modelo_final = next((m for m in models if "gemini-1.5-flash" in m), models[0])
        model = genai.GenerativeModel(modelo_final)
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        raise Exception(f"Erro na IA: {str(e)}")

# --- INTERFACE DE LOGIN / CADASTRO ---
if 'logado' not in st.session_state: 
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🚀 CRM Meneses - Acesso Restrito")
    t_login, t_reg, t_rec = st.tabs(["Entrar", "Novo Cadastro", "Recuperar Senha"])
    
    with t_login:
        u = st.text_input("Usuário", key="l_u")
        p = st.text_input("Senha", type='password', key="l_p")
        if st.button("Acessar Sistema"):
            user_row = df_users[df_users['username'] == u]
            if not user_row.empty and user_row.iloc[0]['password'] == hash_pw(p):
                st.session_state.logado = True
                st.session_state.user_name = u
                st.session_state.user_role = user_row.iloc[0]['role']
                st.rerun()
            else: st.error("Acesso Negado.")

    with t_reg:
        new_u = st.text_input("Novo Usuário")
        new_p = st.text_input("Senha", type='password')
        perg = st.selectbox("Pergunta de Segurança", ["Cidade Natal?", "Primeiro Pet?", "Nome da Mãe?"])
        resp = st.text_input("Resposta")
        if st.button("Criar Conta"):
            if new_u and new_p and resp:
                if new_u not in df_users['username'].values:
                    new_row = pd.DataFrame([{"username": new_u, "password": hash_pw(new_p), "role": "user", "pergunta_seg": perg, "resposta_seg": hash_pw(resp.lower().strip())}])
                    save_data(pd.concat([df_users, new_row], ignore_index=True), "users")
                    st.success("Cadastrado com sucesso!")
                else: st.error("Usuário já existe.")

    with t_rec:
        u_rec = st.text_input("Usuário para recuperar")
        if u_rec:
            res_rec = df_users[df_users['username'] == u_rec]
            if not res_rec.empty:
                st.warning(f"Pergunta: {res_rec.iloc[0]['pergunta_seg']}")
                r_tentativa = st.text_input("Resposta Secreta")
                n_p = st.text_input("Nova Senha", type="password")
                if st.button("Redefinir"):
                    if hash_pw(r_tentativa.lower().strip()) == res_rec.iloc[0]['resposta_seg']:
                        df_users.loc[df_users['username'] == u_rec, 'password'] = hash_pw(n_p)
                        save_data(df_users, "users")
                        st.success("Senha atualizada!")

# --- APP PRINCIPAL ---
else:
    st.sidebar.title(f"👤 {st.session_state.user_name}")
    pages = ["Dashboard", "Adicionar Lead (IA)", "Editar Leads"]
    if st.session_state.user_role == "admin":
        pages.append("Painel Admin")
    
    menu = st.sidebar.radio("Navegação", pages)
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if menu == "Dashboard":
        st.header("📊 Inteligência Comercial")
        df_leads = get_data("leads")
        if not df_leads.empty:
            c1, c2 = st.columns(2)
            c1.metric("Leads", len(df_leads))
            c2.metric("Pipeline", f"R$ {pd.to_numeric(df_leads['valor']).sum():,.2f}")
            st.bar_chart(df_leads['status'].value_counts())
            st.dataframe(df_leads, use_container_width=True)
            st.download_button("Exportar CSV", df_leads.to_csv(index=False).encode('utf-8'), "leads.csv")
        else: st.info("Sem leads.")

    elif menu == "Adicionar Lead (IA)":
        st.header("🪄 Captura Inteligente")
        txt = st.text_area("Descreva o lead:")
        if st.button("Processar"):
            try:
                res = chamar_ia(f"JSON: {{'nome','empresa','status','historico','score','valor'}}. Texto: {txt}")
                d = json.loads(res.replace('```json', '').replace('```', '').strip())
                df_leads = get_data("leads")
                save_data(pd.concat([df_leads, pd.DataFrame([d])], ignore_index=True), "leads")
                st.success("Salvo com sucesso!")
            except Exception as e: st.error(f"Erro: {e}")

    elif menu == "Editar Leads":
        st.header("✏️ Edição")
        df_e = get_data("leads")
        if not df_e.empty:
            idx = st.selectbox("Lead:", df_e.index, format_func=lambda x: f"{df_e.iloc[x]['nome']}")
            with st.form("edit"):
                st.write(f"Editando: {df_e.iloc[idx]['nome']}")
                n_st = st.selectbox("Status", ["Prospecção", "Reunião", "Proposta", "Fechado", "Perdido"])
                n_val = st.number_input("Valor", value=float(df_e.iloc[idx]['valor']))
                if st.form_submit_button("Atualizar"):
                    df_e.at[idx, 'status'] = n_st
                    df_e.at[idx, 'valor'] = n_val
                    save_data(df_e, "leads")
                    st.success("Atualizado!")
        else: st.info("Vazio.")

    elif menu == "Painel Admin" and st.session_state.user_role == "admin":
        st.header("🔐 Admin")
        df_adm = get_data("users")
        u_sel = st.selectbox("Usuário:", df_adm['username'])
        col1, col2 = st.columns(2)
        with col1:
            n_r = st.selectbox("Cargo", ["user", "admin"])
            if st.button("Alterar Cargo"):
                df_adm.loc[df_adm['username'] == u_sel, 'role'] = n_r
                save_data(df_adm, "users")
                st.success("Cargo Alterado!")
        with col2:
            n_s = st.text_input("Reset Senha", type="password")
            if st.button("Forçar Senha"):
                df_adm.loc[df_adm['username'] == u_sel, 'password'] = hash_pw(n_s)
                save_data(df_adm, "users")
                st.success("Senha Resetada!")
