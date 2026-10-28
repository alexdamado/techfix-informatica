import os
import re
import gradio as gr
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
EMAIL = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

def get_db():
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    if not url or not key:
        raise RuntimeError('Credenciais do Supabase não configuradas.')
    return create_client(url, key)

def cadastrar(nome, endereco, email, celular, modelo, problema):
    campos = [nome, endereco, email, celular, modelo, problema]
    if not all(isinstance(x, str) and x.strip() for x in campos):
        return '❌ Preencha todos os campos obrigatórios.'
    email = email.strip().lower()
    celular = celular.strip()
    if not EMAIL.fullmatch(email):
        return '❌ Informe um e-mail válido.'
    if not celular.isdigit() or not 10 <= len(celular) <= 13:
        return '❌ Celular: apenas números, de 10 a 13 dígitos.'
    try:
        db = get_db()
        resultado = db.table('clientes').select('id').eq('email', email).limit(1).execute()
        if resultado.data:
            cliente_id = resultado.data[0]['id']
        else:
            try:
                novo = db.table('clientes').insert({
                    'nome': nome.strip(), 'endereco': endereco.strip(),
                    'email': email, 'celular_whatsapp': celular
                }).execute()
                cliente_id = novo.data[0]['id']
            except Exception:
                # Em caso de cadastro simultâneo, tente recuperar pelo e-mail único.
                existente = db.table('clientes').select('id').eq('email', email).limit(1).execute()
                if not existente.data:
                    raise
                cliente_id = existente.data[0]['id']
        os_nova = db.table('ordens_servico').insert({
            'cliente_id': cliente_id, 'modelo_computador': modelo.strip(),
            'problema_relatado': problema.strip(), 'status': 'Aberto'
        }).execute()
        return f"✅ Ordem de serviço nº {os_nova.data[0]['id']} cadastrada com sucesso! Status: Aberto."
    except Exception:
        return '❌ Não foi possível salvar. Verifique a conexão e as configurações do banco.'

with gr.Blocks(title='TechFix | Atendimento') as demo:
    gr.Markdown('# 🛠️ TechFix Informática\nCadastro de clientes e abertura de ordens de serviço. Use apenas dados fictícios.')
    with gr.Column():
        nome = gr.Textbox(label='Nome do cliente', placeholder='Ex.: Maria Exemplo')
        endereco = gr.Textbox(label='Endereço', placeholder='Ex.: Rua Fictícia, 123')
        email = gr.Textbox(label='E-mail', placeholder='Ex.: maria@example.com')
        celular = gr.Textbox(label='Celular / WhatsApp', placeholder='Somente números, com DDD')
        modelo = gr.Textbox(label='Modelo do computador', placeholder='Ex.: Notebook Modelo X')
        problema = gr.Textbox(label='Problema apresentado', lines=4, placeholder='Descreva o defeito')
        with gr.Row():
            enviar = gr.Button('Cadastrar', variant='primary')
            limpar = gr.Button('Limpar')
        retorno = gr.Textbox(label='Resultado', interactive=False)
    enviar.click(cadastrar, inputs=[nome, endereco, email, celular, modelo, problema], outputs=retorno)
    limpar.click(lambda: ('', '', '', '', '', '', ''), outputs=[nome, endereco, email, celular, modelo, problema, retorno])

if __name__ == '__main__':
    demo.launch(share=os.getenv('GRADIO_SHARE', 'false').lower() == 'true', auth=(os.environ['GRADIO_USER'], os.environ['GRADIO_PASSWORD']) if os.getenv('GRADIO_USER') and os.getenv('GRADIO_PASSWORD') else None)
