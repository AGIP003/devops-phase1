
num = int(input("Kindly key in a number:"))
for i in range (11):
    
    total =  num * i
    
    print(f"{num} * {i} = {total}")

amount = 14.21
if round(amount, 2) != amount:
    print(f"Error: {amount} has more than 2dp")
else:
    print(f"{amount} has 2 dp or fewer")