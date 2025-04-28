import yfinance as yf
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os


def get_db_params():
    """Loads parameters to acces DB."""

    load_dotenv()

    DB_PARAMS = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD")
    }

    DB_TABLE_NAME = os.getenv("ASSETS_PRICE_TABLE")

    return DB_PARAMS, DB_TABLE_NAME


def get_tickers():
    """Read from config assets to extract."""

    print('Reading assets whose data extract...')
    ticker_symbols = ["AAPL", "GOOG", "MSFT", "AMZN", "META"] #TODO read from config file
    return ticker_symbols


def get_extraction_period(): #Must return None if same-day data already extracted
    """Determine what from what period data must be extracted."""

    print('Determining period for data extraction...')
    period = '1d' #TODO read from config file
    return period


def extract_asset_price_data(ticker_symbols, period="1d"):
    """Download stock data for multiple tickers."""

    print('Downloading asset prices...')

    all_data = []

    for ticker in ticker_symbols:
        print(f"Fetching data for {ticker}...")
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            continue

        hist.reset_index(inplace=True)
        hist['ticker_symbol'] = ticker
        all_data.append(hist)

    if not all_data:
        return pd.DataFrame()
    
    combined_df = pd.concat(all_data, ignore_index=True)

    return combined_df


def transform_data(df):
    """Transform raw DataFrame into list of tuples for insertion."""

    print("Preparing data to save...")

    rows = [
        (row['ticker_symbol'], row['Date'].date(), row['Open'], row['Close'], row['High'], row['Low'], row['Volume'])
        for index, row in df.iterrows()
    ]

    return rows


def load_data(rows):
    """Insert rows into the database using bulk insert."""

    print('Loading extracted data into DB...')

    if not rows:
        print("No new data to insert.")
        return
    
    DB_PARAMS, DB_TABLE_NAME = get_db_params()

    insert_query = f"""
        INSERT INTO {DB_TABLE_NAME} (ticker_symbol, date, open, close, high, low, volume)
        VALUES %s
        ON CONFLICT (ticker_symbol, date) DO NOTHING;
    """

    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                execute_values(cur, insert_query, rows)
                conn.commit()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return
        
    print(f"Insertion successful.")


def run_etl():
    print(f"Starting ETL process at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    #Extract
    tickers = get_tickers()
    period = get_extraction_period()

    if period is None:
        print("Daily data already extracted. Exiting.")
        return

    asset_data = extract_asset_price_data(tickers, period=period)

    if asset_data.empty:
        print("No asset data fetched. Exiting.")
        return

    #Transform
    rows = transform_data(asset_data)

    #Load
    load_data(rows)

    print(f"ETL process finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    run_etl()