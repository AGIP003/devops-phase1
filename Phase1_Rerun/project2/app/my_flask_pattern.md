# My Flask Patterns (Reference When Needed)

## Basic Route
```python
from flask import Flask
app = Flask(__name__)

@app.route('/api/endpoint', methods=['GET', 'POST'])
def my_function():
    return jsonify({'key': 'value'}), 200
```

## Database Query
```python
cursor = conn.cursor()
cursor.execute("SELECT * FROM table WHERE id = %s", (id,))
results = cursor.fetchall()
cursor.close()
```

## Insert with RETURNING
```python
cursor.execute(
    "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id",
    (name, email)
)
new_id = cursor.fetchone()[0]
conn.commit()
```
## Building updates dynamically
set_parts = [f"{k} = %s" for k in updates.keys()]
query = f"UPDATE transactions SET {', '.join(set_parts)} WHERE id = %s RETURNING *"
values = list(updates.values()) + [txn_id]
cur.execute(query, values)

## Pattern: Simple text search on one column

Given:
- A table `transactions` with text column `description`.
- User input `query_text` (e.g., "milk").

Goal:
- Return all rows where `description` contains `query_text`, case‑insensitively, including `NULL` safety.

SQL:
```sql
SELECT *
FROM transactions
WHERE LOWER(COALESCE(description, '')) ILIKE LOWER('%' || %s || '%');
```

Python helper:
```python
def search_transactions(query_text):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM transactions WHERE LOWER(COALESCE(description, '')) ILIKE LOWER(%s)",
                (f'%{query_text}%',)
            )
            return cur.fetchall()
    finally:
        conn.close()
```

- Route:
  - `GET /transactions?query=milk` → uses `search_transactions("milk")`.
  - No `query` → falls back to `get_all_transactions()`.

  Bcrypt (Capital B)
👉 This is a class
Think:
blueprint / template / factory
from flask_bcrypt import Bcrypt
You’re importing the thing used to create an object

🔹 bcrypt (small b)
👉 This is a variable (instance)
Think
the actual usable object
bcrypt = Bcrypt()
Now you can do:
bcrypt.generate_password_hash(...)

⚠️ Why naming convention matters

Python devs use:
Capital letters → classes
lowercase → variables/instances

So when you see:
Something()

Your brain should go:
“That’s a class being instantiated”

🧭 In your case
# extensions.py
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()

You:
import the class
create one shared instance
reuse it everywhere
🧨 Subtle mistake people make

They do this:
bcrypt = bcrypt()
Now Python is like:
“You just overwrote the class with a variable. Congratulations.”