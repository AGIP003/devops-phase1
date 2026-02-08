def add(x, y):
    return x + y

def subtract(x, y):
    return x - y

def multiply(x, y):
    return x * y

print("Simple CLI calculator")  
a = float(input("Enter first number: "))
b = float(input("Enter second number: "))  

print(f"Sum: {add(a, b)}")
print(f"Difference: {subtract(a, b)}")
print(f"Multiplication: {multiply(a, b)}")


