--
-- PostgreSQL database dump
--

-- Dumped from database version 9.1.4
-- Dumped by pg_dump version 9.1.4
-- Started on 2012-07-12 13:04:41 MSK

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- TOC entry 2765 (class 1262 OID 16581)
-- Name: rsdn-irc-bot; Type: DATABASE; Schema: -; Owner: rsdn
--

CREATE DATABASE "rsdn-irc-bot" WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'ru_RU.UTF-8' LC_CTYPE = 'ru_RU.UTF-8';


ALTER DATABASE "rsdn-irc-bot" OWNER TO rsdn;

\connect "rsdn-irc-bot"

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- TOC entry 169 (class 3079 OID 12518)
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- TOC entry 2768 (class 0 OID 0)
-- Dependencies: 169
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 165 (class 1259 OID 16613)
-- Dependencies: 2754 5
-- Name: channels_logs; Type: TABLE; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE TABLE channels_logs (
    id bigint NOT NULL,
    nickname_id bigint NOT NULL,
    date_and_time timestamp without time zone DEFAULT now() NOT NULL,
    message text,
    channel character varying(128) NOT NULL,
    is_bot_command boolean
);


ALTER TABLE public.channels_logs OWNER TO rsdn;

--
-- TOC entry 164 (class 1259 OID 16611)
-- Dependencies: 5 165
-- Name: channels_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: rsdn
--

CREATE SEQUENCE channels_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.channels_logs_id_seq OWNER TO rsdn;

--
-- TOC entry 2769 (class 0 OID 0)
-- Dependencies: 164
-- Name: channels_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: rsdn
--

ALTER SEQUENCE channels_logs_id_seq OWNED BY channels_logs.id;


--
-- TOC entry 163 (class 1259 OID 16601)
-- Dependencies: 2752 5
-- Name: nicknames; Type: TABLE; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE TABLE nicknames (
    id bigint NOT NULL,
    nickname character varying(128) NOT NULL,
    rsdn_user_id bigint DEFAULT 0 NOT NULL,
    last_seen timestamp with time zone
);


ALTER TABLE public.nicknames OWNER TO rsdn;

--
-- TOC entry 162 (class 1259 OID 16599)
-- Dependencies: 5 163
-- Name: nicknames_id_seq; Type: SEQUENCE; Schema: public; Owner: rsdn
--

CREATE SEQUENCE nicknames_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.nicknames_id_seq OWNER TO rsdn;

--
-- TOC entry 2770 (class 0 OID 0)
-- Dependencies: 162
-- Name: nicknames_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: rsdn
--

ALTER SEQUENCE nicknames_id_seq OWNED BY nicknames.id;


--
-- TOC entry 168 (class 1259 OID 16664)
-- Dependencies: 5
-- Name: rsdn_messages; Type: TABLE; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE TABLE rsdn_messages (
    id bigint NOT NULL,
    topicid bigint NOT NULL,
    parentid bigint NOT NULL,
    userid bigint NOT NULL,
    forumid bigint NOT NULL,
    subject character varying(256),
    messagename character varying(256),
    message text,
    articleid bigint NOT NULL,
    messagedate timestamp with time zone,
    updatedate timestamp with time zone,
    userrole character varying(32),
    usertitle character varying(64),
    lastmoderated timestamp with time zone,
    closed boolean
);


ALTER TABLE public.rsdn_messages OWNER TO rsdn;

--
-- TOC entry 166 (class 1259 OID 16627)
-- Dependencies: 5
-- Name: rsdn_row_versions; Type: TABLE; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE TABLE rsdn_row_versions (
    name character varying(128) NOT NULL,
    value text
);


ALTER TABLE public.rsdn_row_versions OWNER TO rsdn;

--
-- TOC entry 161 (class 1259 OID 16591)
-- Dependencies: 2750 5
-- Name: rsdn_users; Type: TABLE; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE TABLE rsdn_users (
    usernick character varying(128),
    username character varying(128),
    realname character varying(128),
    homepage character varying(1024),
    wherefrom character varying(256),
    origin character varying(1024),
    id bigint NOT NULL,
    confirmed boolean DEFAULT false NOT NULL,
    specialization character varying(1024),
    userclass smallint
);


ALTER TABLE public.rsdn_users OWNER TO rsdn;

--
-- TOC entry 167 (class 1259 OID 16653)
-- Dependencies: 5 161
-- Name: rsdn_users_id_seq; Type: SEQUENCE; Schema: public; Owner: rsdn
--

CREATE SEQUENCE rsdn_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.rsdn_users_id_seq OWNER TO rsdn;

--
-- TOC entry 2771 (class 0 OID 0)
-- Dependencies: 167
-- Name: rsdn_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: rsdn
--

ALTER SEQUENCE rsdn_users_id_seq OWNED BY rsdn_users.id;


--
-- TOC entry 2753 (class 2604 OID 16616)
-- Dependencies: 164 165 165
-- Name: id; Type: DEFAULT; Schema: public; Owner: rsdn
--

ALTER TABLE ONLY channels_logs ALTER COLUMN id SET DEFAULT nextval('channels_logs_id_seq'::regclass);


--
-- TOC entry 2751 (class 2604 OID 16604)
-- Dependencies: 162 163 163
-- Name: id; Type: DEFAULT; Schema: public; Owner: rsdn
--

ALTER TABLE ONLY nicknames ALTER COLUMN id SET DEFAULT nextval('nicknames_id_seq'::regclass);


--
-- TOC entry 2749 (class 2604 OID 16655)
-- Dependencies: 167 161
-- Name: id; Type: DEFAULT; Schema: public; Owner: rsdn
--

ALTER TABLE ONLY rsdn_users ALTER COLUMN id SET DEFAULT nextval('rsdn_users_id_seq'::regclass);


--
-- TOC entry 2758 (class 2606 OID 16622)
-- Dependencies: 165 165
-- Name: pkey_channels_logs; Type: CONSTRAINT; Schema: public; Owner: rsdn; Tablespace: 
--

ALTER TABLE ONLY channels_logs
    ADD CONSTRAINT pkey_channels_logs PRIMARY KEY (id);


--
-- TOC entry 2762 (class 2606 OID 16671)
-- Dependencies: 168 168
-- Name: pkey_rsdn_messages; Type: CONSTRAINT; Schema: public; Owner: rsdn; Tablespace: 
--

ALTER TABLE ONLY rsdn_messages
    ADD CONSTRAINT pkey_rsdn_messages PRIMARY KEY (id);


--
-- TOC entry 2756 (class 2606 OID 16663)
-- Dependencies: 161 161
-- Name: pkey_rsdn_users; Type: CONSTRAINT; Schema: public; Owner: rsdn; Tablespace: 
--

ALTER TABLE ONLY rsdn_users
    ADD CONSTRAINT pkey_rsdn_users PRIMARY KEY (id);


--
-- TOC entry 2760 (class 2606 OID 16634)
-- Dependencies: 166 166
-- Name: pkey_rsdn_versions; Type: CONSTRAINT; Schema: public; Owner: rsdn; Tablespace: 
--

ALTER TABLE ONLY rsdn_row_versions
    ADD CONSTRAINT pkey_rsdn_versions PRIMARY KEY (name);


--
-- TOC entry 2767 (class 0 OID 0)
-- Dependencies: 5
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


-- Completed on 2012-07-12 13:04:41 MSK

--
-- PostgreSQL database dump complete
--

