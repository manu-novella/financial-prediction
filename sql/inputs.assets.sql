-- Table: inputs.assets

-- Stores the fundamental data of assets this project works with.
-- Table used as a configuration table.

-- DROP TABLE IF EXISTS inputs.assets;

CREATE TABLE IF NOT EXISTS inputs.assets
(
    id serial NOT NULL,                                                     -- id
    ticker character varying(10) COLLATE pg_catalog."default" NOT NULL,     -- ticker string, e.g. 'MSFT'
    name character varying(80) COLLATE pg_catalog."default" NOT NULL,       -- name of the asset, e.g. 'Microsoft'
    pseudonym character varying(80) COLLATE pg_catalog."default",           -- non-official name of the asset
    type character varying COLLATE pg_catalog."default",                    -- type of asset: stock, bond, commodity, ETF, index...
    alphavantage_code character varying(40) COLLATE pg_catalog."default",   -- string id of asset in Alphavantage's API, e.g. 'SPY'
    CONSTRAINT assets_pkey PRIMARY KEY (id),
    CONSTRAINT assets_ticker_key UNIQUE (ticker)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS inputs.assets
    OWNER to postgres;