-- Table: modeling.feature_matrix

-- 

-- DROP TABLE IF EXISTS modeling.feature_matrix;

CREATE TABLE IF NOT EXISTS modeling.feature_matrix
(
    id serial NOT NULL,                                                 -- id
    ticker character varying(20) COLLATE pg_catalog."default" NOT NULL, -- ticker string, e.g. 'MSFT'
    date date NOT NULL,                                                 -- date of the price of the asset
    price_id integer NOT NULL,                                          -- id in table inputs.asset_prices from which the metrics are calculated
    sma_10 real,                                                        -- simple moving average of price of 10 past data points
    sma_20 real,                                                        -- simple moving average of price of 20 past data points
    ema_10 real,                                                        -- exponential moving average of price of 10 past data points
    ema_20 real,                                                        -- exponential moving average of price of 20 past data points
    rsi_14 real,                                                        -- relative strength index of 14 past data points
    daily_return real,                                                  -- percentage change in asset price
    volume_sma_10 real,                                                 -- simple moving average of trading volume of 10 past data points
    sentiment_score real,                                               -- average sentiment score of news on this day and whose confidence scores are high
    next_day_return real,                                               -- percentage variation of price at the end of the day (close)
    next_day_up boolean,                                                -- whether there was an increase in price the next day
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