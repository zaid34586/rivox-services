--
-- PostgreSQL database dump
--

\restrict NgOes94h0xOvVQ1GIvvNbjb6chpD5YzxeW2EWt8PVaBRtp0qFT2FnK2Rfv4WS9W

-- Dumped from database version 18.6 (Ubuntu 18.6-0ubuntu0.26.04.1)
-- Dumped by pg_dump version 18.6 (Ubuntu 18.6-0ubuntu0.26.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: bookings; Type: TABLE; Schema: public; Owner: agency_user
--

CREATE TABLE public.bookings (
    id character varying(50) NOT NULL,
    customer_phone character varying(50),
    customer_name character varying(100),
    customer_mobile character varying(50),
    booking_date date,
    time_start time without time zone,
    time_end time without time zone,
    guests integer,
    status character varying(20) DEFAULT 'confirmed'::character varying,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.bookings OWNER TO agency_user;

--
-- Name: orders; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.orders (
    id character varying(50) NOT NULL,
    business_id character varying(50) NOT NULL,
    customer_phone character varying(50) NOT NULL,
    order_type character varying(20) NOT NULL,
    table_number integer,
    items jsonb NOT NULL,
    subtotal numeric(10,2) NOT NULL,
    tax numeric(10,2) NOT NULL,
    total numeric(10,2) NOT NULL,
    status character varying(20) DEFAULT 'confirmed'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.orders OWNER TO postgres;

--
-- Name: party_bookings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.party_bookings (
    id character varying(50) NOT NULL,
    business_id character varying(50) NOT NULL,
    customer_phone character varying(50) NOT NULL,
    occasion character varying(100),
    booking_date date,
    package_name character varying(100),
    guest_count integer,
    customer_name character varying(100),
    customer_mobile character varying(50),
    customer_email character varying(150),
    total_price numeric(10,2),
    status character varying(20) DEFAULT 'confirmed'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.party_bookings OWNER TO postgres;

--
-- Name: bookings bookings_pkey; Type: CONSTRAINT; Schema: public; Owner: agency_user
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_pkey PRIMARY KEY (id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: party_bookings party_bookings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.party_bookings
    ADD CONSTRAINT party_bookings_pkey PRIMARY KEY (id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT ALL ON SCHEMA public TO agency_user;


--
-- Name: TABLE orders; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.orders TO agency_user;


--
-- Name: TABLE party_bookings; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.party_bookings TO agency_user;


--
-- PostgreSQL database dump complete
--

\unrestrict NgOes94h0xOvVQ1GIvvNbjb6chpD5YzxeW2EWt8PVaBRtp0qFT2FnK2Rfv4WS9W

