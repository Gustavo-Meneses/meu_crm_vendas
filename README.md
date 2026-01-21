# 🚀 AI CRM Pro - Inteligência Comercial (Mistral AI Edition)

Este é um sistema de CRM (Customer Relationship Management) inteligente desenvolvido com **Python** e **Streamlit**. O projeto utiliza a API da **Mistral AI** para processar textos informais (e-mails, conversas de WhatsApp, notas de reuniões) e transformá-los automaticamente em dados estruturados para gestão comercial.

## 🌟 Principais Funcionalidades

- **Captura Inteligente via IA:** Extração automática de Nome, Empresa, Valor, Status, Histórico e Score a partir de blocos de texto.
- **Motor de Alta Estabilidade:** Utiliza o modelo `mistral-small-latest` com suporte nativo a JSON, eliminando erros de formatação.
- **Dashboard Comercial:** Visualização métrica do pipeline de vendas e volume financeiro em negociação.
- **Exportação de Dados:** Função para baixar a base de leads capturada em formato CSV para uso em Excel ou outras ferramentas.
- **Acesso Restrito:** Sistema de login seguro para proteção dos dados da sessão.

## 🛠️ Tecnologias Utilizadas

- [Python](https://www.python.org/) - Base do projeto.
- [Streamlit](https://streamlit.io/) - Interface web dinâmica.
- [Mistral AI SDK](https://docs.mistral.ai/) - Inteligência Artificial para extração de dados.
- [Pandas](https://pandas.pydata.org/) - Manipulação e análise de tabelas.

## 🔑 Credenciais de Acesso

Para acessar o painel administrativo, utilize as seguintes credenciais padrão:

* **Usuário:** `ADM`
* **Senha:** `1234`

## 🚀 Como Executar o Projeto

### Pré-requisitos
1. Possuir o Python 3.9 ou superior.
2. Obter uma chave de API no [Mistral AI Console](https://console.mistral.ai/).

### Instalação e Execução
1. Clone este repositório:
   ```bash
   git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
   cd seu-repositorio
