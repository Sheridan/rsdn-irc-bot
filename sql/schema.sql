SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
CREATE DATABASE "rsdn-irc-bot" WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'ru_RU.UTF-8' LC_CTYPE = 'ru_RU.UTF-8';
ALTER DATABASE "rsdn-irc-bot" OWNER TO rsdn;
\connect "rsdn-irc-bot"
SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;
COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';
SET search_path = public, pg_catalog;
CREATE FUNCTION update_rsdn_messages(i_id integer, i_topicid integer, i_parentid integer, i_userid integer, i_forumid integer, i_subject character varying, i_messagename character varying, i_message text, i_articleid integer, i_messagedate timestamp with time zone, i_updatedate timestamp with time zone, i_userrole character varying, i_usertitle character varying, i_lastmoderated timestamp with time zone, i_closed boolean) RETURNS boolean
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
ALTER FUNCTION public.update_rsdn_messages(i_id integer, i_topicid integer, i_parentid integer, i_userid integer, i_forumid integer, i_subject character varying, i_messagename character varying, i_message text, i_articleid integer, i_messagedate timestamp with time zone, i_updatedate timestamp with time zone, i_userrole character varying, i_usertitle character varying, i_lastmoderated timestamp with time zone, i_closed boolean) OWNER TO rsdn;
CREATE FUNCTION update_rsdn_moderate(i_crerate timestamp with time zone, i_messageid integer, i_topicid integer, i_userid integer, i_forumid integer) RETURNS boolean
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
ALTER FUNCTION public.update_rsdn_moderate(i_crerate timestamp with time zone, i_messageid integer, i_topicid integer, i_userid integer, i_forumid integer) OWNER TO rsdn;
CREATE FUNCTION update_rsdn_rating(i_userrating integer, i_rate integer, i_ratedate timestamp with time zone, i_messageid integer, i_topicid integer, i_userid integer) RETURNS boolean
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
ALTER FUNCTION public.update_rsdn_rating(i_userrating integer, i_rate integer, i_ratedate timestamp with time zone, i_messageid integer, i_topicid integer, i_userid integer) OWNER TO rsdn;
CREATE FUNCTION update_rsdn_users(i_id integer, i_usernick character varying, i_username character varying, i_realname character varying, i_homepage character varying, i_wherefrom character varying, i_origin character varying, i_specialization character varying, i_userclass integer) RETURNS boolean
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
ALTER FUNCTION public.update_rsdn_users(i_id integer, i_usernick character varying, i_username character varying, i_realname character varying, i_homepage character varying, i_wherefrom character varying, i_origin character varying, i_specialization character varying, i_userclass integer) OWNER TO postgres;
SET default_tablespace = '';
SET default_with_oids = false;
CREATE TABLE channels_logs (
    id integer NOT NULL,
    nickname_id integer NOT NULL,
    date_and_time timestamp without time zone DEFAULT now() NOT NULL,
    message text,
    channel character varying(128) NOT NULL,
    is_bot_command boolean
);
ALTER TABLE public.channels_logs OWNER TO rsdn;
CREATE SEQUENCE channels_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE public.channels_logs_id_seq OWNER TO rsdn;
ALTER SEQUENCE channels_logs_id_seq OWNED BY channels_logs.id;
CREATE TABLE nicknames (
    id integer NOT NULL,
    nickname character varying(128) NOT NULL,
    rsdn_user_id bigint DEFAULT 0 NOT NULL,
    last_seen timestamp with time zone
);
ALTER TABLE public.nicknames OWNER TO rsdn;
CREATE SEQUENCE nicknames_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE public.nicknames_id_seq OWNER TO rsdn;
ALTER SEQUENCE nicknames_id_seq OWNED BY nicknames.id;
CREATE TABLE rsdn_messages (
    id integer NOT NULL,
    topicid integer NOT NULL,
    parentid integer NOT NULL,
    userid integer NOT NULL,
    forumid integer NOT NULL,
    subject character varying(256),
    messagename character varying(256),
    message text,
    articleid integer NOT NULL,
    messagedate timestamp with time zone,
    updatedate timestamp with time zone,
    userrole character varying(32),
    usertitle character varying(64),
    lastmoderated timestamp with time zone,
    closed boolean
);
ALTER TABLE public.rsdn_messages OWNER TO rsdn;
CREATE TABLE rsdn_moderate (
    messageid integer NOT NULL,
    topicid integer NOT NULL,
    userid integer NOT NULL,
    forumid integer NOT NULL,
    crerate timestamp with time zone
);
ALTER TABLE public.rsdn_moderate OWNER TO rsdn;
CREATE TABLE rsdn_rating (
    messageid integer NOT NULL,
    topicid integer NOT NULL,
    userid integer NOT NULL,
    userrating integer,
    rate integer,
    ratedate timestamp with time zone
);
ALTER TABLE public.rsdn_rating OWNER TO rsdn;
CREATE TABLE rsdn_row_versions (
    name character varying(128) NOT NULL,
    value text
);
ALTER TABLE public.rsdn_row_versions OWNER TO rsdn;
CREATE TABLE rsdn_users (
    usernick character varying(128),
    username character varying(128),
    realname character varying(128),
    homepage character varying(1024),
    wherefrom character varying(256),
    origin character varying(1024),
    id integer NOT NULL,
    confirmed boolean DEFAULT false NOT NULL,
    specialization character varying(1024),
    userclass smallint
);
ALTER TABLE public.rsdn_users OWNER TO rsdn;
CREATE SEQUENCE rsdn_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE public.rsdn_users_id_seq OWNER TO rsdn;
ALTER SEQUENCE rsdn_users_id_seq OWNED BY rsdn_users.id;
ALTER TABLE ONLY channels_logs ALTER COLUMN id SET DEFAULT nextval('channels_logs_id_seq'::regclass);
ALTER TABLE ONLY nicknames ALTER COLUMN id SET DEFAULT nextval('nicknames_id_seq'::regclass);
ALTER TABLE ONLY rsdn_users ALTER COLUMN id SET DEFAULT nextval('rsdn_users_id_seq'::regclass);
ALTER TABLE ONLY channels_logs
    ADD CONSTRAINT pkey_channels_logs PRIMARY KEY (id);
