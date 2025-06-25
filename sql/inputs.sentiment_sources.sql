-- Table: inputs.sentiment_sources

-- Stores financial news articles of assets of interest.

-- DROP TABLE IF EXISTS inputs.sentiment_sources;

CREATE TABLE IF NOT EXISTS inputs.sentiment_sources
(
    content_id serial NOT NULL,                                         -- id
    source character varying(255) COLLATE pg_catalog."default",         -- source of the retrieved news, e.g. 'Yahoo Finance'
    published_date date NOT NULL,                                       -- publishing date of the news
    title text COLLATE pg_catalog."default" NOT NULL,                   -- title of the news article
    body text COLLATE pg_catalog."default",                             -- body of the news article
    url text COLLATE pg_catalog."default" NOT NULL,                     -- URL of the article
    scraped_at timestamp without time zone,                             -- time when the article was retrieved
    ticker character varying(10) COLLATE pg_catalog."default" NOT NULL, -- ticker string the article talks about, e.g. 'MSFT'
    CONSTRAINT sentiment_sources_pkey PRIMARY KEY (content_id),
    CONSTRAINT sentiment_sources_title_published_date_ticker_key UNIQUE (title, published_date, ticker)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS inputs.sentiment_sources
    OWNER to postgres;