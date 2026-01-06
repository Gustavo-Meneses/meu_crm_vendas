import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
import hashlib
import json

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Gemini CRM Pro - Sheets", layout="wide")

# Conexão com Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Erro na conexão com o Banco de Dados. Verifique os Secrets.")
    st.stop()

# --- FUNÇÕES DE DADOS ---
def get_data(worksheet_name):
    try:
        # ttl=0 garante que os dados sejam lidos em tempo real sem cache antigo
        return conn.read(spreadsheet=st.secrets["gsheets_url"], worksheet=worksheet_name, ttl=0)
    except Exception:
        if worksheet_name == "users":
            return pd.DataFrame(columns=["username", "password", "role", "pergunta_seg", "resposta_seg"])
        return pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

def save_data(df, worksheet_name):
    try:
        conn.update(spreadsheet=st.secrets["gsheets_url"], worksheet=worksheet_name, data=df)
    except Exception as e:
        st.error(f"Erro ao salvar no Google Sheets: {e}")

# --- FUNÇÕES DE SEGURANÇA ---
def hash_pw(pw): 
    return hashlib.sha256(str.encode(pw)).hexdigest()

# --- INICIALIZAÇÃO DE USUÁRIOS ---
df_users = get_data("users")

# Garantir que Gustavo Meneses (Admin) existe na planilha
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

# --- IA: CONFIGURAÇÃO ---
def chamar_ia(prompt_text):
    try:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        # Auto-detecção de modelo disponível
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        modelo_final = next((m for m in models if "gemini-1.5-flash" in m), models[0])
        model = genai.GenerativeModel(modelo_final)
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        raise Exception(f"Erro na IA: {str(e)}")

# --- INTERFACE DE ACESSO ---
if 'logado' not in st.session_state: 
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🚀 CRM Inteligente - Acesso")
    tab_login, tab_reg, tab_rec = st.tabs(["Entrar", "Novo Cadastro", "Recuperar Senha"])
    
    with tab_login:
        u = st.text_input("Usuário", key="login_u")
        p = st.text_input("Senha", type='password', key="login_p")
        if st.button("Acessar Sistema"):
            user_row = df_users[df_users['username'] == u]
            if not user_row.empty and user_row.iloc[0]['password'] == hash_pw(p):
                st.session_state.logado = True
                st.session_state.user_name = u
                st.session_state.user_role = user_row.iloc[0]['role']
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    with tab_reg:
        st.subheader("Crie sua conta")
        new_u = st.text_input("Defina seu Usuário")
        new_p = st.text_input("Defina sua Senha", type='password')
        perg_list = ["Nome do primeiro pet?", "Cidade natal?", "Cor favorita?", "Nome da mãe?"]
        chosen_perg = st.selectbox("Pergunta de segurança (para recuperação)", perg_list)
        chosen_resp = st.text_input("Resposta da pergunta")
        
        if st.button("Finalizar Cadastro"):
            if new_u and new_p and chosen_resp:
                if new_u not in df_users['username'].values:
                    new_row = pd.DataFrame([{
                        "username": new_u, "password": hash_pw(new_p), 
                        "role": "user", "pergunta_seg": chosen_perg, 
                        "resposta_seg": hash_pw(chosen_resp.lower().strip())
                    }])
                    save_data(pd.concat([df_users, new_row], ignore_index=True), "users")
                    st.success("Cadastro realizado!")
                else: st.error("Usuário já existe.")
            else: st.warning("Preencha todos os campos.")

    with tab_rec:
        st.subheader("Redefinição de Senha")
        u_rec = st.text_input("Digite seu usuário", key="rec_u")
        if u_rec:
            res_rec = df_users[df_users['username'] == u_rec]
            if not res_rec.empty:
                st.warning(f"Pergunta: {res_rec.iloc[0]['pergunta_seg']}")
                resp_tentativa = st.text_input("Sua resposta secreta")
                nova_p_rec = st.text_input("Nova Senha", type="password")
                if st.button("Atualizar Senha"):
                    if hash_pw(resp_tentativa.lower().strip()) == res_rec.iloc[0]['resposta_seg']:
                        df_users.loc[df_users['username'] == u_rec, 'password'] = hash_pw(nova_p_rec)
                        save_data(df_users, "users")
                        st.success("Senha alterada! Faça login.")
                    else: st.error("Resposta incorreta.")

