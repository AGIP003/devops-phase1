import psycopg2
import os
from psycopg2.extras import RealDictCursor
from app import create_app 
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    app = create_app()
    conn = psycopg2.connect(
        host = os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
    )