from dotenv import load_dotenv
import os

def get_db_params():
    '''Loads parameters to access DB.'''

    load_dotenv()

    DB_CONN_PARAMS = {
        'host':     os.getenv('FINANCIAL_DB_HOST', 'localhost'), #By default, localhost - if not specified by env var in Docker
        'port':     os.getenv('FINANCIAL_DB_PORT'),
        'database': os.getenv('FINANCIAL_DB_NAME'),
        'user':     os.getenv('FINANCIAL_DB_USER'),
        'password': os.getenv('FINANCIAL_DB_PASSWORD')
    }

    params = {'db_conn':            DB_CONN_PARAMS,
              'assets_price':       os.getenv('ASSETS_PRICE_TABLE'),
              'assets':             os.getenv('ASSETS_TABLE'),
              'sentiment_sources':  os.getenv('SENTIMENT_SOURCES_TABLE'),
              'sentiment_analysis': os.getenv('SENTIMENT_ANALYSIS_TABLE'),
              'technical_analysis': os.getenv('TECHNICAL_ANALYSIS_TABLE'),
              'feature_matrix':     os.getenv('FEATURE_MATRIX_TABLE')
    }

    return params