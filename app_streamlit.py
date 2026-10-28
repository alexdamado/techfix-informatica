import os
import re
import hmac
from io import StringIO
import pandas as pd
import streamlit as st
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title='TechFix | Gerência', page_icon='🛠️', layout='wide')
STATUS = ['Aberto', 'Em análise', 'Aguardando peça', 'Concluído', 'Entregue']
EMAIL = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

def secret(name):
    return os.getenv(name) or st.secrets.get(name, '')

def db():
    if not secret('SUPABASE_URL') or not secret('SUPABASE_KEY'):
        raise RuntimeError('Credenciais não configuradas')
    return create_client(secret('SUPABASE_URL'), secret('SUPABASE_KEY'))

def validate(nome, endereco, email, celular, modelo=None, problema=None):
    if not all(str(x).strip() for x in [nome, endereco, email, celular]):
        raise ValueError('Preencha os dados do cliente.')
    if not EMAIL.fullmatch(email.strip()):
        raise ValueError('E-mail inválido.')
    if not celular.isdigit() or not 10 <= len(celular) <= 13:
        raise ValueError('Celular deve conter 10 a 13 dígitos.')
    if modelo is not None and (not modelo.strip() or not problema.strip()):
        raise ValueError('Preencha modelo e problema.')

def load_data():
    try:
        clientes = db().table('clientes').select('*').order('id').range(0, 9999).execute().data or []
        ordens = db().table('ordens_servico').select('*').order('id', desc=True).range(0, 9999).execute().data or []
        base = pd.DataFrame(ordens)
        if base.empty:
            return pd.DataFrame(columns=['id','cliente_id','nome','email','celular_whatsapp','endereco','modelo_computador','problema_relatado','status','data_abertura','data_atualizacao']), clientes, ordens
        c = pd.DataFrame(clientes)
        if c.empty:
            return base, clientes, ordens
        merged = base.merge(c[['id','nome','email','celular_whatsapp','endereco']], left_on='cliente_id', right_on='id', suffixes=('','_cliente'), how='left')
        return merged.drop(columns=['id_cliente']), clientes, ordens
    except Exception:
        st.error('Não foi possível consultar o banco. Verifique as credenciais e a conexão.')
        return pd.DataFrame(), [], []

st.title('🛠️ TechFix Informática — Painel Gerencial')
st.caption('Demonstração acadêmica. Use apenas dados fictícios.')
password = secret('ADMIN_PASSWORD')
if not password:
    st.error('Configure ADMIN_PASSWORD nos segredos do aplicativo antes de utilizá-lo.')
    st.stop()
if not st.session_state.get('autenticado', False):
    with st.form('login'):
        senha = st.text_input('Senha de acesso do gerente', type='password')
        entrar = st.form_submit_button('Entrar')
    if entrar:
        if hmac.compare_digest(senha, password):
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error('Senha incorreta.')
    st.stop()

if st.sidebar.button('Sair'):
    st.session_state.autenticado = False
    st.rerun()

base, clientes, ordens = load_data()
st.sidebar.header('Filtros')
nome_filtro = st.sidebar.text_input('Nome do cliente')
email_filtro = st.sidebar.text_input('E-mail')
status_filtro = st.sidebar.selectbox('Status', ['Todos'] + STATUS)
filtrada = base.copy()
if not filtrada.empty:
    if nome_filtro:
        filtrada = filtrada[filtrada['nome'].fillna('').str.contains(nome_filtro, case=False, regex=False)]
    if email_filtro:
        filtrada = filtrada[filtrada['email'].fillna('').str.contains(email_filtro, case=False, regex=False)]
    if status_filtro != 'Todos':
        filtrada = filtrada[filtrada['status'] == status_filtro]

aba1, aba2, aba3, aba4 = st.tabs(['Consultar', 'Cadastrar', 'Editar/Excluir', 'Indicadores'])
with aba1:
    st.subheader('Ordens de serviço')
    st.dataframe(filtrada, use_container_width=True, hide_index=True)
    st.download_button('⬇️ Exportar CSV filtrado (+0,5)', filtrada.to_csv(index=False).encode('utf-8-sig'), 'techfix_ordens.csv', 'text/csv')
