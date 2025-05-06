-- Table: inputs.asset_prices

-- DROP TABLE IF EXISTS inputs.asset_prices;

CREATE TABLE IF NOT EXISTS inputs.asset_prices
(
    price_id serial NOT NULL,
    ticker character varying(20) COLLATE pg_catalog."default" NOT NULL,
    date date NOT NULL,
    open numeric(20,6),
    close numeric(20,6),
    high numeric(20,6),
    low numeric(20,6),
    volume bigint,
    CONSTRAINT asset_prices_pkey PRIMARY KEY (price_id),
    CONSTRAINT asset_prices_ticker_date_key UNIQUE (ticker, date)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS inputs.asset_prices
    OWNER to postgres;