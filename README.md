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
