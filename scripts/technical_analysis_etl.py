import pandas as pd
import pandas_ta as ta
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

from db import get_db_params


def get_asset_data() -> pd.DataFrame:
    '''Retrieve asset trading data from DB.'''

    print('Extracting asset data from database...')

    params =            get_db_params()
    asset_price_tbl =   params['assets_price']
    db_conn_params =    params['db_conn']

    columns = ['price_id', 'ticker', 'date', 'open', 'close', 'high', 'low', 'volume']

    select_query = f'''SELECT {", ".join(columns)}
                        FROM {asset_price_tbl}
                        WHERE ticker = 'SPY'
                    '''
    
    try:
        with psycopg2.connect(**db_conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(select_query)
                conn.commit()
                records = cur.fetchall()
    except psycopg2.Error as e:
        print(f'Database error: {e}')

    asset_prices_df = pd.DataFrame(records, columns=columns)

    return asset_prices_df


def compute_ta_metrics(asset_df: pd.DataFrame, start_time: datetime) -> pd.DataFrame:
    '''Compute technical analysis metrics on past data.'''

    print('Computing technical analysis metrics...')

    computed_rows = []

    for ticker, group in asset_df.groupby('ticker'):
        group = group.sort_values('date').copy()
        
        group['sma_10'] =           group['close'].rolling(10).mean()
        group['sma_20'] =           group['close'].rolling(20).mean()
        group['ema_10'] =           group['close'].ewm(span=10).mean()
        group['ema_20'] =           group['close'].ewm(span=20).mean()
        group['rsi_14'] =           ta.rsi(group['close'], length=14)
        group['daily_return'] =     group['close'].pct_change()
        group['volume_sma_10'] =    group['volume'].rolling(10).mean()

        #Collect id and metrics
        for _, row in group.dropna().iterrows():
            computed_rows.append([
                row['price_id'],
                row['sma_10'],
                row['sma_20'],
                row['ema_10'],
                row['ema_20'],
                row['rsi_14'],
                row['daily_return'],
                row['volume_sma_10'],
                start_time
            ])

    columns = ['asset_price_id', 'sma_10', 'sma_20', 'ema_10', 'ema_20', 
               'rsi_14', 'daily_return', 'volume_sma_10', 'computed_at']
    metrics_df = pd.DataFrame(computed_rows, columns=columns)

    return metrics_df


def transform_data(df: pd.DataFrame) -> list:
    '''Transform raw DataFrame into list of tuples for insertion.'''

    print('Preparing data to save...')

    rows = [
        (
            row['asset_price_id'], row['sma_10'], row['sma_20'],
            row['ema_10'], row['ema_20'], row['rsi_14'],
            row['daily_return'], row['volume_sma_10'], row['computed_at']
        )
        for index, row in df.iterrows()
    ]

    return rows


def store_results(rows: list):
    '''Insert rows into the database using bulk insert.'''

    if not rows:
        print('No new data to insert.')
        return
    
    print('Loading technical analysis results into database...')
    
    params =                    get_db_params()
    technical_analysis_tbl =    params['technical_analysis']
    db_conn_params =            params['db_conn']

    insert_query = f'''INSERT INTO {technical_analysis_tbl} (
                        asset_price_id, sma_10, sma_20, ema_10, ema_20,
                        rsi_14, daily_return, volume_sma_10, computed_at
                        )
                        VALUES %s
                        ON CONFLICT (asset_price_id) DO NOTHING;
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


def run_technical_analysis_etl():
    start_time = datetime.now()
    print(f'Starting Technical Analysis ETL at {start_time.strftime("%Y-%m-%d %H:%M:%S")}')

    #Extract
    asset_df = get_asset_data()

    #Transform
    metrics_df = compute_ta_metrics(asset_df, start_time)
    rows = transform_data(metrics_df)

    #Load
    store_results(rows)

    print(f'ETL process finished at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')


if __name__ == '__main__':
    run_technical_analysis_etl()