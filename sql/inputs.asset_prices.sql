-- Table: inputs.asset_prices

-- Stores the historical trading price of the assets.

-- DROP TABLE IF EXISTS inputs.asset_prices;

CREATE TABLE IF NOT EXISTS inputs.asset_prices
(
    price_id serial NOT NULL,                                           -- id
    ticker character varying(20) COLLATE pg_catalog."default" NOT NULL, -- ticker string, e.g. 'MSFT'
    date date NOT NULL,                                                 -- date of the price of the asset
    open numeric(20,6),                                                 -- price of the asset at the start of the trading day
    close numeric(20,6),                                                -- price of the asset at the end of the trading day
    high numeric(20,6),                                                 -- max price of the asset during the trading day
    low numeric(20,6),                                                  -- min price of the asset during the trading day
    volume bigint,                                                      -- trading volume
    CONSTRAINT asset_prices_pkey PRIMARY KEY (price_id),
    CONSTRAINT asset_prices_ticker_date_key UNIQUE (ticker, date)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS inputs.asset_prices
    OWNER to postgres;