import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
from transformers import pipeline
from datetime import datetime

from db import get_db_params


def get_sources():
    """Retrieve text sources from DB."""

    print("Extracting sources from database...")

    params = get_db_params()
    sources_tbl = params['sentiment_sources']
    companies_tbl = params['companies']
    db_conn_params = params['db_conn']

    select_query = f"""SELECT s.content_id, s.published_date, s.title, c.name
                        FROM {sources_tbl} s
                        LEFT JOIN {companies_tbl} c
                        ON s.ticker = c.ticker
                    """
    #TODO filter by published_date
    #TODO handle pseudonyms

    try:
        with psycopg2.connect(**db_conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(select_query)
                conn.commit()
                records = cur.fetchall()
    except psycopg2.Error as e:
        print(f"Database error: {e}")

    columns = ['content_id', 'published_date', 'title', 'name']
    sources_df = pd.DataFrame(records, columns=columns)

    return sources_df


def analyze_sentiment(analysis_df, analysis_timpestamp):
    """Analyze the sentiment of each text referring to an asset."""
    #TODO analyze based on each company, as there may be more than one in the same text

    print("Analyzing sentiment of sources...")

    model = 'ProsusAI/finbert'
    sentiment_model = pipeline('sentiment-analysis', model=model)
    
    texts = analysis_df['title']
    results = []
    for text in texts:
        res = sentiment_model(text)[0]
        results.append(res)

    sentiment_score = [1 if result['label'] == 'positive'
                       else -1 if result['label'] == 'negative'
                       else 0
                       for result in results]
    score_confidence = [result['score'] for result in results]

    analysis_df['sentiment_score'] = sentiment_score
    analysis_df['score_confidence'] = score_confidence
    analysis_df['model_name'] = model
    analysis_df['analyzed_at'] = analysis_timpestamp

    return analysis_df


def transform_data(df):
    """Transform raw DataFrame into list of tuples for insertion."""

    print("Preparing data to save...")

    rows = [
        (row['content_id'], row['sentiment_score'], row['score_confidence'], row['model_name'], row['analyzed_at'])
        for index, row in df.iterrows()
    ]

    return rows


def store_results(rows):
    """Insert rows into the database using bulk insert."""

    if not rows:
        print("No new data to insert.")
        return
    
    print('Loading extracted data into DB...')
    
    params = get_db_params()
    sentiment_analysis_tbl = params['sentiment_analysis']
    db_conn_params = params['db_conn']

    insert_query = f"""
        INSERT INTO {sentiment_analysis_tbl} (source_id, sentiment_score, score_confidence, model_name, analyzed_at)
        VALUES %s;
    """

    try:
        with psycopg2.connect(**db_conn_params) as conn:
            with conn.cursor() as cur:
                execute_values(cur, insert_query, rows)
                conn.commit()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return
        
    print(f"Insertion successful.")


def run_etl():
    start_time = datetime.now()
    print(f"Starting Sentiment Analysis ETL at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    #Extract
    sources_df = get_sources()

    #Transform
    analysis_df = analyze_sentiment(sources_df, start_time)
    rows = transform_data(analysis_df)

    #Load
    store_results(rows)

    print(f"ETL process finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    run_etl()