--
-- PostgreSQL database dump
--

-- Dumped from database version 9.1.4
-- Dumped by pg_dump version 9.1.4
-- Started on 2012-08-07 12:57:29 MSK

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- TOC entry 2799 (class 1262 OID 16581)
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
-- TOC entry 2802 (class 0 OID 0)
-- Dependencies: 171
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

--
-- TOC entry 184 (class 1255 OID 88823)
-- Dependencies: 5 524
-- Name: update_rsdn_messages(bigint, bigint, bigint, bigint, bigint, character varying, character varying, text, bigint, timestamp with time zone, timestamp with time zone, character varying, character varying, timestamp with time zone, boolean); Type: FUNCTION; Schema: public; Owner: rsdn
--

CREATE FUNCTION update_rsdn_messages(i_id bigint, i_topicid bigint, i_parentid bigint, i_userid bigint, i_forumid bigint, i_subject character varying, i_messagename character varying, i_message text, i_articleid bigint, i_messagedate timestamp with time zone, i_updatedate timestamp with time zone, i_userrole character varying, i_usertitle character varying, i_lastmoderated timestamp with time zone, i_closed boolean) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
begin
  begin
    INSERT INTO rsdn_messages(id, topicid, parentid, userid, forumid, subject, messagename,
                              message, articleid, messagedate, updatedate, userrole, usertitle,
                              lastmoderated, closed)
    VALUES (i_id, i_topicid, i_parentid, i_userid, i_forumid, i_subject, i_messagename,
            i_message, i_articleid, i_messagedate, i_updatedate, i_userrole, i_usertitle,
            i_lastmoderated, i_closed);
    EXCEPTION WHEN unique_violation THEN
        UPDATE rsdn_messages
        SET topicid=i_topicid, parentid=i_parentid, userid=i_userid, forumid=i_forumid, subject=i_subject,
            messagename=i_messagename, message=i_message, articleid=i_articleid, messagedate=i_messagedate, updatedate=i_updatedate,
            userrole=i_userrole, usertitle=i_usertitle, lastmoderated=i_lastmoderated, closed=i_closed
        WHERE id=i_id;
     return true;
  end;
  return false;
end;
$$;


ALTER FUNCTION public.update_rsdn_messages(i_id bigint, i_topicid bigint, i_parentid bigint, i_userid bigint, i_forumid bigint, i_subject character varying, i_messagename character varying, i_message text, i_articleid bigint, i_messagedate timestamp with time zone, i_updatedate timestamp with time zone, i_userrole character varying, i_usertitle character varying, i_lastmoderated timestamp with time zone, i_closed boolean) OWNER TO rsdn;

--
-- TOC entry 186 (class 1255 OID 107116)
-- Dependencies: 5 524
-- Name: update_rsdn_moderate(timestamp with time zone, bigint, bigint, bigint, bigint); Type: FUNCTION; Schema: public; Owner: rsdn
--

CREATE FUNCTION update_rsdn_moderate(i_crerate timestamp with time zone, i_messageid bigint, i_topicid bigint, i_userid bigint, i_forumid bigint) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
begin
  begin
    INSERT INTO rsdn_moderate(crerate, messageid, topicid, userid, forumid)
    VALUES(i_crerate, i_messageid, i_topicid, i_userid, i_forumid);
    EXCEPTION WHEN unique_violation THEN
        update rsdn_moderate
        set crerate=i_crerate
        where messageid=i_messageid and topicid=i_topicid and userid=i_userid and forumid=i_forumid;
     return true;
  end;
  return false;
end;
$$;


ALTER FUNCTION public.update_rsdn_moderate(i_crerate timestamp with time zone, i_messageid bigint, i_topicid bigint, i_userid bigint, i_forumid bigint) OWNER TO rsdn;

--
-- TOC entry 183 (class 1255 OID 107113)
-- Dependencies: 5 524
-- Name: update_rsdn_rating(integer, integer, timestamp with time zone, bigint, bigint, bigint); Type: FUNCTION; Schema: public; Owner: rsdn
--

CREATE FUNCTION update_rsdn_rating(i_userrating integer, i_rate integer, i_ratedate timestamp with time zone, i_messageid bigint, i_topicid bigint, i_userid bigint) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
begin
  begin
    INSERT INTO rsdn_rating(userrating, rate, ratedate, messageid, topicid, userid)
    VALUES(i_userrating, i_rate, i_ratedate, i_messageid, i_topicid, i_userid);
    EXCEPTION WHEN unique_violation THEN
        update rsdn_rating
        set userrating=i_userrating, rate=i_rate, ratedate=i_ratedate
        where messageid=i_messageid and topicid=i_topicid and userid=i_userid;
     return true;
  end;
  return false;
end;
$$;


