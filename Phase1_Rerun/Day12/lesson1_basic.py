class Dog:
    def __init__(self, name, breed, age):
        self.name = name
        self.breed = breed
        self.age = age
    #Method - a function inside a class
    def bark (self):
        print(f"{self.name} says: Woof! Woof!")

    def eat(self, food):
        print(f"{self.name} is eating {food}")

    def celebrate_birthday(self):
        self.age += 1
        print(f"Happy birthday {self.name}! You are now {self.age} years old.")

#creating Objects (instances)
 #Three different dogs
dog1 = Dog("Rex", "Golden Retriever", 3)
dog2 = Dog("Max", "Beagle", 5)
dog3 = Dog("Bella", "Poodle", 2)

#Use the objects
print("=== Dog 1 ===")
print(f"Name: {dog1.name}")
print(f"Breed: {dog1.breed}")
print(f"Age: {dog1.age}")
dog1.bark()
dog1.eat("kibble")

print("\n=== Dog 2 ===")
dog2.bark()
dog2.celebrate_birthday()

print("\n=== Dog 3 ===")
dog3.eat("treats")


class Person:
    def __init__(self, name, age, city):
        self.name = name
        self.age = age
        self.city = city

    def introduce(self):
       print(f"My name is: {self.name}")

    def have_birthday(self):
        self.age += 1
        print(f"Happy birthday {self.name} you are now turning {self.age} years old.")
 
    def move_to(self, new_city):
        print(f"{self.name} is moving from {self.city} to {new_city}")

#Creating objects
person1 = Person("Vera", 23, "Thika")
person2 = Person("Vee", 26, "Mirema")

#Using the objects
print ("\n=== Person 1 ===")
person1.introduce()
person1.have_birthday()
person1.move_to("Waiyaki_Way")


