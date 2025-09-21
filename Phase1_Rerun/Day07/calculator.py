a = float(input("Enter a number: "))
b = float(input("Enter a second number: "))

operation = input("Kindly choose the sign: + - / * % ")

if operation == '+':
    print("Result:", a + b)
elif operation == '-':
    print("Result:", a - b)
elif operation == '*':
    print("Result:", a * b)
elif operation == '/':
    if b != 0:
        print("Result:", a / b)
    else:
        print("Math error!")
elif operation == '%':
    print("Result:", a % b)
else:
    print("Error! Kindly key in the correct sign")

 
