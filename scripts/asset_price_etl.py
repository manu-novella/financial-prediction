import yfinance as yf
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os
import requests
from io import StringIO

from db import get_db_params



def get_tickers():
    '''Read from DB assets to extract.'''

    print('Reading assets whose data extract...')

    params = get_db_params()
    assets_tbl = params['assets']
    db_conn_params = params['db_conn']

    select_query = f'''SELECT ticker FROM {assets_tbl}
                        WHERE alphavantage_code IS NOT NULL --#!TODO rethink
                    '''

    try:
        with psycopg2.connect(**db_conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(select_query)
                conn.commit()
                records = cur.fetchall()
    except psycopg2.Error as e:
        print(f'Database error: {e}')

    tickers = []
    for record in records:
        tickers.append(record[0])
    
    return tickers


def get_extraction_period(): #Must return None if same-day data already extracted
    '''Determine from what period data must be extracted.'''

    print('Determining period for data extraction...')

    period = '1d' #TODO read from config file and pass as parameter

    return period


def extract_asset_price_data(tickers, period='1d'):
    '''Download stock data for multiple tickers.'''

    print('Downloading asset prices...')

    all_data = []

    #session = requests.Session(impersonate='chrome') #Bypass yfinance block

    load_dotenv()
    api_key = os.getenv('ALPHAVANTAGE_API_KEY')

    for ticker in tickers:
        print(f'Fetching data for {ticker}...')
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&datatype=csv&apikey={api_key}'
        req = requests.get(url)

        if req.status_code != 200:
            print(f"Couldn't retrieve data for ticker {ticker}")
            continue

        df = pd.read_csv(StringIO(req.text))
        df.reset_index(inplace=True)
        df['ticker'] = ticker
        all_data.append(df)

    if not all_data:
        return pd.DataFrame()
    
    combined_df = pd.concat(all_data, ignore_index=True)

    return combined_df


def transform_data(df):
    '''Transform raw DataFrame into list of tuples for insertion.'''

    print('Preparing data to save...')

    rows = [
        (row['ticker'], row['timestamp'], row['open'], row['close'], row['high'], row['low'], row['volume'])
        for index, row in df.iterrows()
    ]

    return rows


def load_data(rows):
    '''Insert rows into the database using bulk insert.'''

    if not rows:
        print('No new data to insert.')
        return
    
    print('Loading extracted prices into database...')
    
    params = get_db_params()
    assets_price_tbl = params['assets_price']
    db_conn_params = params['db_conn']

    insert_query = f'''INSERT INTO {assets_price_tbl} (ticker, date, open, close, high, low, volume)
                        VALUES %s
                        ON CONFLICT (ticker, date) DO NOTHING;
    '''

    try:
        with psycopg2.connect(**db_conn_params) as conn:
            with conn.cursor() as cur:
                execute_values(cur, insert_query, rows)
                conn.commit()
    except psycopg2.Error as e:
        print(f'Database error: {e}')
        return
        
    print(f'Insertion successful.')


def run_etl():
    print(f'Starting Asset Price ETL at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')

    #Extract
    period = get_extraction_period()

    if period is None:
        print('Daily data already extracted. Exiting.')
        return
    
    tickers = get_tickers()
    asset_data = extract_asset_price_data(tickers, period=period)

    if asset_data.empty:
        print('No asset data fetched. Exiting.')
        return

    #Transform
    rows = transform_data(asset_data)

    #Load
    load_data(rows)

    print(f'ETL process finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')



if __name__ == '__main__':
    run_etl()