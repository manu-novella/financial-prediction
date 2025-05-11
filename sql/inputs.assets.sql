-- Table: inputs.assets

-- DROP TABLE IF EXISTS inputs.assets;

CREATE TABLE IF NOT EXISTS inputs.assets
(
    id serial NOT NULL,
    ticker character varying(10) COLLATE pg_catalog."default" NOT NULL,
    name character varying(80) COLLATE pg_catalog."default" NOT NULL,
    pseudonym character varying(80) COLLATE pg_catalog."default",
    type character varying COLLATE pg_catalog."default",
    CONSTRAINT assets_pkey PRIMARY KEY (id),
    CONSTRAINT assets_ticker_key UNIQUE (ticker)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS inputs.assets
    OWNER to postgres;