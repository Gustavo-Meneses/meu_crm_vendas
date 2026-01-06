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

# Tabelas atualizadas
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (username TEXT, password TEXT, role TEXT, pergunta_seg TEXT, resposta_seg TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS leads 
             (nome TEXT, empresa TEXT, status TEXT, historico TEXT, score INTEGER, valor REAL)''')
conn.commit()

# --- FUNÇÕES DE SEGURANÇA ---
def hash_pw(pw): return hashlib.sha256(str.encode(pw)).hexdigest()

# Criar Admin Padrão (Gustavo Meneses) se não existir
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

# --- LOGIN E RECUPERAÇÃO ---
if 'logado' not in st.session_state: st.session_state.logado = False
if 'user_role' not in st.session_state: st.session_state.user_role = "user"

if not st.session_state.logado:
    st.title("🚀 CRM - Acesso")
    tab1, tab2, tab3 = st.tabs(["Login", "Registrar", "Esqueci a Senha"])
    
    with tab1:
        u = st.text_input("Usuário", key="login_u")
        p = st.text_input("Senha", type='password', key="login_p")
        if st.button("Entrar"):
            c.execute('SELECT password, role FROM users WHERE username=?', (u,))
            user = c.fetchone()
            if user and user[0] == hash_pw(p):
                st.session_state.logado = True
                st.session_state.user_name = u
                st.session_state.user_role = user[1]
                st.rerun()
            else: st.error("Dados incorretos.")

    with tab2:
        new_u = st.text_input("Novo Usuário")
        new_p = st.text_input("Nova Senha", type='password')
        perg = st.selectbox("Pergunta de Segurança", ["Qual o nome do seu pet?", "Sua cor favorita?", "Nome da sua mãe?"])
        resp = st.text_input("Resposta de Segurança")
        role = st.selectbox("Cargo", ["user", "admin"]) if u == "Gustavo Meneses" else "user"
        
        if st.button("Criar Conta"):
            c.execute('INSERT INTO users VALUES (?,?,?,?,?)', (new_u, hash_pw(new_p), role, perg, hash_pw(resp)))
            conn.commit()
            st.success("Conta criada!")

    with tab3:
        st.subheader("Recuperar Senha")
        u_rec = st.text_input("Usuário para recuperar")
        if u_rec:
            c.execute('SELECT pergunta_seg, resposta_seg FROM users WHERE username=?', (u_rec,))
            dados = c.fetchone()
            if dados:
                st.info(dados[0])
                resp_rec = st.text_input("Sua resposta")
                nova_p = st.text_input("Nova senha desejada", type="password")
                if st.button("Redefinir"):
                    if hash_pw(resp_rec) == dados[1]:
                        c.execute('UPDATE users SET password=? WHERE username=?', (hash_pw(nova_p), u_rec))
                        conn.commit()
                        st.success("Senha alterada com sucesso!")
                    else: st.error("Resposta incorreta.")

# --- APP PRINCIPAL ---
else:
    st.sidebar.title(f"Olá, {st.session_state.user_name}")
    menu_options = ["Dashboard", "Adicionar Lead (IA)", "Editar Leads"]
    if st.session_state.user_role == "admin":
        menu_options.append("Admin - Usuários")
    
    page = st.sidebar.radio("Menu", menu_options)
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # 1. FUNÇÃO DASHBOARD (COM GRÁFICOS)
    if page == "Dashboard":
        st.header("📊 Painel de Vendas")
        df = pd.read_sql_query("SELECT * FROM leads", conn)
        if not df.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de Leads", len(df))
            col2.metric("Pipeline Total", f"R$ {df['valor'].sum():,.2f}")
            col3.metric("Score Médio", f"{df['score'].mean():.1f}")
            
            st.subheader("Distribuição por Status")
            st.bar_chart(df['status'].value_counts())
            
            st.dataframe(df, use_container_width=True)
            
            # 2. FUNÇÃO EXPORTAR (EXCEL/CSV)
            st.subheader("📥 Exportar Dados")
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Baixar em CSV", csv, "leads.csv", "text/csv")
        else:
            st.info("Sem dados.")

    elif page == "Adicionar Lead (IA)":
        st.header("✍️ Captura Inteligente")
        texto = st.text_area("Descreva a interação:")
        if st.button("Analisar"):
            try:
                prompt = f"Gere JSON: {{'nome','empresa','status','resumo_conversa','score','valor'}}. Texto: {texto}"
                res = chamar_ia(prompt)
                d = json.loads(res.replace('```json', '').replace('```', '').strip())
                c.execute('INSERT INTO leads VALUES (?,?,?,?,?,?)', 
                          (d.get('nome',''), d.get('empresa',''), d.get('status',''), d.get('resumo_conversa',''), d.get('score',0), d.get('valor',0)))
                conn.commit()
                st.success("Salvo!")
            except Exception as e: st.error(f"{e}")

    # 3. FUNÇÃO EDIÇÃO MANUAL
    elif page == "Editar Leads":
        st.header("📝 Editar Leads Existentes")
        df = pd.read_sql_query("SELECT rowid, * FROM leads", conn)
        if not df.empty:
            lead_idx = st.selectbox("Selecione o Lead para editar", df.index, format_func=lambda x: f"{df.iloc[x]['nome']} ({df.iloc[x]['empresa']})")
            rowid = int(df.iloc[lead_idx]['rowid'])
            
            with st.form("form_edit"):
                new_status = st.selectbox("Status", ["Prospecção", "Reunião", "Proposta", "Fechado", "Perdido"], index=0)
                new_valor = st.number_input("Valor", value=float(df.iloc[lead_idx]['valor']))
                if st.form_submit_button("Atualizar Lead"):
                    c.execute('UPDATE leads SET status=?, valor=? WHERE rowid=?', (new_status, new_valor, rowid))
                    conn.commit()
                    st.success("Atualizado!")
                    st.rerun()
        else: st.info("Sem leads para editar.")

    elif page == "Admin - Usuários" and st.session_state.user_role == "admin":
        st.header("🛡️ Gestão de Usuários")
        df_u = pd.read_sql_query("SELECT username, role FROM users", conn)
        st.table(df_u)
        
        target_u = st.selectbox("Alterar cargo de:", df_u['username'])
        new_role = st.selectbox("Novo cargo", ["user", "admin"])
        if st.button("Confirmar Alteração"):
            c.execute('UPDATE users SET role=? WHERE username=?', (new_role, target_u))
            conn.commit()
            st.success("Cargo alterado!")
