import psycopg2
import os
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Helper functions to get IDs from string values
def get_payment_method_id(payment_method_name):
    """Convert payment method string to its database ID"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT id FROM payment_methods WHERE LOWER(name) = LOWER(%s)",
                (payment_method_name,)
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Payment method '{payment_method_name}' not found")
            return row['id']
    finally:
        conn.close()

def get_category_id(category_name, user_id):
    """Convert category string to its database ID"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT id FROM categories WHERE LOWER(name) = LOWER(%s) AND user_id = %s",
                (category_name, user_id)
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Category '{category_name}' not found for user {user_id}")
            return row['id']
    finally:
        conn.close()

def get_db_connection():
    return psycopg2.connect(
        host = os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
    )   

def search_transactions(query_text, user_id):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT * 
                FROM transactions
                WHERE  LOWER(COALESCE(description, '')) ILIKE LOWER(%s) AND user_id = %s
                """,
                (f"%{query_text}%", user_id)
            )
            rows = cursor.fetchall()
        conn.commit()
        return rows
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_all_transactions():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
            rows = cursor.fetchall()
        conn.commit()
        return rows
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def db_get_transaction_by_id(txn_id):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM transactions WHERE id = %s",
                           (txn_id,)
                           )
            rows = cursor.fetchone()
            if rows is None:
                raise RuntimeError("Failed to retrieve the transaction")
        conn.commit()
        return rows
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def create_transactions(data):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO transactions 
                    (user_id, category_id, payment_method_id, amount, date, description, type, created_at)
                VALUES
                    (%(user_id)s, %(category_id)s, %(payment_method_id)s,
                     %(amount)s, %(date)s, %(description)s, %(type)s, CURRENT_TIMESTAMP)
                RETURNING *
                """,
                data,
                )
            row = cursor.fetchone()
            conn.commit()
        return row
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

ALLOWED_UPDATE_FIELDS = {
    "amount",
    "date",
    "description",
    "type",
    "category_id",
    "payment_method_id",
}
def update_transactions(txn_id, updates):
    conn = get_db_connection()
    #Filtering only allowed fields
    updates = {k: v for k, v in updates.items() if k in ALLOWED_UPDATE_FIELDS}
    if not updates:
        return None, "No valid fields to update"
        
    #Building set dynamically (only updating present fields)
    set_parts = [f"{k} = %({k})s" for k in updates.keys()]
    if not set_parts:
        return None
    
    query = f"UPDATE transactions set {', '.join(set_parts)} WHERE id = %s RETURNING *"
    params = {**updates, "id": txn_id}
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            conn.commit()
        if row:
            return row, None     
        else:
            return None, "Transaction not found"   
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_transactions(txn_id):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("DELETE FROM transactions WHERE id = %s RETURNING id",
                           (txn_id,)
                           )
            rows = cursor.fetchone()
            conn.commit()
        return rows
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s",
                           (email,)
                           )
            row = cursor.fetchone()
            conn.commit()
        return row
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_user_by_id(user_id):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s",
                           (user_id,)
                           )
            row = cursor.fetchone()
            conn.commit()
        return row
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_user_by_id(user_id):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s",
                           (user_id,)
                           )
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def insert_user_hashed_pw(email, username, password_hash):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                           INSERT INTO users (email, username, password_hash) 
                           VALUES (%(email)s, %(username)s, %(password_hash)s)
                           RETURNING id, username, email, role, created_at
                           """,
                           {"email": email, "username":username, "password_hash": password_hash}
            )
            rows = cursor.fetchone()
            conn.commit()
        return rows
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def update_reset_password(user_id, password_hash):
    conn = get_db_connection()

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                            UPDATE users SET password_hash = %s WHERE id=%s
                            """,
                           (password_hash, user_id)
                           )
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


