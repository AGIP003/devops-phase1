"""
Docstring for project2.finance_tracker.utils.storage
Storage module - Handle JSON persistence
"""

import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Storage:
    """Handle transactions in JSON"""

    def __init__(self, filename='data/transactions.json'):
        self.filename = filename
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create file if it doesnt exist"""
        #Data Directory
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)

        #Empty file if it doesnt exist
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                json.dump([], f)
            logger.info(f"Created New storage file: {self.filename}")

    def load_all(self):
        """Load all transactions"""
        try:
            with open(self.filename, 'r') as f:
                transactions = json.load(f)
            logger.debug(f"Loaded {len(transactions)} transactions")
            return transactions
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading transactions: {e}")
            return []
        
    def save_all(self, transactions):
        """Save all transactions"""
        try:
            with open(self.filename, 'w') as f:
                json.dump(transactions, f, indent=2)
            logger.info(f"Saved {len(transactions)} transactions.")
            return True
        except Exception as e:
            logger.error(f"Error saving transactions: {e}")
            return False
        
    def add(self, transaction):
        """Add a single transactions"""
        transactions = self.load_all()

        #Adding a transaction ID if not present
        if 'id' not in transaction:
            transaction['id'] = self._generate_id(transactions)

        #Adding a timestamp if not present
        if 'created_at' not in transaction:
            transactions['created_at'] = datetime.now().isoformat()    

        transactions.append(transaction)

        if self.save_all(transactions):
            logger.info(f"Added transaction: {transaction['id']}")
            return transaction
        else:
            return None

    def delete(self, transaction_id):
        """Delete transaction by ID"""
        transactions = self.load_all()
        original_count = len(transactions)

        transactions = [t for t in transactions if t.get('id') != transaction_id]
        if len(transactions) < original_count:
            self.save_all(transactions)
            logger.info(f"Deleted transaction: {transaction_id}")
            return True
        
        logger.warning(f"Transaction not found: {transaction_id}")
        return False
    
    def update(self, transaction_id, updates):
        """Update a specific transaction"""
        transactions = self.load_all()

        for t in transactions:
            if t.get('id') == transaction_id:
                t.update(updates)
                t['updated_at'] = datetime.now().isoformat()
                self.save_all(transactions)
                logger.info(f"Updated transaction: {transaction_id}")
                return True
            
            logger.warning(f"Transaction not found: {transaction_id}")
            return False
    
    def _generate_id(self, transactions):
        """Generate unique ID"""
        if not transactions:
            return 1
        return max(t.get('id', 0) for t in transactions) + 1





