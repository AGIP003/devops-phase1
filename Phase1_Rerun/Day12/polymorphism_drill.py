class Car:
    def __init__(self, brand, price):
        self.brand = brand
        self.price = price



class Television:
    def __init__(self, brand, price, inches):
        self.brand = brand
        self.price = price
        self.inches = inches

tv = Television("LG", 300000, 55)
print(tv.brand)
print(tv.inches)

car = Car("Toyota", 20000)
print(car.brand)
print(car.price)

car2 = Car("Honda", 300000)
print(car.brand)
print(car.price)

