-- Table: analytics.sentiment_analysis

-- Stores sentiment analysis results of the news articles.

-- DROP TABLE IF EXISTS analytics.sentiment_analysis;

CREATE TABLE IF NOT EXISTS analytics.sentiment_analysis
(
    id serial NOT NULL,                             -- id
    source_id integer NOT NULL,                     -- id in table inputs.sentiment_sources
    sentiment_score real,                           -- -1: negative, 0: neutral, 1: positive
    score_confidence real,                          -- confidence score of the sentiment analysis model being right
    model_name text COLLATE pg_catalog."default",   -- model used to perform sentiment analysis
    analyzed_at timestamp without time zone,        -- time when the sentiment was analyzed
    CONSTRAINT sentiment_analysis_pkey PRIMARY KEY (id),
    CONSTRAINT fk_source FOREIGN KEY (source_id)
        REFERENCES inputs.sentiment_sources (content_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS analytics.sentiment_analysis
    OWNER to postgres;