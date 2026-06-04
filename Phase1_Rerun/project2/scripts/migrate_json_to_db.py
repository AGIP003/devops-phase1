import json
from dotenv import load_dotenv
from db_config import DatabaseConnection
from psycopg2.extras import execute_values
import os 
from helpers import(
    get_or_create_category,
    get_or_create_group,
    get_or_create_method,
    get_or_create_user,
    insert_transaction
)
load_dotenv()

PAYMENT_METHOD_ALIASES = {
    "bank": "bank transfer",
}

def migrate_json_to_postgres(json_filePath):
    with DatabaseConnection() as cursor:
        # Read Json data
        with open(json_filePath, 'r') as f:
            data = json.load(f)

        print(f"Loaded {len(data)} transactions from {json_filePath}")

        #Insert users
        user_id = get_or_create_user(
            cursor,
            username="jay",
            email="blessedmuchemi@gmail.com",
            password_hash="hashed_password"
        )

        print("got user id:", user_id)
        #payment method --> group mapping
        payment_lookup = {
            "m-pesa":"mobile",
            "airtel money":"mobile",
            "t-kash":"mobile",
            "equitel":"mobile",
            "bank transfer":"banking",
            "debit card":"banking",
            "credit card":"banking",
            "paypal":"digital",
            "cash":"cash"
        }

        for txn_id, txn in data.items():
            try:
                #Category
                category_id = get_or_create_category(
                    cursor,
                    user_id,
                    txn["category"],
                    txn["type"]
                )

                #Payment Method + Group
                method_name = txn.get("payment method")
                method_name = PAYMENT_METHOD_ALIASES.get(method_name, method_name)
                group_name = payment_lookup.get(method_name, "cash")
                group_id = get_or_create_group(
                    cursor,
                    group_name)
                
                method_id = get_or_create_method(
                    cursor,
                    method_name,
                    group_id
                )

                #Transaction
                insert_transaction(cursor, {
                        "user_id": user_id,
                        "category_id": category_id,
                        "payment_method_id": method_id,
                        "amount": txn["amount"],
                        "date": txn["date"],
                        "description": txn.get("description"),
                        "created_at": txn.get("created_at")
                    })

            except Exception as e:
                print(f"Error in inserting the transactions: {txn.get('description')}:{e}")
                raise
            
        print("MIGRATION COMPLETE")

if __name__ == "__main__":
    json_filePath='/home/jay/devops-phase1/Phase1_Rerun/project2/finance_tracker/data/transactions.json'

    if  not os.path.exists(json_filePath):
        print(f"File not found: {json_filePath}")
        print("Kindly provide the correct path to your JSON file")
    else:
        migrate_json_to_postgres(json_filePath)


