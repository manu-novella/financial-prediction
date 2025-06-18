import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

from db import get_db_params


def get_data() -> dict:
    '''Retrieve prices, technical analysis metrics and sentiment data.'''

    print('Extracting prices, metrics and sentiment data from database...')

    params =                    get_db_params()
    asset_price_tbl =           params['assets_price']
    technical_analysis_tbl =    params['technical_analysis']
    sentiment_analysis_tbl =    params['sentiment_analysis']
    sentiment_sources_tbl =     params['sentiment_sources']
    db_conn_params =            params['db_conn']

    prices_columns = ['a.price_id', 'a.ticker', 'a.date', 'a.open', 'a.close', 'a.high', 'a.low', 'a.volume',
                      't.sma_10', 't.sma_20', 't.ema_10', 't.ema_20', 't.rsi_14', 't.daily_return', 't.volume_sma_10'
    ]
    sentiment_columns = ['a.source_id', 'a.sentiment_score', 'a.score_confidence', 's.published_date', 's.ticker']

    prices_query = f'''SELECT {", ".join(prices_columns)}
                        FROM {asset_price_tbl} a
                        LEFT JOIN {technical_analysis_tbl} t
                        ON a.price_id = t.asset_price_id
                        WHERE a.ticker = 'SPY'
                        AND t.asset_price_id IS NOT NULL; --technical metrics have been computed
    '''
    sentiment_query = f'''SELECT {", ".join(sentiment_columns)}
                            FROM {sentiment_analysis_tbl} a
                            LEFT JOIN {sentiment_sources_tbl} s
                            ON a.source_id = s.content_id
                            WHERE a.analyzed_at = (
                                SELECT MAX(analyzed_at)
                                FROM analytics.sentiment_analysis
                            )
                            AND s.ticker = 'SPY';
    '''
    
    try:
        with psycopg2.connect(**db_conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(prices_query)
                conn.commit()
                prices = cur.fetchall()

                cur.execute(sentiment_query)
                conn.commit()
                sentiments = cur.fetchall()
    except psycopg2.Error as e:
        print(f'Database error: {e}')

    prices_df = pd.DataFrame(prices, columns=prices_columns)
    sentiments_df = pd.DataFrame(sentiments, columns=sentiment_columns)

    joined_data = {'prices': prices_df,
                   'sentiments': sentiments_df
    }

    return joined_data


def compute_final_matrix(data: dict) -> pd.DataFrame:
    '''Compute aggregated sentiment score along with target columns for model training.'''

    print('Computing final matrix...')

    prices_df = data['prices']
    sentiments_df = data['sentiments']

    #Remove rows where the sentiment analysis confidence is not high enough
    sentiments_df = sentiments_df[sentiments_df['a.score_confidence'] >= 0.8]

    #Compute the average sentiment score
    sentiments_agg = sentiments_df.groupby(['s.ticker', 's.published_date']).agg(
        sentiment_score=('a.sentiment_score', 'mean')
    ).reset_index()
    sentiments_df = sentiments_df.merge(sentiments_agg, on=['s.ticker', 's.published_date'], how='left')

    #Join prices and sentiments
    prices_df = prices_df.merge(sentiments_df,
                                left_on=['a.ticker', 'a.date'],
                                right_on=['s.ticker', 's.published_date'],
                                how='left')
    
    #Where there was no sentiment reported, assume neutrality
    prices_df['sentiment_score'] = prices_df['sentiment_score'].fillna(0)
    
    #Drop unnecessary columns that may cause confusion
    columns_to_drop = ['a.source_id', 'a.sentiment_score', 'a.score_confidence', 's.published_date', 's.ticker']
    prices_df = prices_df.drop(columns_to_drop, axis=1)

    #Compute target columns
    prices_df['next_close'] = prices_df.groupby('a.ticker')['a.close'].shift(-1)
    prices_df['next_day_return'] = (prices_df['next_close'] - prices_df['a.close']) / prices_df['a.close']
    prices_df['next_day_up'] = prices_df['next_day_return'] > 0

    #Drop latest row of each ticker group as it contains nulls in target colums
    prices_df = prices_df.dropna(subset=['next_day_return'])

    return prices_df


def transform_data(df: pd.DataFrame) -> list:
    '''Transform raw DataFrame into list of tuples for insertion.'''

    print('Preparing data to save...')

    rows = [
        (row['a.ticker'], row['a.date'], row['a.price_id'], row['t.sma_10'], row['t.sma_20'], row['t.ema_10'],
         row['t.ema_20'], row['t.rsi_14'], row['t.daily_return'], row['t.volume_sma_10'], row['sentiment_score'],
         row['next_day_return'], row['next_day_up']
    )
        for index, row in df.iterrows()
    ]

    return rows


def store_results(rows: list):
    '''Insert rows into the database using bulk insert.'''

    if not rows:
        print('No new data to insert.')
        return
    
    print('Loading feature matrix into database...')
    
    params = get_db_params()
    feature_matrix_tbl = params['feature_matrix']
    db_conn_params = params['db_conn']

    insert_query = f'''INSERT INTO {feature_matrix_tbl}
                        (ticker, date, price_id, sma_10, sma_20, ema_10, ema_20, rsi_14, daily_return,
                        volume_sma_10, sentiment_score, next_day_return, next_day_up)
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
    start_time = datetime.now()
    print(f'Starting Feature Matrix Build at {start_time.strftime('%Y-%m-%d %H:%M:%S')}')

    #Extract
    base_data = get_data()

    #Transform
    matrix = compute_final_matrix(base_data)
    rows = transform_data(matrix)

    #Load
    store_results(rows)

    print(f'Feature Matrix Build finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}')


if __name__ == '__main__':
    run_etl()