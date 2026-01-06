import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import hashlib
import json
import io

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Gemini CRM Pro", layout="wide")

# Banco de Dados
conn = sqlite3.connect('crm_data.db', check_same_thread=False)
c = conn.cursor()

# Tabelas com estrutura para Suporte a Admin e Recuperação
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (username TEXT, password TEXT, role TEXT, pergunta_seg TEXT, resposta_seg TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS leads 
             (nome TEXT, empresa TEXT, status TEXT, historico TEXT, score INTEGER, valor REAL)''')
conn.commit()

# --- FUNÇÕES DE SEGURANÇA ---
def hash_pw(pw): return hashlib.sha256(str.encode(pw)).hexdigest()

# Inserção Automática do Administrador Gustavo Meneses
c.execute('SELECT * FROM users WHERE username=?', ("Gustavo Meneses",))
if not c.fetchone():
    c.execute('INSERT INTO users VALUES (?,?,?,?,?)', 
              ("Gustavo Meneses", hash_pw("1234"), "admin", "Qual o nome da sua empresa?", hash_pw("CRM")))
    conn.commit()

# --- IA: AUTO-DESCOBERTA DE MODELO ---
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

# --- INTERFACE DE ACESSO (LOGIN / CADASTRO / RECUPERAÇÃO) ---
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🚀 CRM Inteligente - Acesso")
    tab_login, tab_reg, tab_rec = st.tabs(["Entrar", "Novo Cadastro", "Recuperar Senha"])
    
    with tab_login:
        u = st.text_input("Usuário", key="l_u")
        p = st.text_input("Senha", type='password', key="l_p")
        if st.button("Acessar Sistema"):
            c.execute('SELECT password, role FROM users WHERE username=?', (u,))
            user = c.fetchone()
            if user and user[0] == hash_pw(p):
                st.session_state.logado = True
                st.session_state.user_name = u
                st.session_state.user_role = user[1]
                st.rerun()
            else: st.error("Usuário ou senha incorretos.")

    with tab_reg:
        st.subheader("Crie sua conta")
        new_u = st.text_input("Defina seu Usuário")
        new_p = st.text_input("Defina sua Senha", type='password')
        
        st.write("---")
        st.write("🔒 **Configuração de Recuperação**")
        perg_list = [
            "Qual o nome do seu primeiro animal de estimação?",
            "Qual a cidade onde seus pais se conheceram?",
            "Qual o nome da sua primeira escola?",
            "Qual sua comida favorita da infância?"
        ]
        chosen_perg = st.selectbox("Escolha uma pergunta de segurança", perg_list)
        chosen_resp = st.text_input("Sua resposta secreta (não esqueça!)")
        
        # Apenas Gustavo ou outros Admins podem criar novos Admins
        role_opt = ["user", "admin"] if new_u == "Gustavo Meneses" else ["user"]
        chosen_role = st.selectbox("Nível de Acesso", role_opt)

        if st.button("Finalizar Cadastro"):
            if new_u and new_p and chosen_resp:
                c.execute('INSERT INTO users VALUES (?,?,?,?,?)', 
                          (new_u, hash_pw(new_p), chosen_role, chosen_perg, hash_pw(chosen_resp.lower().strip())))
                conn.commit()
                st.success("Cadastro realizado! Mude para a aba 'Entrar'.")
            else: st.warning("Preencha todos os campos, incluindo a resposta de segurança.")

    with tab_rec:
        st.subheader("Redefinição de Senha")
        u_rec = st.text_input("Digite seu usuário")
        if u_rec:
            c.execute('SELECT pergunta_seg, resposta_seg FROM users WHERE username=?', (u_rec,))
            res_rec = c.fetchone()
            if res_rec:
                st.warning(f"Pergunta: {res_rec[0]}")
                resp_tentativa = st.text_input("Sua resposta secreta")
                nova_p_rec = st.text_input("Nova Senha", type="password")
                if st.button("Atualizar Senha"):
                    if hash_pw(resp_tentativa.lower().strip()) == res_rec[1]:
                        c.execute('UPDATE users SET password=? WHERE username=?', (hash_pw(nova_p_rec), u_rec))
                        conn.commit()
                        st.success("Senha alterada! Já pode fazer login.")
                    else: st.error("Resposta de segurança incorreta.")
            else: st.error("Usuário não encontrado.")

# --- SISTEMA PRINCIPAL ---
else:
    st.sidebar.title(f"👤 {st.session_state.user_name}")
    st.sidebar.info(f"Nível: {st.session_state.user_role.upper()}")
    
    pages = ["Dashboard", "Adicionar Lead (IA)", "Editar Leads"]
    if st.session_state.user_role == "admin":
        pages.append("Painel Admin")
    
    menu = st.sidebar.radio("Navegação", pages)
    
    if st.sidebar.button("Encerrar Sessão"):
        st.session_state.logado = False
        st.rerun()

    # --- 1. DASHBOARD COM GRÁFICOS ---
    if menu == "Dashboard":
        st.header("📊 Inteligência de Dados")
        df = pd.read_sql_query("SELECT * FROM leads", conn)
        
        if not df.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("Leads Totais", len(df))
            m2.metric("Pipeline (R$)", f"{df['valor'].sum():,.2f}")
            m3.metric("Conversão Média", f"{df['score'].mean():.0f}%")

            col_graf1, col_graf2 = st.columns(2)
            with col_graf1:
                st.write("**Status dos Leads**")
                st.bar_chart(df['status'].value_counts())
            with col_graf2:
                st.write("**Potencial Financeiro por Empresa**")
                st.line_chart(df.set_index('empresa')['valor'])

            st.write("---")
            st.dataframe(df, use_container_width=True)

            # --- 2. EXPORTAÇÃO ---
            st.subheader("📥 Exportação")
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button("Exportar para CSV (Excel)", csv_data, "relatorio_leads.csv", "text/csv")
        else:
            st.info("Ainda não existem leads para exibir gráficos.")

    # --- ADICIONAR LEAD (IA) ---
    elif menu == "Adicionar Lead (IA)":
        st.header("🪄 Captura por Inteligência Artificial")
        raw_text = st.text_area("Cole a conversa ou notas aqui:")
        if st.button("Processar Dados"):
            try:
                prompt = f"Extraia em JSON: {{'nome','empresa','status','resumo_conversa','score','valor'}}. Texto: {raw_text}"
                resp_ia = chamar_ia(prompt)
                json_data = json.loads(resp_ia.replace('```json', '').replace('```', '').strip())
                
                c.execute('INSERT INTO leads VALUES (?,?,?,?,?,?)', 
                          (json_data.get('nome',''), json_data.get('empresa',''), json_data.get('status',''), 
                           json_data.get('resumo_conversa',''), json_data.get('score',0), json_data.get('valor',0)))
                conn.commit()
                st.success("Lead identificado e salvo!")
            except Exception as e: st.error(f"Erro no processamento: {e}")

    # --- 3. EDIÇÃO MANUAL ---
    elif menu == "Editar Leads":
        st.header("✏️ Gestão Manual")
        df_edit = pd.read_sql_query("SELECT rowid, * FROM leads", conn)
        if not df_edit.empty:
            escolha = st.selectbox("Qual lead deseja alterar?", df_edit.index, 
                                    format_func=lambda x: f"{df_edit.iloc[x]['nome']} - {df_edit.iloc[x]['empresa']}")
            
            with st.form("edit_form"):
                new_st = st.selectbox("Alterar Status", ["Prospecção", "Reunião", "Proposta", "Fechado", "Perdido"], 
                                      index=["Prospecção", "Reunião", "Proposta", "Fechado", "Perdido"].index(df_edit.iloc[escolha]['status']) if df_edit.iloc[escolha]['status'] in ["Prospecção", "Reunião", "Proposta", "Fechado", "Perdido"] else 0)
                new_val = st.number_input("Valor Atualizado", value=float(df_edit.iloc[escolha]['valor']))
                
                if st.form_submit_button("Salvar Alterações"):
                    c.execute('UPDATE leads SET status=?, valor=? WHERE rowid=?', 
                              (new_st, new_val, int(df_edit.iloc[escolha]['rowid'])))
                    conn.commit()
                    st.success("Lead atualizado!")
                    st.rerun()
        else: st.warning("Nenhum lead para editar.")

    # --- ADMINISTRAÇÃO DE USUÁRIOS ---
    elif menu == "Painel Admin":
        st.header("🔐 Controle de Acessos")
        df_users = pd.read_sql_query("SELECT username, role FROM users", conn)
        st.table(df_users)
        
        user_alvo = st.selectbox("Mudar cargo de:", df_users['username'])
        novo_cargo = st.selectbox("Novo Nível", ["user", "admin"])
        if st.button("Atualizar Cargo"):
            c.execute('UPDATE users SET role=? WHERE username=?', (novo_cargo, user_alvo))
            conn.commit()
            st.success(f"O usuário {user_alvo} agora é {novo_cargo}!")
