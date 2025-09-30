class BankAccount:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance
        self.transactions = []

    # Instance method - operates on specific account
    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            self.transactions.append(f"Deposited ${amount}")
            print(f"✓ {self.owner} deposited ${amount}")
            print(f"  New balance: ${self.balance}")
        else:
            print("❌ Deposit amount must be positive!")
    
    
    def withdraw(self, amount):
        if amount > self.balance:
            print(f"❌ Insufficient funds! Balance: ${self.balance}")
        elif amount <= 0:
            print("❌ Withdrawal amount must be positive!")
        else:
            self.balance -= amount
            self.transactions.append(f"Withdrew ${amount}")
            print(f"✓ {self.owner} withdrew ${amount}")
            print(f"  New balance: ${self.balance}")
    
    
    def get_balance(self):
        return f"{self.owner}'s balance: ${self.balance}"
    
    
    def transfer_to(self, other_account, amount):
        """Transfer money to another account"""
        if amount > self.balance:
            print(f"❌ Transfer failed! Insufficient funds.")
        else:
            self.withdraw(amount)
            other_account.deposit(amount)
            self.balance -= amount
            self.transactions.append(f"Transferred ${amount}")
            print(f"✓ Transferred ${amount} from {self.owner} to {other_account.owner}")
            print(f"Balance remaining: {self.balance}") 
    
    def show_transactions(self):
        print(f"\n=== {self.owner}'s Transactions ===")
        if not self.transactions:
            print("No transactions yet.")
        else:
            for transaction in self.transactions:
                print(f"  • {transaction}")


# Testing Methods
# Create two bank accounts
account1 = BankAccount("Alice", 1000)
account2 = BankAccount("Bob", 500)
print("=== Initial Balances ===")
print(account1.get_balance())
print(account2.get_balance())


print("\n=== Deposits ===")
account1.deposit(500)
account2.deposit(200)


print("\n=== Withdrawals ===")
account1.withdraw(300)
account2.withdraw(1000)  # Should fail


print("\n=== Transfers ===")
account1.transfer_to(account2, 200)


print("\n=== Transaction History ===")
account1.show_transactions()
account2.show_transactions()


print("\n=== Final Balances ===")
print(account1.get_balance())
print(account2.get_balance())
