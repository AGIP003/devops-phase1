 ``cursor.fetchone()`` | Returns **a single row** from the result set as a tuple. If no more rows are available, it returns ``None``. | When you only need one row (e.g., checking a single record, iterating row by row). |
| ``cursor.fetchall()`` | Returns **all remaining rows** from the result set as a list of tuples. If no rows remain, it returns an empty list. | When you want to process the entire result set at once. |

🧩 Practical Tip
Use fetchone() inside a loop if you want to process rows one by one without loading them all into memory.

Use fetchall() when the dataset is small enough to fit comfortably in memory and you want quick access to all rows.


``Dynamic SET clause``:
Build SQL update statements based only on fields present in the request payload.
Example: if payload = {"amount": 500}, query becomes:
        UPDATE transactions SET amount = %(amount)s WHERE id = %s RETURNING *

`Named parameters (%(field)s)`:
Placeholders map to dict keys.
Works naturally with request.json in Flask.
Order doesn’t matter, keys must match.

`Tradeoffs: Named vs Positional`
Named (%(field)s)
✅ Clear mapping between JSON keys and SQL columns.
✅ Safer, order-independent.
✅ Perfect for APIs (dict payloads).
❌ Slightly more verbose.

Positional (%s)
✅ Shorter syntax.
✅ Good for small, fixed queries.
❌ Order-sensitive (easy to mess up).
❌ Harder to read with many fields.

🚀 Why This Makes API Faster
No wasted updates: Only updates fields provided → less DB work.
No extra SELECT: RETURNING * gives back the updated row immediately.
Cleaner payload flow: Can pass request.json directly into query.
Less boilerplate: No need to reshape dicts into tuples manually.

## SQL Text Search Basics

- `LIKE '%text%'` → matches strings that contain `text` (case‑sensitive).  
- `ILIKE '%text%'` → same as `LIKE`, but **case‑insensitive** (recommended for user‑faced search).

- `COALESCE(column, default)` → returns first non‑`NULL` value.  
  - `COALESCE(description, '')` → if `description` is `NULL`, use `''` instead.

- `LOWER(text)` → convert text to lowercase.  
  - Useful when combining with `ILIKE` for extra robustness.

Example pattern for user search:

```sql
SELECT *
FROM transactions
WHERE LOWER(COALESCE(description, '')) ILIKE LOWER('%{{query}}%');
```

- Searches `description` for `query` (case‑insensitive, safe for `NULL`).
- You can OR additional fields, e.g., by category, payment method, etc.

curl: (56) Recv failure: Connection reset by peer

