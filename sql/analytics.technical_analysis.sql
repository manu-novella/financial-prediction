-- Table: analytics.technical_analysis

-- DROP TABLE IF EXISTS analytics.technical_analysis;

CREATE TABLE IF NOT EXISTS analytics.technical_analysis
(
    id serial NOT NULL,
    asset_price_id integer NOT NULL,
    sma_10 real,
    sma_20 real,
    ema_10 real,
    ema_20 real,
    rsi_14 real,
    daily_return real,
    volume_sma_10 real,
    computed_at timestamp without time zone,
    CONSTRAINT technical_analysis_pkey PRIMARY KEY (id),
    CONSTRAINT technical_analysis_asset_price_id_key UNIQUE (asset_price_id),
    CONSTRAINT fk_asset_price_id FOREIGN KEY (asset_price_id)
        REFERENCES inputs.asset_prices (price_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS analytics.technical_analysis
    OWNER to postgres;