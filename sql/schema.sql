--
-- PostgreSQL database dump
--

-- Dumped from database version 9.1.4
-- Dumped by pg_dump version 9.1.4
-- Started on 2012-07-13 11:43:31 MSK

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- TOC entry 2785 (class 1262 OID 16581)
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
-- TOC entry 171 (class 3079 OID 12518)
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- TOC entry 2788 (class 0 OID 0)
-- Dependencies: 171
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 165 (class 1259 OID 16613)
-- Dependencies: 2762 5
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
-- Dependencies: 165 5
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
-- TOC entry 2789 (class 0 OID 0)
-- Dependencies: 164
-- Name: channels_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: rsdn
--

ALTER SEQUENCE channels_logs_id_seq OWNED BY channels_logs.id;


--
-- TOC entry 163 (class 1259 OID 16601)
-- Dependencies: 2760 5
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
-- TOC entry 2790 (class 0 OID 0)
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
-- TOC entry 170 (class 1259 OID 19635)
-- Dependencies: 5
-- Name: rsdn_moderate; Type: TABLE; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE TABLE rsdn_moderate (
    messageid bigint NOT NULL,
    topicid bigint NOT NULL,
    userid bigint NOT NULL,
    forumid integer NOT NULL,
    crerate timestamp with time zone
);


ALTER TABLE public.rsdn_moderate OWNER TO rsdn;

--
-- TOC entry 169 (class 1259 OID 19632)
-- Dependencies: 5
-- Name: rsdn_rating; Type: TABLE; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE TABLE rsdn_rating (
    messageid bigint,
    topicid bigint,
    userid bigint,
    userrating integer,
    rate integer,
    ratedate timestamp with time zone
);


ALTER TABLE public.rsdn_rating OWNER TO rsdn;

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
-- Dependencies: 2758 5
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
-- TOC entry 2791 (class 0 OID 0)
-- Dependencies: 167
-- Name: rsdn_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: rsdn
--

ALTER SEQUENCE rsdn_users_id_seq OWNED BY rsdn_users.id;


--
-- TOC entry 2761 (class 2604 OID 16616)
-- Dependencies: 164 165 165
-- Name: id; Type: DEFAULT; Schema: public; Owner: rsdn
--

ALTER TABLE ONLY channels_logs ALTER COLUMN id SET DEFAULT nextval('channels_logs_id_seq'::regclass);


--
-- TOC entry 2759 (class 2604 OID 16604)
-- Dependencies: 163 162 163
-- Name: id; Type: DEFAULT; Schema: public; Owner: rsdn
--

ALTER TABLE ONLY nicknames ALTER COLUMN id SET DEFAULT nextval('nicknames_id_seq'::regclass);


--
-- TOC entry 2757 (class 2604 OID 16655)
-- Dependencies: 167 161
-- Name: id; Type: DEFAULT; Schema: public; Owner: rsdn
--

ALTER TABLE ONLY rsdn_users ALTER COLUMN id SET DEFAULT nextval('rsdn_users_id_seq'::regclass);


--
-- TOC entry 2775 (class 2606 OID 16622)
-- Dependencies: 165 165
-- Name: pkey_channels_logs; Type: CONSTRAINT; Schema: public; Owner: rsdn; Tablespace: 
--

ALTER TABLE ONLY channels_logs
    ADD CONSTRAINT pkey_channels_logs PRIMARY KEY (id);


--
-- TOC entry 2771 (class 2606 OID 20524)
-- Dependencies: 163 163
-- Name: pkey_nicknames; Type: CONSTRAINT; Schema: public; Owner: rsdn; Tablespace: 
--

ALTER TABLE ONLY nicknames
    ADD CONSTRAINT pkey_nicknames PRIMARY KEY (id);


--
-- TOC entry 2781 (class 2606 OID 16671)
-- Dependencies: 168 168
-- Name: pkey_rsdn_messages; Type: CONSTRAINT; Schema: public; Owner: rsdn; Tablespace: 
--

ALTER TABLE ONLY rsdn_messages
    ADD CONSTRAINT pkey_rsdn_messages PRIMARY KEY (id);


--
-- TOC entry 2767 (class 2606 OID 16663)
-- Dependencies: 161 161
-- Name: pkey_rsdn_users; Type: CONSTRAINT; Schema: public; Owner: rsdn; Tablespace: 
--

ALTER TABLE ONLY rsdn_users
    ADD CONSTRAINT pkey_rsdn_users PRIMARY KEY (id);


--
-- TOC entry 2777 (class 2606 OID 16634)
-- Dependencies: 166 166
-- Name: pkey_rsdn_versions; Type: CONSTRAINT; Schema: public; Owner: rsdn; Tablespace: 
--

ALTER TABLE ONLY rsdn_row_versions
    ADD CONSTRAINT pkey_rsdn_versions PRIMARY KEY (name);


--
-- TOC entry 2772 (class 1259 OID 20520)
-- Dependencies: 165
-- Name: i_channels_logs_channel; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_channels_logs_channel ON channels_logs USING btree (channel);


--
-- TOC entry 2773 (class 1259 OID 20519)
-- Dependencies: 165
-- Name: i_channels_logs_nick; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_channels_logs_nick ON channels_logs USING btree (nickname_id);


--
-- TOC entry 2768 (class 1259 OID 20525)
-- Dependencies: 163
-- Name: i_nicknames_nickname; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_nicknames_nickname ON nicknames USING btree (nickname);


--
-- TOC entry 2769 (class 1259 OID 20526)
-- Dependencies: 163
-- Name: i_nicknames_rsdn; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_nicknames_rsdn ON nicknames USING btree (rsdn_user_id);


--
-- TOC entry 2778 (class 1259 OID 20472)
-- Dependencies: 168
-- Name: i_rsdn_messages_parentid; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_rsdn_messages_parentid ON rsdn_messages USING btree (parentid);


--
-- TOC entry 2779 (class 1259 OID 20471)
-- Dependencies: 168
-- Name: i_rsdn_messages_userid; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_rsdn_messages_userid ON rsdn_messages USING btree (userid);


--
-- TOC entry 2782 (class 1259 OID 20479)
-- Dependencies: 169 169 169
-- Name: i_rsdn_rating_ids; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_rsdn_rating_ids ON rsdn_rating USING btree (messageid, topicid, userid);


--
-- TOC entry 2763 (class 1259 OID 20505)
-- Dependencies: 161
-- Name: i_rsdn_users_realname; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_rsdn_users_realname ON rsdn_users USING btree (realname);


--
-- TOC entry 2764 (class 1259 OID 20503)
-- Dependencies: 161
-- Name: i_rsdn_users_username; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_rsdn_users_username ON rsdn_users USING btree (username);


--
-- TOC entry 2765 (class 1259 OID 20504)
-- Dependencies: 161
-- Name: i_rsdn_users_usernick; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_rsdn_users_usernick ON rsdn_users USING btree (usernick);


--
-- TOC entry 2787 (class 0 OID 0)
-- Dependencies: 5
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


-- Completed on 2012-07-13 11:43:31 MSK

--
-- PostgreSQL database dump complete
--

