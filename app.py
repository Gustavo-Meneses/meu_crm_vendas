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
    # Busca automaticamente no bloco [connections.gsheets]
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Erro de Configuração nos Secrets: {e}")
    st.info("Certifique-se de copiar o conteúdo INTEGRAL da private_key do seu JSON entre as aspas triplas.")
    st.stop()

# --- FUNÇÕES DE MANIPULAÇÃO DE DADOS ---
def get_data(worksheet_name):
    try:
        url = st.secrets.get("gsheets_url")
        return conn.read(spreadsheet=url, worksheet=worksheet_name, ttl=0)
    except Exception:
        if worksheet_name == "users":
            return pd.DataFrame(columns=["username", "password", "role", "pergunta_seg", "resposta_seg"])
        return pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

def save_data(df, worksheet_name):
    try:
        url = st.secrets.get("gsheets_url")
        conn.update(spreadsheet=url, worksheet=worksheet_name, data=df)
        # Limpa o cache para que o próximo 'read' veja os dados novos
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Falha ao sincronizar com Google Sheets: {e}")

# --- SEGURANÇA ---
def hash_pw(pw): 
    return hashlib.sha256(str.encode(pw)).hexdigest()

# --- INICIALIZAÇÃO DE DADOS ---
df_users = get_data("users")

# Criar Admin Gustavo Meneses se necessário
if "Gustavo Meneses" not in df_users['username'].values:
    admin_data = pd.DataFrame([{
        "username": "Gustavo Meneses", "password": hash_pw("1234"), 
        "role": "admin", "pergunta_seg": "Qual o nome da sua empresa?", "resposta_seg": hash_pw("crm")
    }])
    df_users = pd.concat([df_users, admin_data], ignore_index=True)
    save_data(df_users, "users")

# --- INTELIGÊNCIA ARTIFICIAL ---
def chamar_ia(prompt_text):
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        raise Exception(f"Erro na IA: {str(e)}")

# --- INTERFACE DE LOGIN / CADASTRO ---
if 'logado' not in st.session_state: 
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🚀 CRM Inteligente - Acesso")
    t_login, t_reg, t_rec = st.tabs(["Entrar", "Novo Cadastro", "Recuperar Senha"])
    
    with t_login:
        u = st.text_input("Usuário", key="login_field")
        p = st.text_input("Senha", type='password', key="pass_field")
        if st.button("Acessar Sistema"):
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
                    new_row = pd.DataFrame([{"username": new_u, "password": hash_pw(new_p), "role": "user", "pergunta_seg": perg, "resposta_seg": hash_pw(resp.lower().strip())}])
                    save_data(pd.concat([df_users, new_row], ignore_index=True), "users")
                    st.success("Conta criada! Mude para a aba 'Entrar'.")
                else: st.error("Este usuário já existe.")

    with t_rec:
        u_rec = st.text_input("Usuário para recuperar")
        if u_rec:
            df_users = get_data("users")
            res_rec = df_users[df_users['username'] == u_rec]
            if not res_rec.empty:
                st.info(f"Pergunta: {res_rec.iloc[0]['pergunta_seg']}")
                r_tentativa = st.text_input("Sua Resposta Secreta")
                n_p = st.text_input("Nova Senha", type="password")
                if st.button("Redefinir Senha"):
                    if hash_pw(r_tentativa.lower().strip()) == res_rec.iloc[0]['resposta_seg']:
                        df_users.loc[df_users['username'] == u_rec, 'password'] = hash_pw(n_p)
                        save_data(df_users, "users")
                        st.success("Senha atualizada!")

# --- APP PRINCIPAL ---
else:
    st.sidebar.title(f"👤 {st.session_state.user_name}")
    menu = st.sidebar.radio("Navegação", ["Dashboard", "Adicionar Lead (IA)", "Editar Leads", "Painel Admin"] if st.session_state.user_role == "admin" else ["Dashboard", "Adicionar Lead (IA)", "Editar Leads"])
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if menu == "Dashboard":
        st.header("📊 Inteligência de Vendas")
        df_leads = get_data("leads")
        if not df_leads.empty:
            df_leads['valor'] = pd.to_numeric(df_leads['valor'], errors='coerce').fillna(0)
            st.metric("Pipeline Total", f"R$ {df_leads['valor'].sum():,.2f}")
            st.bar_chart(df_leads['status'].value_counts())
            st.dataframe(df_leads, use_container_width=True)
        else: st.info("Nenhum lead encontrado.")

    elif menu == "Adicionar Lead (IA)":
        st.header("🪄 Captura por IA")
        txt = st.text_area("Descreva o lead:")
        if st.button("Analisar e Salvar"):
            try:
                res = chamar_ia(f"Converta em JSON: {{'nome','empresa','status','historico','score','valor'}}. Texto: {txt}")
                d_json = json.loads(res.replace('```json', '').replace('```', '').strip())
                df_leads = get_data("leads")
                save_data(pd.concat([df_leads, pd.DataFrame([d_json])], ignore_index=True), "leads")
                st.success("Salvo com sucesso!")
            except Exception as e: st.error(f"Erro: {e}")

    elif menu == "Editar Leads":
        st.header("✏️ Edição Manual")
        df_e = get_data("leads")
        if not df_e.empty:
            idx = st.selectbox("Lead:", df_e.index, format_func=lambda x: f"{df_e.iloc[x]['nome']}")
            with st.form("edit"):
                n_st = st.selectbox("Status", ["Prospecção", "Reunião", "Proposta", "Fechado", "Perdido"])
                n_val = st.number_input("Valor", value=float(df_e.iloc[idx]['valor']))
                if st.form_submit_button("Atualizar"):
                    df_e.at[idx, 'status'] = n_st
                    df_e.at[idx, 'valor'] = n_val
                    save_data(df_e, "leads")
                    st.success("Atualizado!")
                    st.rerun()

    elif menu == "Painel Admin":
        st.header("🔐 Admin")
        df_adm = get_data("users")
        u_sel = st.selectbox("Usuário:", df_adm['username'])
        if st.button("Promover a Admin"):
            df_adm.loc[df_adm['username'] == u_sel, 'role'] = 'admin'
            save_data(df_adm, "users")
            st.success("Promovido!")
