-- TechFix Informática: estrutura relacional e integridade.
create table if not exists public.clientes (
    id bigint generated always as identity primary key
   ,nome text not null
   ,endereco text not null
   ,email text not null unique
   ,celular_whatsapp text not null
   ,data_cadastro timestamptz not null default now()
   ,constraint clientes_nome_check check (length(trim(nome)) > 0)
   ,constraint clientes_endereco_check check (length(trim(endereco)) > 0)
   ,constraint clientes_email_check check (email ~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$')
   ,constraint clientes_celular_check check (celular_whatsapp ~ '^[0-9]{10,13}$')
);
-- Uma OS pertence a um cliente; ao excluir o cliente, excluem-se suas OS.
create table if not exists public.ordens_servico (
    id bigint generated always as identity primary key
   ,cliente_id bigint not null
   ,modelo_computador text not null
   ,problema_relatado text not null
   ,status text not null default 'Aberto'
   ,data_abertura timestamptz not null default now()
   ,data_atualizacao timestamptz not null default now()
   ,constraint os_cliente_fk foreign key (cliente_id) references public.clientes(id) on delete cascade
   ,constraint os_modelo_check check (length(trim(modelo_computador)) > 0)
   ,constraint os_problema_check check (length(trim(problema_relatado)) > 0)
   ,constraint os_status_check check (status in ('Aberto','Em análise','Aguardando peça','Concluído','Entregue'))
);
-- Índices para consultas por cliente e status.
create index if not exists idx_os_cliente on public.ordens_servico(cliente_id);
create index if not exists idx_os_status on public.ordens_servico(status);
-- Atualiza automaticamente a data de modificação da OS.
create or replace function public.atualizar_data_os() returns trigger language plpgsql set search_path = '' as $$
begin
    new.data_atualizacao = now();
    return new;
end;
$$;
create or replace trigger trg_atualizar_data_os before update on public.ordens_servico
for each row execute function public.atualizar_data_os();
-- Proteção: somente servidor com chave privada acessa estas tabelas.
alter table public.clientes enable row level security;
alter table public.ordens_servico enable row level security;
revoke all on table public.clientes from anon, authenticated;
revoke all on table public.ordens_servico from anon, authenticated;