with aba2:
    st.subheader('Nova ordem de serviço')
    with st.form('nova_os', clear_on_submit=True):
        nome = st.text_input('Nome do cliente')
        endereco = st.text_input('Endereço')
        email = st.text_input('E-mail')
        celular = st.text_input('Celular / WhatsApp (somente números)')
        modelo = st.text_input('Modelo do computador')
        problema = st.text_area('Problema apresentado')
        enviar = st.form_submit_button('Cadastrar OS')
    if enviar:
        try:
            validate(nome, endereco, email, celular, modelo, problema)
            client = db()
            email = email.strip().lower()
            encontrados = client.table('clientes').select('id').eq('email', email).limit(1).execute().data
            if encontrados:
                cliente_id = encontrados[0]['id']
            else:
                try:
                    criado = client.table('clientes').insert({'nome': nome.strip(), 'endereco': endereco.strip(), 'email': email, 'celular_whatsapp': celular}).execute().data
                    cliente_id = criado[0]['id']
                except Exception:
                    recuperado = client.table('clientes').select('id').eq('email', email).limit(1).execute().data
                    if not recuperado:
                        raise
                    cliente_id = recuperado[0]['id']
            os_criada = client.table('ordens_servico').insert({'cliente_id': cliente_id, 'modelo_computador': modelo.strip(), 'problema_relatado': problema.strip(), 'status': 'Aberto'}).execute().data
            st.success(f"OS nº {os_criada[0]['id']} criada. Atualize a página para consultar.")
        except ValueError as e:
            st.warning(str(e))
        except Exception:
            st.error('Falha ao cadastrar. Verifique os dados e a conexão.')
with aba3:
    st.subheader('Editar ordem de serviço')
    if ordens:
        ids = [x['id'] for x in ordens]
        escolhido = st.selectbox('Número da OS', ids)
        ordem = next(x for x in ordens if x['id'] == escolhido)
        cliente = next((x for x in clientes if x['id'] == ordem['cliente_id']), None)
        if cliente:
            with st.form('editar'):
                novo_status = st.selectbox('Status', STATUS, index=STATUS.index(ordem['status']))
                novo_endereco = st.text_input('Endereço', cliente['endereco'])
                novo_email = st.text_input('E-mail', cliente['email'])
                novo_celular = st.text_input('Celular', cliente['celular_whatsapp'])
                salvar = st.form_submit_button('Salvar alterações')
            if salvar:
                try:
                    validate(cliente['nome'], novo_endereco, novo_email, novo_celular)
                    client = db()
                    client.table('clientes').update({'endereco': novo_endereco.strip(), 'email': novo_email.strip().lower(), 'celular_whatsapp': novo_celular}).eq('id', cliente['id']).execute()
                    client.table('ordens_servico').update({'status': novo_status}).eq('id', escolhido).execute()
                    st.success('Alterações salvas. Atualize a página para conferir.')
                except ValueError as e:
                    st.warning(str(e))
                except Exception:
                    st.error('Não foi possível salvar (verifique também se o e-mail já existe).')
            st.divider()
            st.subheader('Excluir registros')
            alvo = st.radio('O que excluir?', ['Apenas esta OS', 'Cliente e todas as suas OS'], horizontal=True)
            confirmar = st.checkbox('Confirmo a exclusão definitiva dos registros selecionados')
            if st.button('Excluir definitivamente', disabled=not confirmar, type='secondary'):
                try:
                    client = db()
                    if alvo == 'Apenas esta OS':
                        client.table('ordens_servico').delete().eq('id', escolhido).execute()
                    else:
                        client.table('clientes').delete().eq('id', cliente['id']).execute()
                    st.success('Exclusão concluída. Atualize a página.')
                except Exception:
                    st.error('Falha ao excluir os registros.')
    else:
        st.info('Nenhuma ordem cadastrada.')
with aba4:
    st.subheader('Indicadores de atendimento')
    contagem = base['status'].value_counts().reindex(STATUS, fill_value=0) if 'status' in base.columns else pd.Series(0, index=STATUS)
    st.metric('Total de OS', int(contagem.sum()))
    colunas = st.columns(5)
    for col, status in zip(colunas, STATUS):
        col.metric(status, int(contagem[status]))
    st.bar_chart(contagem.rename('Quantidade'))