ALTER TABLE ONLY nicknames
    ADD CONSTRAINT pkey_nicknames PRIMARY KEY (id);
ALTER TABLE ONLY rsdn_messages
    ADD CONSTRAINT pkey_rsdn_messages PRIMARY KEY (id);
ALTER TABLE ONLY rsdn_moderate
    ADD CONSTRAINT pkey_rsdn_moderate PRIMARY KEY (messageid, topicid, userid, forumid);
ALTER TABLE ONLY rsdn_rating
    ADD CONSTRAINT pkey_rsdn_rating PRIMARY KEY (messageid, topicid, userid);
ALTER TABLE ONLY rsdn_users
    ADD CONSTRAINT pkey_rsdn_users PRIMARY KEY (id);
ALTER TABLE ONLY rsdn_row_versions
    ADD CONSTRAINT pkey_rsdn_versions PRIMARY KEY (name);
CREATE INDEX i_channels_logs_channel ON channels_logs USING btree (channel);
CREATE INDEX i_channels_logs_datetime ON channels_logs USING btree (date_and_time);
CREATE INDEX i_channels_logs_nick ON channels_logs USING btree (nickname_id);
CREATE INDEX i_nicknames_nickname ON nicknames USING btree (nickname);
CREATE INDEX i_nicknames_rsdn ON nicknames USING btree (rsdn_user_id);
CREATE INDEX i_rsdn_messagedate ON rsdn_messages USING btree (messagedate);
CREATE INDEX i_rsdn_messages_forumid ON rsdn_messages USING btree (forumid);
CREATE INDEX i_rsdn_messages_parentid ON rsdn_messages USING btree (parentid);
CREATE INDEX i_rsdn_messages_topicid ON rsdn_messages USING btree (topicid);
CREATE INDEX i_rsdn_messages_userid ON rsdn_messages USING btree (userid);
CREATE INDEX i_rsdn_rating_ids ON rsdn_rating USING btree (messageid, topicid, userid);
CREATE INDEX i_rsdn_rating_messageid ON rsdn_rating USING btree (messageid);
CREATE INDEX i_rsdn_rating_userid ON rsdn_rating USING btree (userid);
CREATE INDEX i_rsdn_users_realname ON rsdn_users USING btree (realname);
CREATE INDEX i_rsdn_users_username ON rsdn_users USING btree (username);
CREATE INDEX i_rsdn_users_usernick ON rsdn_users USING btree (usernick);
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;
