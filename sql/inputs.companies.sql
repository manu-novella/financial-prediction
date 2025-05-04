-- Table: inputs.companies

-- DROP TABLE IF EXISTS inputs.companies;

CREATE TABLE IF NOT EXISTS inputs.companies
(
    id serial NOT NULL,
    ticker character varying(10) COLLATE pg_catalog."default" NOT NULL,
    name character varying(80) COLLATE pg_catalog."default" NOT NULL,
    pseudonym character varying(80) COLLATE pg_catalog."default",
    CONSTRAINT companies_pkey PRIMARY KEY (id),
    CONSTRAINT companies_ticker_key UNIQUE (ticker)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS inputs.companies
    OWNER to postgres;