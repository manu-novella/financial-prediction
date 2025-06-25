-- Table: analytics.technical_analysis

-- Stores technical analysis metrics of the asset prices. Metrics are calculated with the closing price.

-- DROP TABLE IF EXISTS analytics.technical_analysis;

CREATE TABLE IF NOT EXISTS analytics.technical_analysis
(
    id serial NOT NULL,                         -- id
    asset_price_id integer NOT NULL,            -- id in table inputs.asset_prices from which the metrics are calculated
    sma_10 real,                                -- simple moving average of price of 10 past data points
    sma_20 real,                                -- simple moving average of price of 20 past data points
    ema_10 real,                                -- exponential moving average of price of 10 past data points
    ema_20 real,                                -- exponential moving average of price of 20 past data points
    rsi_14 real,                                -- relative strength index of 14 past data points
    daily_return real,                          -- percentage change in asset price
    volume_sma_10 real,                         -- simple moving average of trading volume of 10 past data points
    computed_at timestamp without time zone,    -- time when the metric was computed
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