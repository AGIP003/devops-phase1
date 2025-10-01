class BankAccount:
    
    def __init__(self, owner, initial_balance, pin):
        #PUBLIC ATTRIBUTES (no underscore)
        self.owner = owner

        #PROTECTED ATTRIBUTES (single underscore - convention only)
        self._account_number = self._generate_account_number()

        #PRIVATE ATTRIBUTES (double underscore - name mangling)
        self.__balance = initial_balance
        self.__pin = pin

    def _generate_account_number(self):
        """Protected method - internal use"""
        import random
        return f"ACC{random.randint(10000, 99999)}"

    def __validate_pin(self, pin):
        """Private method - cannot be called from outside """
        return pin == self.__pin
 
    # PUBLIC interface - safe way to interact with private data
    def deposit(self, amount, pin):
        if not self.__validate_pin(pin):
            print("❌ Invalid PIN!")
            return False
        
        if amount > 0:
            self.__balance += amount
            print(f"✓ Deposited ${amount}. New balance: ${self.__balance}")
            return True
        else:
            print("❌ Amount must be positive!")
            return False
    
    
    def withdraw(self, amount, pin):
        if not self.__validate_pin(pin):
            print("❌ Invalid PIN!")
            return False
        
        if amount > self.__balance:
            print(f"❌ Insufficient funds! Balance: ${self.__balance}")
            return False
        elif amount > 0:
            self.__balance -= amount
            print(f"✓ Withdrew ${amount}. New balance: ${self.__balance}")
            return True
        else:
            print("❌ Amount must be positive!")
            return False
    
    
    def get_balance(self, pin):
        """Safe way to check balance"""
        if self.__validate_pin(pin):
            return f"Balance: ${self.__balance}"
        else:
            return "❌ Invalid PIN!"

    def change_pin(self, old_pin, new_pin):
        if self.__validate_pin(old_pin):
            self._pin = new_pin
            print("PIN changed succesfully")
        else:
            print("INVALID old PIN!")


# Testing Encapsulation

account = BankAccount("Alice", 1000, "1234")

print("=== PUBLIC Access ===")
print(f"Owner: {account.owner}")  # ✓ Works
print(f"Account #: {account._account_number}")  # ✓ Works (but shouldn't do this!)


print("\n=== PRIVATE Access ===")
# These DON'T work (as intended):
try:
    print(account.__balance)  # ❌ Error!
except AttributeError as e:
    print(f"❌ Error: {e}")

try:
    print(account.__pin)  # ❌ Error!
except AttributeError as e:
    print(f"❌ Error: {e}")


print("\n=== SAFE Access Through Methods ===")
print(account.get_balance("1234"))  # ✓ Correct PIN
print(account.get_balance("0000"))  # ❌ Wrong PIN


print("\n=== Deposits & Withdrawals ===")
account.deposit(500, "1234")
account.withdraw(200, "1234")
account.withdraw(5000, "1234")  # Should fail


print("\n=== Changing PIN ===")
account.change_pin("1234", "9999")
print(account.get_balance("1234"))  # Old PIN - fails
print(account.get_balance("9999"))  # New PIN - works


# ============================================
# Name Mangling (Advanced)
# ============================================
print("\n=== Name Mangling Demo ===")
print("Private attributes are actually renamed:")
print(f"Actual balance attribute: {account._BankAccount__balance}")  # Works but BAD practice!
print("This is called 'name mangling' - DON'T DO THIS in real code!")
