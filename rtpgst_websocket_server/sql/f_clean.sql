CREATE FUNCTION f_clean_statdata() RETURNS integer
    LANGUAGE plpgsql
    AS $$
declare
        v_row record;
begin
	for v_row in execute 'select ''delete from statdata_'' || agent_id || '' where ctime < '''''' || cast(current_timestamp - datakeep_interval as timestamp) || '''''''' as qstr   from agent_config'
        loop
		execute v_row.qstr;
	end loop;
return 0;
end;
$$;

