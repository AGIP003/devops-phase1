import json
from dotenv import load_dotenv
from db_config import DatabaseConnection
from psycopg2.extras import execute_values
import os 

load_dotenv()

def migrate_json_to_postgres(json_filePath):
    with DatabaseConnection() as cursor:
        # Read Json data
        with open(json_filePath, 'r') as f:
            data = json.load(f)

        print(f"Loaded {len(data)} transactions from {json_filePath}")

        #Insert users
        for user in data["users"]:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                (user["username"], user["email"], user["password_hash"])
            )
            user["db_id"] = cursor.fetchone()[0]

        #Insert categories
        for category in data["categories"]:
            cursor.execute(
                "INSERT INTO categories (user_id, name, type) VALUES (%s, %s, %s) RETURNING id",
                (category["user_id"], category["name"], category["type"])
            )
            category["db_id"] = cursor.fetchone()[0]

        #Insert payment methods
        #payment lookup (shell)
        payment_lookup = {
            "m-pesa": "mobile",
            "airtel money": "mobile",
            "paypal": "digital",
            "cash": "cash"
        }
        #Dynamic IDs: store DB IDs separately
        group_ids = {}
        method_ids = {}
        for group in set(payment_lookup.values()):
            cursor.execute(
                "INSERT INTO payment_method_groups (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING id",
                (group,)
            )
            row = cursor.fetchone()

            if row:
                group_ids[group] = row[0]
            else:
                cursor.execute("SELECT id FROM payment_method_groups WHERE name=%s", (group,))
                group_ids[group] = cursor.fetchone()[0]

        for method, group in payment_lookup.items():
            cursor.execute(
                "INSERT  INTO payment_methods (name, group_id) VALUES (%s, %s) RETURNING id",
                (method,)
            )
            row = cursor.fetchone()

            if not row:
                cursor.execute(
                    "INSERT INTO payment_methods (name, group_id) VALUES (%s, %s) RETURNING id",
                    (method, group_ids[group])
                )
                method_ids[method] = cursor.fetchone()[0]
            else:
                method_ids[method] = row[0]
        
        for txn in data["transactions"]:
            try:
                cursor.execute(
                    """INSERT INTO transactions (user_id, category_id, payment_method_id, amount, date, description)
                    VALUES(%s, %s, %s, %s, %s)
                    """,
                    (
                        txn["user_id"],
                        txn["category_id"],
                        payment_lookup[txn["payment method"]],
                        txn["amount"],
                        txn["date"],
                        txn.get("description")
                    )
                )
            except Exception as e:
                print(f"Error in inserting the transactions: {txn.get('description')}")

        


if __name__ == "__main__":
    json_filePath='/home/jay/devops-phase1/Phase1_Rerun/data/transactions.json'

    if  not os.path.exists(json_filePath):
        print(f"File not found: {json_filePath}")
        print("Kindly provide the correct path to your JSON file")
    else:
        migrate_json_to_postgres(json_filePath)



