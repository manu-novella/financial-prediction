-- Table: modeling.feature_matrix

-- DROP TABLE IF EXISTS modeling.feature_matrix;

CREATE TABLE IF NOT EXISTS modeling.feature_matrix
(
    id serial NOT NULL,
    ticker character varying(20) COLLATE pg_catalog."default" NOT NULL,
    date date NOT NULL,
    price_id integer NOT NULL,
    sma_10 real,
    sma_20 real,
    ema_10 real,
    ema_20 real,
    rsi_14 real,
    daily_return real,
    volume_sma_10 real,
    sentiment_score real,
    sentiment_volume integer,
    next_day_return real,
    next_day_up boolean,
    CONSTRAINT feature_matrix_pkey PRIMARY KEY (id),
    CONSTRAINT feature_matrix_ticker_date_key UNIQUE (ticker, date),
    CONSTRAINT feature_matrix_price_id_fkey FOREIGN KEY (price_id)
        REFERENCES inputs.asset_prices (price_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS modeling.feature_matrix
    OWNER to postgres;