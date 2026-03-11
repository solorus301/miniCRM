from psycopg2.extras import RealDictCursor
import psycopg2


def get_db():
    conn = psycopg2.connect(
        dbname='mini_crm', #edit
        user='postgres',
        password='postgres',
        host='localhost',
        port='5432',
        cursor_factory=RealDictCursor      
)
    try:
        yield conn
    finally:
        conn.close()