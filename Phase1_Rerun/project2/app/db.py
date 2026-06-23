import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.errors import UniqueViolation
from config import get_config

config = get_config()

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

def get_category_id(category_name, user_id, category_type=None):
    """Convert category string to its database ID"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT id FROM categories WHERE LOWER(name) = LOWER(%s) AND user_id = %s",
                (category_name, user_id)
            )
            row = cursor.fetchone()
            if not row and category_type:
                cursor.execute(
                    """
                    INSERT INTO categories (user_id, name, type)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (user_id, category_name, category_type)
                )
                row = cursor.fetchone()
                conn.commit()
            if not row:
                raise ValueError(f"Category '{category_name}' not found for user {user_id}")
            return row['id']
    finally:
        conn.close()

def get_db_connection():
    database_url = config.DATABASE_URL.strip() if config.DATABASE_URL else None
    use_database_url = bool(
        database_url
        and (config.ENV in {"production", "prod"} or config.DB_USE_URL)
    )

    if use_database_url:
        return psycopg2.connect(database_url)

    if not config.DB_NAME or not config.DB_USER:
        raise RuntimeError(
            "Local database configuration is incomplete. "
            "Set DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, or enable DB_USE_URL=True."
        )

    return psycopg2.connect(
        host=config.DB_HOST,
        port=str(config.DB_PORT),
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )
TRANSACTION_SELECT = """
    SELECT
        t.id,
        t.user_id,
        t.date,
        t.description,
        c.type,
        c.name AS category,
        t.amount,
        pm.name AS payment_method
    FROM transactions t
    LEFT JOIN categories c ON t.category_id = c.id
    LEFT JOIN payment_methods pm ON t.payment_method_id = pm.id
"""

def search_transactions(query_text, user_id):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                TRANSACTION_SELECT + """
                WHERE LOWER(COALESCE(t.description, '')) ILIKE LOWER(%s)
                    AND t.user_id = %s
                ORDER BY t.date DESC
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

def get_all_transactions_for_user(user_id):
    if user_id is None:
        raise ValueError("user_id is required")

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                TRANSACTION_SELECT + """
                WHERE t.user_id = %s
                ORDER BY t.date DESC
                """,
                (user_id,)
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
            
            cursor.execute(TRANSACTION_SELECT + " ORDER BY t.date DESC")
            
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
            cursor.execute(TRANSACTION_SELECT + " WHERE t.id = %s",
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

def create_transactions(data):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO transactions 
                    (user_id, category_id, payment_method_id, amount, date, description, created_at)
                VALUES
                    (%(user_id)s, %(category_id)s, %(payment_method_id)s,
                     %(amount)s, %(date)s, %(description)s, CURRENT_TIMESTAMP)
                RETURNING *
                """,
                data,
                )
            row = cursor.fetchone()
            conn.commit()
        return db_get_transaction_by_id(row["id"])
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def create_transaction_for_user(
    user_id,
    category_name,
    transaction_type,
    payment_method_name,
    amount,
    date,
    description,
):
    """Resolve related records and create a transaction using one DB connection."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id
                FROM categories
                WHERE LOWER(name) = LOWER(%s) AND user_id = %s
                """,
                (category_name, user_id),
            )
            category = cursor.fetchone()
            if category is None:
                cursor.execute(
                    """
                    INSERT INTO categories (user_id, name, type)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (user_id, category_name, transaction_type),
                )
                category = cursor.fetchone()

            cursor.execute(
                """
                SELECT id
                FROM payment_methods
                WHERE LOWER(name) = LOWER(%s)
                """,
                (payment_method_name,),
            )
            payment_method = cursor.fetchone()
            if payment_method is None:
                raise ValueError(
                    f"Payment method '{payment_method_name}' not found"
                )

            cursor.execute(
                """
                INSERT INTO transactions (
                    user_id,
                    category_id,
                    payment_method_id,
                    amount,
                    date,
                    description,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id
                """,
                (
                    user_id,
                    category["id"],
                    payment_method["id"],
                    amount,
                    date,
                    description,
                ),
            )
            transaction_id = cursor.fetchone()["id"]

            cursor.execute(
                TRANSACTION_SELECT + " WHERE t.id = %s",
                (transaction_id,),
            )
            saved_transaction = cursor.fetchone()

        conn.commit()
        return saved_transaction
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


ALLOWED_UPDATE_FIELDS = {
    "amount",
    "date",
    "description",
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
    
    query = f"UPDATE transactions set {', '.join(set_parts)} WHERE id = %(id)s RETURNING id"
    params = {**updates, "id": txn_id}
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            conn.commit()
        if row:
            return db_get_transaction_by_id(row["id"]), None     
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
                           RETURNING id, username, email
                           """,
                           {"email": email, "username":username, "password_hash": password_hash}
            )
            rows = cursor.fetchone()
            conn.commit()
        if rows is not None:
            rows.setdefault("role", "user")
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


def create_telegram_link_token(user_id, token, expires_at):
    """Create one active Telegram link token for a user."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                UPDATE telegram_link_tokens
                SET used = TRUE
                WHERE user_id = %s AND used = FALSE
                """,
                (user_id,),
            )
            cursor.execute(
                """
                INSERT INTO telegram_link_tokens (user_id, token, expires_at)
                VALUES (%s, %s, %s)
                RETURNING token, expires_at, created_at
                """,
                (user_id, token, expires_at),
            )
            row = cursor.fetchone()
        conn.commit()
        return row
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def telegram_linking_schema_ready():
    """Return whether the database supports Telegram account linking."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    to_regclass('public.telegram_link_tokens') IS NOT NULL
                    AND EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = 'users'
                          AND column_name = 'telegram_id'
                    )
                """
            )
            return cursor.fetchone()[0]
    finally:
        conn.close()


