-- Table: inputs.sentiment_sources

-- DROP TABLE IF EXISTS inputs.sentiment_sources;

CREATE TABLE IF NOT EXISTS inputs.sentiment_sources
(
    content_id serial NOT NULL,
    source character varying(255) COLLATE pg_catalog."default",
    published_date date NOT NULL,
    title text COLLATE pg_catalog."default" NOT NULL,
    body text COLLATE pg_catalog."default",
    url text COLLATE pg_catalog."default" NOT NULL,
    scraped_at timestamp without time zone,
    ticker character varying(10) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT sentiment_sources_pkey PRIMARY KEY (content_id),
    CONSTRAINT sentiment_sources_title_published_date_ticker_key UNIQUE (title, published_date, ticker)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS inputs.sentiment_sources
    OWNER to postgres;