# --- SISTEMA PRINCIPAL ---
else:
    st.sidebar.title(f"👤 {st.session_state.user_name}")
    st.sidebar.info(f"Nível: {st.session_state.user_role.upper()}")
    
    pages = ["Dashboard", "Adicionar Lead (IA)", "Editar Leads"]
    if st.session_state.user_role == "admin":
        pages.append("Painel Admin")
    
    menu = st.sidebar.radio("Navegação", pages)
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # --- 1. DASHBOARD ---
    if menu == "Dashboard":
        st.header("📊 Painel de Vendas")
        df_leads = get_data("leads")
        
        if not df_leads.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("Leads Totais", len(df_leads))
            m2.metric("Pipeline (R$)", f"{pd.to_numeric(df_leads['valor']).sum():,.2f}")
            m3.metric("Score Médio", f"{pd.to_numeric(df_leads['score']).mean():.1f}")

            st.write("**Status dos Leads**")
            st.bar_chart(df_leads['status'].value_counts())
            
            st.dataframe(df_leads, use_container_width=True)
            
            st.subheader("📥 Exportação")
            csv_data = df_leads.to_csv(index=False).encode('utf-8')
            st.download_button("Exportar para Excel (CSV)", csv_data, "relatorio_leads.csv", "text/csv")
        else:
            st.info("Nenhum lead cadastrado ainda.")

    # --- ADICIONAR LEAD (IA) ---
    elif menu == "Adicionar Lead (IA)":
        st.header("🪄 Captura por IA")
        raw_text = st.text_area("Cole a conversa ou notas:")
        if st.button("Analisar"):
            try:
                prompt = f"Gere APENAS JSON: {{'nome','empresa','status','historico','score','valor'}}. Texto: {raw_text}"
                resp_ia = chamar_ia(prompt)
                json_data = json.loads(resp_ia.replace('```json', '').replace('```', '').strip())
                
                df_leads = get_data("leads")
                save_data(pd.concat([df_leads, pd.DataFrame([json_data])], ignore_index=True), "leads")
                st.success("Salvo no Google Sheets!")
            except Exception as e: st.error(f"Erro: {e}")

    # --- 2. EDIÇÃO MANUAL ---
    elif menu == "Editar Leads":
        st.header("✏️ Edição Manual")
        df_edit = get_data("leads")
        if not df_edit.empty:
            escolha = st.selectbox("Selecione o lead:", df_edit.index, 
                                    format_func=lambda x: f"{df_edit.iloc[x]['nome']} - {df_edit.iloc[x]['empresa']}")
            
            with st.form("edit_form"):
                new_st = st.selectbox("Status", ["Prospecção", "Reunião", "Proposta", "Fechado", "Perdido"])
                new_val = st.number_input("Valor", value=float(df_edit.iloc[escolha]['valor']))
                if st.form_submit_button("Salvar Alterações"):
                    df_edit.at[escolha, 'status'] = new_st
                    df_edit.at[escolha, 'valor'] = new_val
                    save_data(df_edit, "leads")
                    st.success("Lead atualizado!")
                    st.rerun()
        else: st.warning("Sem leads.")

    # --- 3. PAINEL ADMIN ---
    elif menu == "Painel Admin" and st.session_state.user_role == "admin":
        st.header("🔐 Gestão de Usuários")
        df_admin_u = get_data("users")
        st.dataframe(df_admin_u[["username", "role"]], use_container_width=True)
        
        user_alvo = st.selectbox("Selecionar Usuário:", df_admin_u['username'])
        
        col1, col2 = st.columns(2)
        with col1:
            novo_c = st.selectbox("Mudar Cargo", ["user", "admin"])
            if st.button("Confirmar Cargo"):
                df_admin_u.loc[df_admin_u['username'] == user_alvo, 'role'] = novo_c
                save_data(df_admin_u, "users")
                st.success("Cargo alterado!")
                st.rerun()
        
        with col2:
            nova_s_admin = st.text_input("Resetar Senha", type="password")
            if st.button("Forçar Nova Senha"):
                df_admin_u.loc[df_admin_u['username'] == user_alvo, 'password'] = hash_pw(nova_s_admin)
                save_data(df_admin_u, "users")
                st.success("Senha redefinida!")
