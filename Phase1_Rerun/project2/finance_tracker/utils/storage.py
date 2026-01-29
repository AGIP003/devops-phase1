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
    validate_category, validate_date, validate_description,
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
                json.dump(self.transactions, f, indent=4, sort_keys=True)

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
            clean_category = validate_category(transaction.get('category'))
            clean_date = validate_date(transaction.get('date'))
            clean_description = validate_description(transaction.get('description'))
            clean_type = validate_transaction_type(transaction.get('type'))

            #Generate ID and Timestamp
            new_id = self._generate_id()
            audit_time = datetime.now().isoformat()
            record = {
                "id": new_id,
                "amount": clean_amount,
                "category": clean_category,
                "date": clean_date,
                "description": clean_description,
                "type": clean_type,
                "created_at": audit_time
            }

            self.transactions[new_id] = record
            logger.info(f"Added and saved {len(new_id)} successfully")
            return self.save_all(self.transactions)
        except Exception as e:
            logger.error(f"Failed to add transactions: {e} ")
            return False
        

    def delete(self, transaction_id):
        """Delete transaction by ID"""
        if transaction_id not in self.transactions():
            logger.error(f"Transaction: {transaction_id} does not exist!!")
            self.transactions[transaction_id].pop()

        for transaction_id in self.transactions.keys():
            if self.transactions['transaction_id'] == transaction_id:
                del self.transactions[transaction_id]
        
        logger.info(f"Deleted {transaction_id} successfully")
        return self.save_all(self.transactions)
    
    def update(self, transaction_id, updates):
        """Update a specific transaction"""
        
    
    def search(self, transaction_id):
        """Searching transactions"""



    def display_all(self):
        """Displaying all  transactions"""
        for transaction_id, records in self.transactions.items():
            for record in records:
                print(f" - ID:{record['id']}, AMOUNT:{record['amount']}, CATEGORY:{record['category']}, DATE:{record['date']}, DESCRIPTION:{record['description']}, TYPE:{record['type']} ")
   
    def _generate_id(self, transactions):
        """Generate unique ID"""
        if not self.transactions:
            return "1"
        
        # Find the highest current ID and add 1
        existing_ids = [int(transaction_id) for transaction_id in self.transactions.keys]
        return str(max(existing_ids) + 1)
        





