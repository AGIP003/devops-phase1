class Calculator:
    def operate(self, a, b):
        return 0

class Adder(Calculator):
   def operate(self, a, b):
        # FIX: Return a + b (not print)
        return a + b

class Multiplier(Calculator):
    def operate(self, a, b):
        # FIX: Return a * b (not print)  
        return a * b

class Divider(Calculator):
    def operate(self, a, b):
        return a / b

# TEST
calcs = [
    Adder(), 
    Multiplier(),
    Divider()
]

for calc in calcs:
    result = calc.operate(5, 3)  # Should get 8 and 15
    print(f"Result: {result}")
