# 🏢 AI CRM Pro - Gestão Comercial com Processamento em Lote

Plataforma corporativa de CRM desenvolvida com **Python** e **Streamlit**, equipada com um motor de Inteligência Artificial (**Mistral AI**) capaz de ler, interpretar e estruturar múltiplos leads de vendas simultaneamente.

## 🚀 O que há de novo? (Batch Processing)

Diferente de CRMs tradicionais onde você preenche formulários um a um, o **AI CRM Pro** aceita blocos de texto brutos contendo dezenas de clientes misturados.

O sistema utiliza **Padrões de Identificação (Regex)** para separar cada cliente pelo seu **ID** e envia os blocos individualmente para a IA, que retorna os dados estruturados para o Dashboard.

## 🌟 Funcionalidades Principais

* **Captura em Lote (Bulk):** Processa listas inteiras de e-mails, notas ou conversas de uma só vez.
* **Identificação Única (Upsert):** Se o sistema encontrar um `ID do Cliente` que já existe, ele **atualiza** as informações. Se for novo, ele **cria** o registro.
* **Dashboard Visual:** Gráficos prontos para apresentações (Status do Funil, Top 10 Clientes, Pipeline Financeiro).
* **Gestão de Acesso:** Sistema de Login e Cadastro de Usuários (Sessão).
* **Exportação Power BI:** Gera arquivos `.csv` limpos e padronizados.

## 🛠️ Stack Tecnológica

* **Linguagem:** [Python 3.9+](https://www.python.org/)
* **Frontend:** [Streamlit](https://streamlit.io/)
* **IA Engine:** [Mistral AI](https://docs.mistral.ai/) (Modelo: `mistral-small-latest`)
* **Manipulação de Dados:** [Pandas](https://pandas.pydata.org/) & [Regex](https://docs.python.org/3/library/re.html)

## 🔐 Credenciais de Acesso

O sistema possui uma conta administrativa padrão configurada:

* **Usuário:** `ADM`
* **Senha:** `1234`

*(Novos usuários podem ser cadastrados na tela de login, válidos para a sessão atual).*

## 📝 Formato de Entrada (Como usar)

Para processar múltiplos leads, cole o texto na aba **"➕ Capturar (Lote)"** seguindo o padrão **"ID do Cliente: [Número]"**:


ID do Cliente: 101
Reunião com a Empresa A. O valor do contrato é 50.000 reais.
Status: Proposta. Score: 90.

ID do Cliente: 102
O cliente da Empresa B recusou a oferta de 2.000.
Status: Perdido.
O sistema identificará automaticamente os blocos 101 e 102 e fará a análise separada.

🚀 Instalação e Configuração
1. Dependências
No terminal, instale as bibliotecas necessárias:

Bash
pip install streamlit pandas mistralai
2. Configuração da API Key
Crie um arquivo .streamlit/secrets.toml na raiz do projeto (ou configure nos Secrets do Streamlit Cloud):

Ini, TOML
MISTRAL_API_KEY = "SUA_CHAVE_DA_MISTRAL_AQUI"
3. Executando o Projeto
Bash
streamlit run app.py
⚠️ Nota sobre Persistência
Este sistema opera com Session State (memória volátil).

Os dados permanecem salvos enquanto a aba do navegador estiver aberta.

Para salvar seu trabalho permanentemente, utilize sempre o botão "📥 Exportar CSV" disponível no Dashboard antes de fechar o sistema.

Desenvolvido para automatizar a inteligência comercial e eliminar o trabalho manual de preenchimento de CRM. 📈
