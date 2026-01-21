Excelente escolha. Títulos corporativos transmitem mais credibilidade e profissionalismo ao projeto. Vamos usar **"Acesso ao Sistema de Gestão Comercial"**.

Aqui está o **código completo** atualizado com o novo título e mantendo a configuração do usuário **ADM**, seguido pelo **README** revisado.

### 1. Código Completo (`app.py`)

```python
import streamlit as st
import pandas as pd
from mistralai import Mistral
import json

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão Comercial Inteligente", layout="wide", page_icon="🏢")

# --- INICIALIZAÇÃO DE DADOS EM MEMÓRIA ---
if 'df_leads' not in st.session_state:
    st.session_state.df_leads = pd.DataFrame(columns=["nome", "empresa", "status", "historico", "score", "valor"])

if 'logado' not in st.session_state:
    st.session_state.logado = False

# --- FUNÇÃO IA (MISTRAL AI) ---
def processar_com_mistral(texto_entrada):
    try:
        api_key = st.secrets.get("MISTRAL_API_KEY")
        if not api_key:
            return "ERRO_CONFIG: Chave MISTRAL_API_KEY não encontrada nos Secrets."
        
        client = Mistral(api_key=api_key)
        model = "mistral-small-latest"
        
        prompt_sistema = (
            "Você é um analista de dados comerciais. Extraia do texto e retorne APENAS um JSON puro. "
            "Campos: nome, empresa, status (Prospecção, Reunião, Proposta, Fechado, Perdido), "
            "historico, score (0-100) e valor (numérico). "
            "Não adicione comentários, apenas o JSON."
        )

        response = client.chat.complete(
            model=model,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Extraia os dados deste lead: {texto_entrada}"}
            ],
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"ERRO_API: {str(e)}"

# --- INTERFACE DE LOGIN CORPORATIVA ---
if not st.session_state.logado:
    st.markdown("<h2 style='text-align: center;'>Acesso ao Sistema de Gestão Comercial</h2>", unsafe_content_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Insira suas credenciais para acessar o painel administrativo.</p>", unsafe_content_html=True)
    
    # Centralizando o formulário de login
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        
        if st.button("Autenticar", use_container_width=True):
            if u == "ADM" and p == "1234":
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Credenciais inválidas. Tente novamente.")

# --- APP PRINCIPAL (SISTEMA LOGADO) ---
else:
    st.sidebar.title("🏢 Portal do Analista")
    st.sidebar.markdown(f"**Usuário:** ADM")
    
    aba = st.sidebar.radio("Navegação Estratégica", ["📊 Dashboard de Vendas", "➕ Captura de Lead (IA)"])
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Encerrar Sessão"):
        st.session_state.logado = False
        st.rerun()

    # ABA: DASHBOARD
    if aba == "📊 Dashboard de Vendas":
        st.header("📊 Painel de Performance Comercial")
        if not st.session_state.df_leads.empty:
            total_leads = len(st.session_state.df_leads)
            valor_total = pd.to_numeric(st.session_state.df_leads['valor'], errors='coerce').sum()
            
            c1, c2 = st.columns(2)
            c1.metric("Volume de Leads", total_leads)
            c2.metric("Pipeline Estimado", f"R$ {valor_total:,.2f}")
            
            st.divider()
            st.subheader("Base de Prospecção Ativa")
            st.dataframe(st.session_state.df_leads, use_container_width=True)
            
            csv = st.session_state.df_leads.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exportar Relatório (CSV)", csv, "relatorio_leads.csv", "text/csv")
        else:
            st.info("Nenhum registro encontrado no pipeline atual.")

    # ABA: CAPTURA IA
    elif aba == "➕ Captura de Lead (IA)":
        st.header("⚡ Extração Inteligente de Leads")
        st.write("Utilize inteligência artificial para converter textos brutos em registros de CRM.")
        
        txt = st.text_area("Entrada de Dados (E-mail/WhatsApp/Notas):", height=200)
        
        if st.button("Processar Dados"):
            if txt:
                with st.spinner("O sistema está analisando as informações..."):
                    resultado = processar_com_mistral(txt)
                    
                    if "ERRO_API" in resultado:
                        st.error(f"Falha técnica: {resultado}")
                    else:
                        try:
                            dados = json.loads(resultado)
                            st.session_state.df_leads = pd.concat([
                                st.session_state.df_leads, 
                                pd.DataFrame([dados])
                            ], ignore_index=True)
                            
                            st.success("Lead processado e registrado com sucesso!")
                            st.json(dados)
                            st.balloons()
                        except Exception:
                            st.error("Erro na estruturação dos dados.")
            else:
                st.warning("Campo obrigatório vazio.")

```

---

### 2. README Atualizado (`README.md`)

```markdown
# 🏢 AI CRM Pro - Gestão Comercial Inteligente

Plataforma corporativa de CRM desenvolvida com **Python** e **Streamlit**, integrada à API da **Mistral AI** para automação de entrada de dados e gestão estratégica de leads.

## 🌟 Funcionalidades Principais
- **Acesso Corporativo:** Interface de login profissional e restrita.
- **Processamento de Linguagem Natural (LLM):** Extração automatizada de dados comerciais complexos a partir de textos informais.
- **Painel de Performance (Dashboard):** Acompanhamento métrico de volume de leads e pipeline financeiro.
- **Exportação Estruturada:** Geração de relatórios em CSV para integração com ferramentas de BI.

## 🛠️ Stack Tecnológica
- **Linguagem:** Python 3.9+
- **Frontend:** Streamlit
- **IA Engine:** Mistral AI (Model: mistral-small-latest)
- **Data:** Pandas para processamento de DataFrames.

## 🔐 Controle de Acesso
O sistema utiliza autenticação administrativa padrão para a sessão:
- **Usuário:** `ADM`
- **Senha:** `1234`

## 🚀 Instalação e Configuração

1. **Dependências:**
   ```bash
   pip install streamlit pandas mistralai

```

2. **Secrets do Streamlit:**
Configure sua chave de API nos Secrets do Streamlit Cloud ou no arquivo local `.streamlit/secrets.toml`:
```toml
MISTRAL_API_KEY = "SUA_CHAVE_AQUI"

```


3. **Execução:**
```bash
streamlit run app.py

```



## 📝 Observações Técnicas

Este sistema utiliza **Session State** para armazenamento volátil de dados. Recomendamos o uso da função **"Exportar Relatório (CSV)"** no Dashboard para garantir a persistência das informações fora do ambiente de execução.

---

Solução desenvolvida para otimizar o fluxo de prospecção e vendas. 📈

```

---

**O que você deve fazer agora:**
1. Atualize o `app.py` no GitHub.
2. Atualize o `README.md` no GitHub.
3. Como o título da aba do navegador também mudou para **"Gestão Comercial Inteligente"**, o app terá um aspecto muito mais sério e robusto.

**Deseja que eu adicione um logo (uma imagem ou ícone maior) no centro da tela de login para finalizar o visual corporativo?**

```
