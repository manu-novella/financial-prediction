from dotenv import load_dotenv
import os

def get_db_params():
    """Loads parameters to acces DB."""

    load_dotenv()

    DB_CONN_PARAMS = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD")
    }

    ASSETS_PRICE_TABLE_NAME = os.getenv("ASSETS_PRICE_TABLE")
    COMPANIES_TABLE = os.getenv("COMPANIES_TABLE")
    SENTIMENT_SOURCES_TABLE = os.getenv("SENTIMENT_SOURCES_TABLE")


    params = {"db_conn": DB_CONN_PARAMS,
              "assets_price": ASSETS_PRICE_TABLE_NAME,
              "companies": COMPANIES_TABLE,
              "sentiment_sources": SENTIMENT_SOURCES_TABLE
    }

    return params