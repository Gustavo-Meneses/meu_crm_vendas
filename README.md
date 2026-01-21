# 🏢 AI CRM Pro - Gestão Comercial Inteligente

Plataforma corporativa de CRM desenvolvida com **Python** e **Streamlit**, integrada à API da **Mistral AI** para automação de entrada de dados e gestão estratégica de leads.

Este sistema transforma textos informais (conversas de WhatsApp, e-mails e notas de reunião) em registros estruturados para o funil de vendas, eliminando o preenchimento manual de planilhas.

## 🌟 Funcionalidades Principais

- **Acesso Corporativo:** Interface de login profissional, segura e restrita para administradores.
- **Processamento de Linguagem Natural (LLM):** Extração automatizada de dados comerciais (Nome, Empresa, Valor, Score) utilizando o modelo `mistral-small-latest`.
- **Painel de Performance (Dashboard):** Visualização métrica do pipeline de vendas, ticket médio e volume financeiro em negociação.
- **Exportação Estruturada:** Função de download para relatórios em CSV, permitindo integração com Excel ou ferramentas de BI.

## 🛠️ Stack Tecnológica

- **Linguagem:** [Python 3.9+](https://www.python.org/)
- **Frontend:** [Streamlit](https://streamlit.io/)
- **IA Engine:** [Mistral AI](https://docs.mistral.ai/)
- **Processamento de Dados:** [Pandas](https://pandas.pydata.org/)

## 🔐 Controle de Acesso

O sistema utiliza autenticação administrativa para proteção do ambiente de dados:

* **Usuário:** `ADM`
* **Senha:** `1234`

## 🚀 Instalação e Configuração

### 1. Requisitos
Instale as bibliotecas necessárias via terminal:
```bash
pip install streamlit pandas mistralai

### 2. Chave de API (Secrets)
Obtenha sua chave no Mistral AI Console e configure-a nos Secrets do Streamlit Cloud ou no arquivo local .streamlit/secrets.toml:

Ini, TOML

MISTRAL_API_KEY = "SUA_CHAVE_AQUI"
### 3. Execução
Para rodar o projeto localmente:

Bash

streamlit run app.py
📝 Observações Técnicas
Este sistema utiliza Session State para o armazenamento volátil de dados.

Os dados permanecem ativos enquanto a aba do navegador estiver aberta.

Persistência: Como não há banco de dados fixo nesta versão, utilize sempre a função "Exportar Relatório (CSV)" no Dashboard para salvar as informações permanentemente antes de encerrar a sessão.

Solução desenvolvida para otimizar o fluxo de prospecção e acelerar o fechamento de vendas. 📈