ALTER FUNCTION public.update_rsdn_rating(i_userrating integer, i_rate integer, i_ratedate timestamp with time zone, i_messageid bigint, i_topicid bigint, i_userid bigint) OWNER TO rsdn;

--
-- TOC entry 185 (class 1255 OID 88834)
-- Dependencies: 5 524
-- Name: update_rsdn_users(bigint, character varying, character varying, character varying, character varying, character varying, character varying, character varying, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION update_rsdn_users(i_id bigint, i_usernick character varying, i_username character varying, i_realname character varying, i_homepage character varying, i_wherefrom character varying, i_origin character varying, i_specialization character varying, i_userclass integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
begin
  begin
    INSERT INTO rsdn_users(usernick, username, realname, homepage, wherefrom, origin, id, confirmed, specialization, userclass)
    VALUES (i_usernick, i_username, i_realname, i_homepage, i_wherefrom, i_origin, i_id, false, i_specialization, i_userclass);
    EXCEPTION WHEN unique_violation THEN
        UPDATE rsdn_users
        SET usernick=i_usernick, username=i_username, realname=i_realname, homepage=i_homepage, wherefrom=i_wherefrom,
            origin=i_origin, specialization=i_specialization, userclass=i_userclass
        WHERE id=i_id;
     return true;
  end;
  return false;
end;
$$;


ALTER FUNCTION public.update_rsdn_users(i_id bigint, i_usernick character varying, i_username character varying, i_realname character varying, i_homepage character varying, i_wherefrom character varying, i_origin character varying, i_specialization character varying, i_userclass integer) OWNER TO postgres;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 165 (class 1259 OID 16613)
-- Dependencies: 2766 5
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
-- TOC entry 2803 (class 0 OID 0)
-- Dependencies: 164
-- Name: channels_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: rsdn
--

ALTER SEQUENCE channels_logs_id_seq OWNED BY channels_logs.id;


--
-- TOC entry 163 (class 1259 OID 16601)
-- Dependencies: 2764 5
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
-- TOC entry 2804 (class 0 OID 0)
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
    messageid bigint NOT NULL,
    topicid bigint NOT NULL,
    userid bigint NOT NULL,
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
-- Dependencies: 2762 5
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
-- TOC entry 2805 (class 0 OID 0)
-- Dependencies: 167
-- Name: rsdn_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: rsdn
--

ALTER SEQUENCE rsdn_users_id_seq OWNED BY rsdn_users.id;


--
-- TOC entry 2765 (class 2604 OID 16616)
-- Dependencies: 165 164 165
-- Name: id; Type: DEFAULT; Schema: public; Owner: rsdn
--

ALTER TABLE ONLY channels_logs ALTER COLUMN id SET DEFAULT nextval('channels_logs_id_seq'::regclass);


--
-- TOC entry 2763 (class 2604 OID 16604)
-- Dependencies: 163 162 163
-- Name: id; Type: DEFAULT; Schema: public; Owner: rsdn
--

ALTER TABLE ONLY nicknames ALTER COLUMN id SET DEFAULT nextval('nicknames_id_seq'::regclass);


--
-- TOC entry 2761 (class 2604 OID 16655)
-- Dependencies: 167 161
-- Name: id; Type: DEFAULT; Schema: public; Owner: rsdn
--

ALTER TABLE ONLY rsdn_users ALTER COLUMN id SET DEFAULT nextval('rsdn_users_id_seq'::regclass);


--
-- TOC entry 2780 (class 2606 OID 16622)
-- Dependencies: 165 165
-- Name: pkey_channels_logs; Type: CONSTRAINT; Schema: public; Owner: rsdn; Tablespace: 
--

ALTER TABLE ONLY channels_logs
    ADD CONSTRAINT pkey_channels_logs PRIMARY KEY (id);


--
-- TOC entry 2775 (class 2606 OID 20524)
-- Dependencies: 163 163
-- Name: pkey_nicknames; Type: CONSTRAINT; Schema: public; Owner: rsdn; Tablespace: 
--

ALTER TABLE ONLY nicknames
    ADD CONSTRAINT pkey_nicknames PRIMARY KEY (id);


--
-- TOC entry 2789 (class 2606 OID 16671)
-- Dependencies: 168 168
-- Name: pkey_rsdn_messages; Type: CONSTRAINT; Schema: public; Owner: rsdn; Tablespace: 
--

ALTER TABLE ONLY rsdn_messages
    ADD CONSTRAINT pkey_rsdn_messages PRIMARY KEY (id);


--
-- TOC entry 2796 (class 2606 OID 107115)
-- Dependencies: 170 170 170 170 170
-- Name: pkey_rsdn_moderate; Type: CONSTRAINT; Schema: public; Owner: rsdn; Tablespace: 
--

ALTER TABLE ONLY rsdn_moderate
    ADD CONSTRAINT pkey_rsdn_moderate PRIMARY KEY (messageid, topicid, userid, forumid);


--
-- TOC entry 2794 (class 2606 OID 107111)
-- Dependencies: 169 169 169 169
-- Name: pkey_rsdn_rating; Type: CONSTRAINT; Schema: public; Owner: rsdn; Tablespace: 
--

ALTER TABLE ONLY rsdn_rating
    ADD CONSTRAINT pkey_rsdn_rating PRIMARY KEY (messageid, topicid, userid);


--
-- TOC entry 2771 (class 2606 OID 16663)
-- Dependencies: 161 161
-- Name: pkey_rsdn_users; Type: CONSTRAINT; Schema: public; Owner: rsdn; Tablespace: 
--

ALTER TABLE ONLY rsdn_users
    ADD CONSTRAINT pkey_rsdn_users PRIMARY KEY (id);


--
-- TOC entry 2782 (class 2606 OID 16634)
-- Dependencies: 166 166
-- Name: pkey_rsdn_versions; Type: CONSTRAINT; Schema: public; Owner: rsdn; Tablespace: 
--

ALTER TABLE ONLY rsdn_row_versions
    ADD CONSTRAINT pkey_rsdn_versions PRIMARY KEY (name);


--
-- TOC entry 2776 (class 1259 OID 20520)
-- Dependencies: 165
-- Name: i_channels_logs_channel; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_channels_logs_channel ON channels_logs USING btree (channel);


--
-- TOC entry 2777 (class 1259 OID 107130)
-- Dependencies: 165
-- Name: i_channels_logs_datetime; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_channels_logs_datetime ON channels_logs USING btree (date_and_time);


--
-- TOC entry 2778 (class 1259 OID 20519)
-- Dependencies: 165
-- Name: i_channels_logs_nick; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_channels_logs_nick ON channels_logs USING btree (nickname_id);


--
-- TOC entry 2772 (class 1259 OID 20525)
-- Dependencies: 163
-- Name: i_nicknames_nickname; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_nicknames_nickname ON nicknames USING btree (nickname);


--
-- TOC entry 2773 (class 1259 OID 20526)
-- Dependencies: 163
-- Name: i_nicknames_rsdn; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_nicknames_rsdn ON nicknames USING btree (rsdn_user_id);


--
-- TOC entry 2783 (class 1259 OID 107126)
-- Dependencies: 168
-- Name: i_rsdn_messagedate; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_rsdn_messagedate ON rsdn_messages USING btree (messagedate);


--
-- TOC entry 2784 (class 1259 OID 107127)
-- Dependencies: 168
-- Name: i_rsdn_messages_forumid; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_rsdn_messages_forumid ON rsdn_messages USING btree (forumid);


--
-- TOC entry 2785 (class 1259 OID 107125)
-- Dependencies: 168
-- Name: i_rsdn_messages_id; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_rsdn_messages_id ON rsdn_messages USING btree (id);


--
-- TOC entry 2786 (class 1259 OID 20472)
-- Dependencies: 168
-- Name: i_rsdn_messages_parentid; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_rsdn_messages_parentid ON rsdn_messages USING btree (parentid);


--
-- TOC entry 2787 (class 1259 OID 20471)
-- Dependencies: 168
-- Name: i_rsdn_messages_userid; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_rsdn_messages_userid ON rsdn_messages USING btree (userid);


--
-- TOC entry 2790 (class 1259 OID 20479)
-- Dependencies: 169 169 169
-- Name: i_rsdn_rating_ids; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_rsdn_rating_ids ON rsdn_rating USING btree (messageid, topicid, userid);


--
-- TOC entry 2791 (class 1259 OID 61692)
-- Dependencies: 169
-- Name: i_rsdn_rating_messageid; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_rsdn_rating_messageid ON rsdn_rating USING btree (messageid);


--
-- TOC entry 2792 (class 1259 OID 61649)
-- Dependencies: 169
-- Name: i_rsdn_rating_userid; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_rsdn_rating_userid ON rsdn_rating USING btree (userid);


--
-- TOC entry 2767 (class 1259 OID 20505)
-- Dependencies: 161
-- Name: i_rsdn_users_realname; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_rsdn_users_realname ON rsdn_users USING btree (realname);


--
-- TOC entry 2768 (class 1259 OID 20503)
-- Dependencies: 161
-- Name: i_rsdn_users_username; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_rsdn_users_username ON rsdn_users USING btree (username);


--
-- TOC entry 2769 (class 1259 OID 20504)
-- Dependencies: 161
-- Name: i_rsdn_users_usernick; Type: INDEX; Schema: public; Owner: rsdn; Tablespace: 
--

CREATE INDEX i_rsdn_users_usernick ON rsdn_users USING btree (usernick);


--
-- TOC entry 2801 (class 0 OID 0)
-- Dependencies: 5
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


-- Completed on 2012-08-07 12:57:31 MSK

--
-- PostgreSQL database dump complete
--

