from dotenv import load_dotenv
import os

def get_db_params():
    '''Loads parameters to acces DB.'''

    load_dotenv()

    DB_CONN_PARAMS = {
        'host':     os.getenv('DB_HOST'),
        'port':     os.getenv('DB_PORT'),
        'database': os.getenv('DB_NAME'),
        'user':     os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }

    params = {'db_conn':            DB_CONN_PARAMS,
              'assets_price':       os.getenv('ASSETS_PRICE_TABLE'),
              'companies':          os.getenv('COMPANIES_TABLE'),
              'sentiment_sources':  os.getenv('SENTIMENT_SOURCES_TABLE'),
              'sentiment_analysis': os.getenv('SENTIMENT_ANALYSIS_TABLE'),
              'technical_analysis': os.getenv('TECHNICAL_ANALYSIS_TABLE'),
              'feature_matrix':     os.getenv('FEATURE_MATRIX_TABLE')
    }

    return params