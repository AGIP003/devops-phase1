"""
Personal Finance Tracker - Main CLI
"""
import argparse
import sys
import logging
from datetime import datetime

from utils.storage import Storage
from utils.validations import (
    validate_amount, validate_transaction_type,
    validate_category, validate_date, validate_description,
    ValidationError
)
#from utils.reports import (
#    generate_summary, generate_category_report,
#    generate_monthly_report, filter_by_date_range,
#    filter_by_category
#)
#Setup logging
import os
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler('logs/tracker.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class FinanceTrackerCli:
    def __init__(self):
        self.db = Storage()

    def run(self):
        """Shows the menu"""
        
        while True:
            print("---- WELCOME TO YOUR FINANCIAL TRACKER -----")
            print("1. Add transaction\n" 
            "2. Update transaction\n"
            "3. Delete transaction\n" 
            "4. Search\n" 
            "5. Display the transactions\n"
            "6. Exit")

            choice = input("Kindly key in a option 1, 2 , 3 or 4. (Numbers only)")
            if  choice == "1":
                self.handle_add()
            elif choice == "2":
                self.handle_update()
            elif choice == "3":
                self.handle_delete()
            elif choice == "4":
                self.handle_search()
            elif choice == "5":
                self.handle_display()
            elif choice == "6":
                print("Closing the Tracker. Bye!!")
                break
            else: 
                print("Invalid option. Kindly choose a number between 1-6") 
                continue

    def handle_add(self):
        """Collecting user's input and pass it through the other files"""
        print("--- ADD TRANSACTION ---")

        date = input("Enter date (YYYY-MM-DD): ")
        description = input("Enter description: ")
        type = input("Enter the type(income/expense): ").strip().lower()

        #Providing the option for users to choose in type and category
        if type == "income":
            print("Categories: salary, business, freelance, investments, gifts, other income")
        elif type == "expense":
            print("Expense: rent, utilities, food, transport, medical, subscriptions, entertainment, education, vacations, tools/software, personal_care, taxes, black tax, other expense")
        else:
            print("Invalid option. Choose between income or expense")

        category = input("Enter the category: ").strip().lower()
        amount = input("Enter the amount: ").strip()
        payment_method = input("Enter the payment method(bank/m-pesa,cash,paypal,card): ").strip().lower()
        

        data = {
            "date": date,
            "description": description,
            "type": type,
            "category": category,
            "amount": amount,
            "payment method": payment_method
        }
        
        try:
            success = self.db.add(data)
            logger.debug(f"Transaction: {data} added successfully")
            print(f"Transaction added successfully: {success}")
            return True
        except Exception as e:
            logger.error(f"Error in adding the transactions: {e}")
            return False


    def handle_search(self):
        """Ask the user what they are looking for and pass it through other files and display results"""
        print("----- SEARCH  ------")
        query = input("What are you looking for?")
        
        try:
            results = self.db.search(query)
            if results:
                print("Found results: ")
                for r in results:
                    print(r)
                logger.debug(f"User search result has been displayed succesfully {results}")
            else:
                print("No results found")
                logger.info("User's query was not found in the database")
            return True
        except Exception as e:
            print(f"Error during search: {e}")
            logger.error(f"Error during search: {e}")
            return False
    
    def handle_update(self):
        """Ask the user for the update, pass it through other files and then display the update"""
        print("---- UPDATE YOUR TRANSACTION ----")
        transaction_id = input("Kindly key in the ID of the transaction you want to delete: ")
        field = input("Kindly key in the field you want to update: ")
        updates = input("Key in the new value")
        try:
            updated = self.db.update(transaction_id, field, updates)
            logger.info(f"Successfully updated the transactions")
            print(f"Succesfully updated your transaction: {updated}")
            return True
        except Exception as e:
            print(f"Error during the update: {e}")
            logger.error(f"Failed to update the transaction: {e}")
            return False

    def handle_delete(self):
        """Ask the user what to delete, pass it through other files and confirm if successful"""
        print("----DELETE YOUR TRANSACTION----")
        transaction_id = input("Kindly key in the ID of the transaction you would like to delete: ")
        confirmation = input("Are you sure (y/n)?").strip().lower()
        if confirmation == "y":
            try:
                deleted = self.db.delete(transaction_id)
                logger.debug(f"Transaction deleted succesfully: {deleted}")
                print(f"The transaction:{transaction_id} has been deleted successfully")
            except Exception as e:
                print(f"Error in deleting the transaction. The Error is {e}")
                logger.error(f"Failed to delete the transaction: {e}")
            return True
        elif confirmation == "n":
            print("Deletion cancelled successfully")
            return False
        else: 
            print("Kindly key in y or no to confirm deletion")
            return False
        
    def handle_display(self):
        """Display the transactions"""
        print("------ All Transactions ------")
        self.db.display_all()
        logger.info(f"Displayed the results successfully")
        return True

if __name__ == "__main__":
    cli = FinanceTrackerCli()
    cli.run()


