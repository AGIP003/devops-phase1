
class BankAccount:
   
    def __init__(self, owner, balance=0):
        """ Called when creating new account"""
        self.owner = owner
        self.balance = balance
        print(f"__init__ called: Created account for {owner}")

    def __str__(self):
        """Called by print() - user-friendly string"""
        return f"{self.owner}'s account: ${self.balance}"

    def __repr__(self):
        """Called by repr() - developer-friendly string"""
        return f"BankAccount(owner='{self.owner}', balance={self.balance})"

    def __len__(self):
        """Called by len() - return number of digits in balance"""
        return len(str(int(self.balance)))

    
    def __add__(self, other):
        """Called by + operator"""
        if isinstance(other, BankAccount):
            # Adding two accounts: combine balances
            return BankAccount(
                f"{self.owner} & {other.owner}",
                self.balance + other.balance
            )
        elif isinstance(other, (int, float)):
            # Adding money to account
            new_account = BankAccount(self.owner, self.balance + other)
            return new_account
        else:
            raise TypeError("Can only add BankAccount or number")


    def __sub__(self, amount):
        """Called by - operator"""
        if isinstance(amount, (int, float)):
            return BankAccount(self.owner, self.balance - amount)
        else:
            raise TypeError("Can only subtract numbers")
    
    
    def __eq__(self, other):
        """Called by == operator"""
        if isinstance(other, BankAccount):
            return self.balance == other.balance
        return False
    
    
    def __lt__(self, other):
        """Called by < operator"""
        if isinstance(other, BankAccount):
            return self.balance < other.balance
        return False
    
    
    def __gt__(self, other):
        """Called by > operator"""
        if isinstance(other, BankAccount):
            return self.balance > other.balance
        return False
    
    
    def __iadd__(self, amount):
        """Called by += operator (in-place addition)"""
        if isinstance(amount, (int, float)):
            self.balance += amount
            return self
        else:
            raise TypeError("Can only add numbers")
    
    
    def __call__(self, action, amount=0):
        """Makes the object callable like a function"""
        if action == "deposit":
            self.balance += amount
            print(f"Deposited ${amount}")
        elif action == "withdraw":
            self.balance -= amount
            print(f"Withdrew ${amount}")
        else:
            print(f"Unknown action: {action}")

account1 = BankAccount("Alice", 1000)
account2 = BankAccount("Bob", 1500)

print("\n=== __str__ vs __repr__ ===")
print(account1)          # Calls __str__
print(str(account1))     # Calls __str__
print(repr(account1))    # Calls __repr__


print("\n=== __len__ ===")
print(f"Balance digits: {len(account1)}")  # 4 (from 1000)

print("\n=== __add__ (+ operator) ===")
account3 = account1 + account2  # Combine accounts
print(account3)

account4 = account1 + 500  # Add money
print(account4)

print("\n=== __sub__ (- operator) ===")
account5 = account1 - 200
print(account5)

print("\n=== __eq__ (== operator) ===")
acc_a = BankAccount("Test1", 1000)
acc_b = BankAccount("Test2", 1000)
acc_c = BankAccount("Test3", 2000)

print(f"acc_a == acc_b? {acc_a == acc_b}")  # True (same balance)
print(f"acc_a == acc_c? {acc_a == acc_c}")  # False


print("\n=== __lt__ and __gt__ (< and > operators) ===")
print(f"account1 < account2? {account1 < account2}")  # True
print(f"account1 > account2? {account1 > account2}")  # False


print("\n=== __iadd__ (+= operator) ===")
print(f"Before: {account1}")
account1 += 300  # In-place addition
print(f"After: {account1}")


print("\n=== __call__ (making object callable) ===")
account1("deposit", 100)  # Use object like a function!
account1("withdraw", 50)
print(account1)
