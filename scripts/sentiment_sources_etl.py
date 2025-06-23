import feedparser
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import spacy
import pandas as pd
import re
from rapidfuzz import process, fuzz
from collections.abc import KeysView

from db import get_db_params


def fetch_rss_news(url: str) -> list:
    '''Fetch news articles from an RSS feed.'''

    print('Fetching RSS news...')

    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries:
        articles.append({
            'title': entry.title,
            'link': entry.link,
            'published': entry.published,
            'summary': entry.summary if 'summary' in entry else ''
        })

    return articles


def build_org_ticker_dict() -> dict:
    '''Read companies data from DB and build a dictionary to map their tickers.'''

    print('Extracting relevant companies from database...')

    params =            get_db_params()
    assets_tbl =        params['assets']
    db_conn_params =    params['db_conn']

    select_query = f'''SELECT name, pseudonym, ticker FROM {assets_tbl}
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

    org_to_ticker = {}

    for record in records:
        org_to_ticker[record[0]] = record[2]
        if record[1] is not None: #If company has pseudonym
            org_to_ticker[record[1]] = record[2]

    return org_to_ticker


def clean_org_name(name: str) -> str:
    '''Strip non-specifying words from company name.'''

    return re.sub(r'\b(Inc|Incorporated|Corp|Corporation|Ltd|LLC|Motors)\b|\.', '', name, flags=re.IGNORECASE).strip()


def extract_orgs(text: str, relevant_orgs: KeysView, nlp_model: object) -> list:
    '''Helper function to extract organization names from scraped news.'''
    
    #Use of spaCy pretrained model for more potential finds
    doc = nlp_model(text)
    orgs = [clean_org_name(ent.text) for ent in doc.ents if ent.label_ == "ORG"]
    
    for org in relevant_orgs:
        if org.lower() in text.lower():
            orgs.append(org)

    return orgs


def fuzzy_match_org(org: str, relevant_orgs: KeysView, threshold: int =85) -> str:
    '''Match org string scraped from text with set of orgs in DB.'''
    
    match, score, _ = process.extractOne(org.title(), relevant_orgs, scorer=fuzz.token_sort_ratio, processor=str.lower)
    if score >= threshold:
        return match


def build_asset_mentions_df(articles: list, ticker_dict: dict, nlp_model: object, url: str, scraping_timestamp: datetime) -> pd.DataFrame:
    '''Iterate the scraped articles and return data about the relevant mentioned assets.'''

    print('Extracting mentions of assets in news...')

    columns = ['source', 'published_date', 'title', 'body', 'url', 'scraped_at', 'ticker']
    sentiment_sources = pd.DataFrame(columns=columns)
    
    for article in articles:
        title = article['title']
        body = article['summary'] #TODO extract true body via link
        orgs = set(extract_orgs(title, ticker_dict.keys(), nlp_model) 
                   + extract_orgs(body, ticker_dict.keys(), nlp_model)
                )
        
        for org in orgs:
            match = fuzzy_match_org(org, ticker_dict.keys())
            if match is not None:
                new_row = ['Yahoo Finance', #TODO parameterize
                           datetime.strptime(article['published'], '%a, %d %b %Y %H:%M:%S %z').date(),
                           title,
                           body, #TODO extract true body via link
                           url,
                           scraping_timestamp,
                           ticker_dict[match]
                ]
                sentiment_sources.loc[len(sentiment_sources)] = new_row

    return sentiment_sources


def transform_data(df: pd.DataFrame) -> list:
    '''Transform raw DataFrame into list of tuples for insertion.'''

    print('Preparing data to save...')

    rows = [
        (row['source'], row['published_date'], row['title'], row['body'], row['url'], row['scraped_at'], row['ticker'])
        for index, row in df.iterrows()
    ]

    return rows


def load_data(rows: list):
    '''Insert rows into the database using bulk insert.'''

    if not rows:
        print('No new data to insert.')
        return
    
    print('Loading extracted data into database...')
    
    params =                get_db_params()
    sentiment_sources_tbl = params['sentiment_sources']
    db_conn_params =        params['db_conn']

    #Same article several times is ok, but once per ticker
    insert_query = f'''
                    INSERT INTO {sentiment_sources_tbl} (source, published_date, title, body, url, scraped_at, ticker)
                    VALUES %s
                    ON CONFLICT (published_date, title, ticker) DO NOTHING;
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


def run_sentiment_sources_etl():
    start_time = datetime.now()
    print(f'Starting News Sentiment ETL at {start_time.strftime("%Y-%m-%d %H:%M:%S")}')

    #Extract
    rss_url = 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=SPY&region=US&lang=en-US'
    articles = fetch_rss_news(rss_url)

    #Transform
    org_to_ticker_dict = build_org_ticker_dict()
    nlp = spacy.load('en_core_web_sm')
    sources_df = build_asset_mentions_df(articles, org_to_ticker_dict, nlp, rss_url, start_time)
    rows = transform_data(sources_df)

    #Load
    load_data(rows)

    print(f'ETL process finished at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')


if __name__ == '__main__':
    run_sentiment_sources_etl()