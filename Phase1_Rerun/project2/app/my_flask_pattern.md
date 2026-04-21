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

