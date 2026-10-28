# TechFix Informática — Atividade 2

Sistema acadêmico fictício com cadastro em Gradio, gerenciamento em Streamlit e banco Supabase.

## Banco
Execute `sql/schema.sql` no SQL Editor do Supabase. As tabelas `clientes` e `ordens_servico` têm validações, chave estrangeira e RLS ativado.

## Credenciais
Nunca publique chaves. Copie `.env.example` para `.env` apenas em ambientes privados e configure `SUPABASE_URL`, `SUPABASE_KEY` (chave secreta do servidor) e `ADMIN_PASSWORD`. O `.env` está ignorado pelo Git.

No Streamlit Community Cloud, configure em **App settings → Secrets**:

```toml
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_KEY = "SUA_CHAVE_PRIVADA"
ADMIN_PASSWORD = "SENHA_FORTE_DO_GERENTE"
```

## Gradio no Google Colab (sem instalação no computador)

Abra um notebook no Colab, configure as credenciais em **Secrets** (ícone de chave), com os nomes `SUPABASE_URL`, `SUPABASE_KEY`, `GRADIO_USER`, `GRADIO_PASSWORD`. Marque o acesso do notebook a esses segredos. Execute:

```python
!git clone https://github.com/alexdamado/techfix-informatica.git
%cd techfix-informatica
!pip -q install -r requirements.txt
from google.colab import userdata
import os
for nome in ['SUPABASE_URL','SUPABASE_KEY','GRADIO_USER','GRADIO_PASSWORD']:
    os.environ[nome] = userdata.get(nome)
os.environ['GRADIO_SHARE'] = 'true'
!python app_gradio.py
```

O link Gradio é temporário. O login protege o formulário; não compartilhe as credenciais.

## Streamlit Community Cloud
Crie um app a partir deste repositório, branch `main`, arquivo principal `app_streamlit.py`, e configure os segredos antes de usar. A senha do gerente é obrigatória.

## Evidências
Inclua prints de: Gradio no celular, confirmação de cadastro, tabelas preenchidas no Supabase e painel Streamlit nas abas Consulta, Editar/Excluir e Indicadores.

**Importante:** sistema apenas demonstrativo, não adequado para dados reais de clientes. Use somente dados fictícios.
