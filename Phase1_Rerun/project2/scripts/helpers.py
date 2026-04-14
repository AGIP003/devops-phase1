def get_or_create_user(cursor, username, email, password_hash):
    cursor.execute(
        "SELECT id FROM users WHERE email=%s",
        (email,))
    row = cursor.fetchone()
    if row:
        return row["id"]
    cursor.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING ID",
        (username, email, password_hash)
    )
    new_row = cursor.fetchone()
    if new_row is None:
        raise RuntimeError(f"Insert failed for email ='{email}', username ='{username}'")
    return new_row["id"]

def get_or_create_category(cursor, user_id, name, type):
    cursor.execute(
        "SELECT id FROM categories WHERE user_id=%s AND name=%s",
        (user_id, name)
    )
    row = cursor.fetchone()
    if row:
        return row["id"]
    cursor.execute(
        "INSERT INTO categories (user_id, name, type) VALUES (%s, %s, %s) RETURNING ID",
        (user_id, name, type)
    )
    return cursor.fetchone()["id"]

def get_or_create_group(cursor, group_name):
    cursor.execute(
        "SELECT id FROM payment_method_groups WHERE name=%s",
        (group_name,)
    )
    row = cursor.fetchone()
    if row:
        return row["id"]
    cursor.execute(
        "INSERT INTO  payment_method_groups (name) VALUES(%s) RETURNING ID",
        (group_name,)
    )
    return cursor.fetchone()["id"]

def get_or_create_method(cursor, method_name, group_id):
    cursor.execute("SELECT id FROM payment_methods WHERE name=%s", (method_name,))
    row = cursor.fetchone()
    if row:
        return row["id"]
    cursor.execute(
        "INSERT INTO payment_methods (name, group_id) VALUES (%s, %s) RETURNING id",
        (method_name, group_id)
    )
    return cursor.fetchone()["id"]

def insert_transaction(cursor, txn):
    cursor.execute(
        """INSERT INTO transactions (user_id, category_id, payment_method_id, amount, date, description, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (
            txn["user_id"],
            txn["category_id"],
            txn["payment_method_id"],
            txn["amount"],
            txn["date"],
            txn.get("description"),
            txn.get("created_at")
        )
    )