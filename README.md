# 🚀 AI CRM Pro - Inteligência Comercial com Mistral AI

Este é um sistema de CRM (Customer Relationship Management) inteligente e ultraveloz, desenvolvido com **Python** e **Streamlit**. O projeto utiliza o modelo **Mistral Small** para extrair dados estruturados de textos informais, automatizando a entrada de leads com alta precisão.

## 🌟 Diferenciais desta Versão
- **Motor Mistral AI:** Migração para a API da Mistral AI, garantindo 100% de estabilidade e tempo de resposta reduzido.
- **Extração JSON Nativa:** Utiliza o modo de resposta estruturada da Mistral para garantir que os dados do lead sejam sempre válidos.
- **Modo de Memória Otimizado:** Gestão de dados via `session_state`, permitindo testes rápidos sem necessidade de configuração de banco de dados complexos.
- **Segurança:** Sistema de login integrado para proteção do painel de vendas.

## 🛠️ Tecnologias Utilizadas
- [Python](https://www.python.org/) - Linguagem principal.
- [Streamlit](https://streamlit.io/) - Interface do usuário.
- [Mistral AI SDK](https://docs.mistral.ai/) - Inteligência Artificial para processamento de linguagem natural.
- [Pandas](https://pandas.pydata.org/) - Estruturação e visualização de dados.

## 🚀 Como Instalar e Rodar

### 1. Requisitos
Certifique-se de ter o Python 3.9+ instalado.

### 2. Instalação de Dependências
No terminal, execute:
```bash
pip install streamlit pandas mistralai

3. Configuração de Chaves (Secrets)
Crie um arquivo em .streamlit/secrets.toml (local) ou configure no painel do Streamlit Cloud:
MISTRAL_API_KEY = "SUA_CHAVE_AQUI"

4. Executando o App
streamlit run app.py

📊 Estrutura do Sistema
 * Login: Acesso restrito (Padrão: Gustavo Meneses / 1234).
 * Dashboard: Visão geral do pipeline, métricas de valor total e volume de leads.
 * Captura IA: Área para colar e-mails ou conversas. A Mistral extrai automaticamente: Nome, Empresa, Status, Histórico, Score e Valor.
 * Exportação: Botão para baixar todos os leads da sessão em formato CSV.
📝 Nota sobre Persistência de Dados
Esta versão opera em Modo de Memória (Ephemeral). Isso significa que os dados residem na sessão do navegador. Para salvar permanentemente seus leads de teste, utilize o botão "Exportar CSV" disponível no Dashboard antes de encerrar a sessão.
Desenvolvido para transformar textos informais em oportunidades reais de negócio. 📈