def get_telegram_link_status(user_id):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT telegram_id, updated_at
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()
        return row
    finally:
        conn.close()


def unlink_telegram_account(user_id):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                UPDATE users
                SET telegram_id = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, telegram_id
                """,
                (user_id,),
            )
            user = cursor.fetchone()
            if user is None:
                conn.rollback()
                return None

            cursor.execute(
                """
                UPDATE telegram_link_tokens
                SET used = TRUE
                WHERE user_id = %s AND used = FALSE
                """,
                (user_id,),
            )
        conn.commit()
        return user
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_user_by_telegram_id(telegram_id):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, username, email, role, telegram_id
                FROM users
                WHERE telegram_id = %s
                """,
                (telegram_id,),
            )
            return cursor.fetchone()
    finally:
        conn.close()


def get_telegram_preferences(user_id):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO telegram_user_preferences (user_id)
                VALUES (%s)
                ON CONFLICT (user_id) DO NOTHING
                """,
                (user_id,),
            )
            cursor.execute(
                """
                SELECT default_payment_method, category_aliases
                FROM telegram_user_preferences
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()
        conn.commit()
        return row
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_telegram_preferences(user_id, default_payment_method=None, category_aliases=None):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO telegram_user_preferences (user_id)
                VALUES (%s)
                ON CONFLICT (user_id) DO NOTHING
                """,
                (user_id,),
            )
            updates = []
            params = []
            if default_payment_method is not None:
                updates.append("default_payment_method = %s")
                params.append(default_payment_method)
            if category_aliases is not None:
                updates.append("category_aliases = %s::jsonb")
                params.append(category_aliases)
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(user_id)
                cursor.execute(
                    f"""
                    UPDATE telegram_user_preferences
                    SET {", ".join(updates)}
                    WHERE user_id = %s
                    """,
                    params,
                )
            cursor.execute(
                """
                SELECT default_payment_method, category_aliases
                FROM telegram_user_preferences
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()
        conn.commit()
        return row
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def consume_telegram_link_token(token, telegram_id):
    """Atomically consume a valid link token and bind its user to Telegram."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    t.id AS link_token_id,
                    t.user_id,
                    t.expires_at,
                    t.used,
                    (t.expires_at <= CURRENT_TIMESTAMP) AS expired,
                    u.username,
                    u.email,
                    u.role,
                    u.telegram_id
                FROM telegram_link_tokens AS t
                JOIN users AS u ON u.id = t.user_id
                WHERE t.token = %s
                FOR UPDATE
                """,
                (token,),
            )
            link = cursor.fetchone()

            if link is None:
                conn.rollback()
                return None, "invalid"
            if link["used"]:
                conn.rollback()
                return None, "used"

            if link["expired"]:
                cursor.execute(
                    "UPDATE telegram_link_tokens SET used = TRUE WHERE id = %s",
                    (link["link_token_id"],),
                )
                conn.commit()
                return None, "expired"

            cursor.execute(
                "SELECT id FROM users WHERE telegram_id = %s AND id <> %s",
                (telegram_id, link["user_id"]),
            )
            if cursor.fetchone():
                conn.rollback()
                return None, "telegram_in_use"

            cursor.execute(
                """
                UPDATE users
                SET telegram_id = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (telegram_id, link["user_id"]),
            )
            cursor.execute(
                "UPDATE telegram_link_tokens SET used = TRUE WHERE id = %s",
                (link["link_token_id"],),
            )

        conn.commit()
        return {
            "id": link["user_id"],
            "username": link["username"],
            "email": link["email"],
            "role": link["role"] or "user",
            "telegram_id": telegram_id,
        }, None
    except UniqueViolation:
        conn.rollback()
        return None, "telegram_in_use"
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
