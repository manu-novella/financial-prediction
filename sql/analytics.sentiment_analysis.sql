-- Table: analytics.sentiment_analysis

-- DROP TABLE IF EXISTS analytics.sentiment_analysis;

CREATE TABLE IF NOT EXISTS analytics.sentiment_analysis
(
    id serial NOT NULL,
    source_id integer NOT NULL,
    sentiment_score real,
    score_confidence real,
    model_name text COLLATE pg_catalog."default",
    analyzed_at timestamp without time zone,
    CONSTRAINT sentiment_analysis_pkey PRIMARY KEY (id),
    CONSTRAINT fk_source FOREIGN KEY (source_id)
        REFERENCES inputs.sentiment_sources (content_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS analytics.sentiment_analysis
    OWNER to postgres;