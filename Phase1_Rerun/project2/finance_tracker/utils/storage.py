"""
Docstring for project2.finance_tracker.utils.storage
Storage module - Handle JSON persistence
"""

import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from utils.validations import (
    validate_amount, validate_transaction_type,
    validate_category, validate_date, validate_description, validate_payment_method,
    ValidationError
)

class Storage:
    """Handle transactions in JSON"""

    def __init__(self, filename='data/transactions.json'):
        self.filename = filename
        self._ensure_file_exists()
        self.transactions = self.load_all()

    def _ensure_file_exists(self):
        """Create file if it doesnt exist"""
        #Data Directory
        directory = os.path.dirname(self.filename)
        if directory:
            os.makedirs(directory, exist_ok=True)

        if not os.path.exists(self.filename):
            with open(self.filename, "w") as f:
                json.dump({}, f)
                logger.info(f"Created new storage file: {self.filename}")
        
    def load_all(self):
        """Load all transactions"""
        try:
            with open(self.filename, "r") as f:
                transactions = json.load(f)
            logger.debug(f"Loaded {len(transactions)} transactions successfully")
            return transactions
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load: {e}")
            return {}

    def save_all(self, transactions):
        """Save all transactions"""
        try:
            with open(self.filename, "w") as f:
                json.dump(transactions, f, indent=4, sort_keys=True)

            #Keeping the memory in sync with the file
            self.transactions = transactions
            
            logger.debug(f"Saved {len(transactions)} transactions successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save: {e} ")
            return False
        
    def add(self, transaction):
        """Add a single transactions"""
        #Validation
        try:
            clean_amount = validate_amount(transaction.get('amount'))
            clean_type = validate_transaction_type(transaction.get('type'))
            clean_category = validate_category(clean_type, transaction.get('category'))
            clean_date = validate_date(transaction.get('date'))
            clean_description = validate_description(transaction.get('description'))
            # Accept both 'payment method' (preferred) and 'payment_method' (alternate key)
            pm_raw = transaction.get('payment method') if transaction.get('payment method') is not None else transaction.get('payment_method')
            clean_payment_method = validate_payment_method(pm_raw) 

            #Generate ID and Timestamp
            new_id = self._generate_id()
            audit_time = datetime.now().isoformat()
            record = {
                "id": new_id,
                "date": clean_date,
                "description": clean_description,
                "type": clean_type,
                "category": clean_category,
                "amount": clean_amount,
                "payment method": clean_payment_method,
                "created_at": audit_time
            }

            self.transactions[new_id] = record
            logger.info(f"Added and saved {new_id} successfully")
            return self.save_all(self.transactions)
        except Exception as e:
            logger.error(f"Failed to add transactions: {e} ")
            return False
        

    def delete(self, transaction_id):
        """Delete transaction by ID"""
        if transaction_id in self.transactions:
            del self.transactions[transaction_id]

            logger.info(f"Deleted {transaction_id} successfully")
            return self.save_all(self.transactions)
   
        logger.error(f"Transaction: {transaction_id} does not exist!!")
        return False
    

    def update(self, transaction_id, field, updates):
        """Update a specific transaction"""
        if transaction_id not in self.transactions:
            print("No transaction found")
            logger.error(f"The transaction:{transaction_id} does not exist")
            return False

        #The current record  
        record = self.transactions[transaction_id]
      
        #Routing
        if field == "amount":
            updates = validate_amount(updates)
        if field == "category":
            # validate_category expects (txn_type, category)
            updates = validate_category(record.get('type'), updates)
        if field == "date":
            updates = validate_date(updates)
        if field == "description":
            updates = validate_description(updates)
        if field == "type":
            updates = validate_transaction_type(updates)
        if field == "payment method":
            updates = validate_payment_method(updates)
        
        #Updating the specific field
        record[field] = updates
        logger.info(f"Updated {field} successfully")

        return self.save_all(self.transactions)
        

    def search(self, query):
        """Searching transactions looks through categories and descriptions"""
        query = str(query).lower().strip()

        results = []

        for transacrions_id, record in self.transactions.items():
            #Check if the query is in categories or description
            in_category = query in record['category'].lower()
            in_description = query in record['description'].lower()

            if in_category or in_description:
                results.append(record)
        
        logger.info(f"Searched for{len(results)} successfully")
        return results

    def display_all(self):
        """Displaying all  transactions"""
        if not self.transactions:
            print("No transactions found.")
            logger.error(f"The transaction {self.transactions} does not exist")
            return 
        for transaction_id, record in self.transactions.items():
            print(f" - ID:{record['id']}, DATE:{record['date']}, DESCRIPTION:{record['description']},  TYPE:{record['type']}, CATEGORY:{record['category']}, AMOUNT:{record['amount']}, PAYMENT METHOD:{record['payment method']} ")
   

    def _generate_id(self):
        """Generate unique ID"""
        if not self.transactions:
            return "1"
        
        # Find the highest current ID and add 1
        existing_ids = [int(transaction_id) for transaction_id in self.transactions.keys()]
        return str(max(existing_ids) + 1)
        





