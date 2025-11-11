# Level 1: Base Class
class Animal:
    def __init__(self, name):
        self.name = name
        print(f"Animal.__init__ called for {name}")

    def eat(self):
        print(f"{self.name} is eating")

    def breathe(self):
        print(f"{self.name} is breathing")

# LEVEL 2: Inherits from Animal
class Mammal(Animal):
    def __init__(self, name, fur_color):
        super().__init__(name)
        self.fur_color = fur_color
        print(f"Mammal.__init__ called - fur color: {fur_color}")

    def give_birth(self):
        print(f"{self.name} gives live birth")
    
    def produce_milk(self):
        print(f"{self.name} produces milk")

# LEVEL 3: Inherits from Mammal (which inherits from Animal)
class Dog(Mammal):
    def __init__(self, name, fur_color, breed):
        super().__init__(name, fur_color)
        self.breed = breed
        print(f"Dog.__init__ called - breed: {breed}")
    
    def bark(self):
        print(f"{self.name} says: Woof!")
    
    def wag_tail(self):
        print(f"{self.name} is wagging its tail")


print("=== Creating a Dog (Watch the Constructor Chain) ===")
dog = Dog("Rex", "Golden", "Golden Retriever")

print("\n=== Dog Can Access ALL Parent Methods ===")
dog.breathe()       # From Animal (grandparent)
dog.eat()           # From Animal (grandparent)
dog.give_birth()    # From Mammal (parent)
dog.produce_milk()  # From Mammal (parent)
dog.bark()          # From Dog (itself)
dog.wag_tail()      # From Dog (itself)

print("\n=== Attributes from All Levels ===")
print(f"Name: {dog.name}")           # From Animal
print(f"Fur Color: {dog.fur_color}") # From Mammal
print(f"Breed: {dog.breed}")         # From Dog
