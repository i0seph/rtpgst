--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


SET search_path = public, pg_catalog;

--
-- Name: tr_manage_stat_table(); Type: FUNCTION; Schema: public; Owner: statagent
--

CREATE FUNCTION tr_manage_stat_table() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
declare
	qstr text;
begin
    if tg_op = 'INSERT' then
       qstr := 'create table if not exists statdata_' || new.agent_id || ' (like statdata including all)';
       execute qstr;
       return new;
    elsif tg_op = 'DELETE' then
       execute 'drop table if exists statdata_' || old.agent_id;
       return old;
    end if;
end;
$$;


ALTER FUNCTION public.tr_manage_stat_table() OWNER TO statagent;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: agent_config; Type: TABLE; Schema: public; Owner: statagent; Tablespace: 
--

CREATE TABLE agent_config (
    agent_id integer NOT NULL,
    dbhost inet NOT NULL,
    check_interval integer DEFAULT 10 NOT NULL,
    datakeep_interval interval DEFAULT '1 mon'::interval NOT NULL,
    page_title character varying(128),
    dbport integer DEFAULT 5432 NOT NULL,
    dbname name NOT NULL
);


ALTER TABLE public.agent_config OWNER TO statagent;

--
-- Name: agent_config_agent_id_seq; Type: SEQUENCE; Schema: public; Owner: statagent
--

CREATE SEQUENCE agent_config_agent_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.agent_config_agent_id_seq OWNER TO statagent;

--
-- Name: agent_config_agent_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: statagent
--

ALTER SEQUENCE agent_config_agent_id_seq OWNED BY agent_config.agent_id;


--
-- Name: agent_users; Type: TABLE; Schema: public; Owner: statagent; Tablespace: 
--

CREATE TABLE agent_users (
    username text NOT NULL,
    password text NOT NULL,
    agents integer[]
);


ALTER TABLE public.agent_users OWNER TO statagent;

--
-- Name: logdata_3; Type: TABLE; Schema: public; Owner: statagent; Tablespace: 
--

CREATE TABLE logdata_3 (
    ctime timestamp without time zone NOT NULL,
    data json
);


ALTER TABLE public.logdata_3 OWNER TO statagent;

--
-- Name: statdata; Type: TABLE; Schema: public; Owner: statagent; Tablespace: 
--

CREATE TABLE statdata (
    ctime timestamp without time zone NOT NULL,
    data json
);


ALTER TABLE public.statdata OWNER TO statagent;

--
-- Name: statdata_3; Type: TABLE; Schema: public; Owner: statagent; Tablespace: 
--

CREATE TABLE statdata_3 (
    ctime timestamp without time zone NOT NULL,
    data json
);


ALTER TABLE public.statdata_3 OWNER TO statagent;

--
-- Name: agent_id; Type: DEFAULT; Schema: public; Owner: statagent
--

ALTER TABLE ONLY agent_config ALTER COLUMN agent_id SET DEFAULT nextval('agent_config_agent_id_seq'::regclass);


--
-- Name: agent_config_dbhost_dbport_dbname_key; Type: CONSTRAINT; Schema: public; Owner: statagent; Tablespace: 
--

ALTER TABLE ONLY agent_config
    ADD CONSTRAINT agent_config_dbhost_dbport_dbname_key UNIQUE (dbhost, dbport, dbname);


--
-- Name: agent_config_pkey; Type: CONSTRAINT; Schema: public; Owner: statagent; Tablespace: 
--

ALTER TABLE ONLY agent_config
    ADD CONSTRAINT agent_config_pkey PRIMARY KEY (agent_id);


--
-- Name: agent_users_pkey; Type: CONSTRAINT; Schema: public; Owner: statagent; Tablespace: 
--

ALTER TABLE ONLY agent_users
    ADD CONSTRAINT agent_users_pkey PRIMARY KEY (username);


--
-- Name: logdata_3_pkey; Type: CONSTRAINT; Schema: public; Owner: statagent; Tablespace: 
--

ALTER TABLE ONLY logdata_3
    ADD CONSTRAINT logdata_3_pkey PRIMARY KEY (ctime);


--
-- Name: statdata_3_pkey; Type: CONSTRAINT; Schema: public; Owner: statagent; Tablespace: 
--

ALTER TABLE ONLY statdata_3
    ADD CONSTRAINT statdata_3_pkey PRIMARY KEY (ctime);


--
-- Name: statdata_pkey; Type: CONSTRAINT; Schema: public; Owner: statagent; Tablespace: 
--

ALTER TABLE ONLY statdata
    ADD CONSTRAINT statdata_pkey PRIMARY KEY (ctime);


--
-- Name: tr_manage_stat_table; Type: TRIGGER; Schema: public; Owner: statagent
--

CREATE TRIGGER tr_manage_stat_table AFTER INSERT OR DELETE ON agent_config FOR EACH ROW EXECUTE PROCEDURE tr_manage_stat_table();


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

