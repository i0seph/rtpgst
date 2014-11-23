CREATE OR REPLACE FUNCTION tr_manage_stat_table() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
declare
	qstr text;
begin
    if tg_op = 'INSERT' then
       execute 'create table if not exists statdata_' || new.agent_id || ' (like statdata including all)';
       execute 'alter table statdata_' || new.agent_id || ' owner to statagent';
       execute 'create table if not exists dw1min.statdata_' || new.agent_id || ' (like statdata including all)';
       execute 'alter table dw1min.statdata_' || new.agent_id || ' owner to statagent';
       execute 'create table if not exists dw15min.statdata_' || new.agent_id || ' (like statdata including all)';
       execute 'alter table dw15min.statdata_' || new.agent_id || ' owner to statagent';
       return new;
    elsif tg_op = 'DELETE' then
       execute 'drop table if exists statdata_' || old.agent_id;
       execute 'drop table if exists dw1min.statdata_' || old.agent_id;
       execute 'drop table if exists dw15min.statdata_' || old.agent_id;
       return old;
    end if;
end;
$$;
