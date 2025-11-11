class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        print ("Animal speaks")

class Dog(Animal):
    def speak(self):
        print (f"{self.name}: Woof!")

class Cat(Animal):
    def speak(self):
        print (f"{self.name}: Meow!")

class Cow(Animal):
    def speak(self):
        print (f"{self.name}: Moo!")

animals = [
    Dog("Rex"),
    Cat("Whiskers"),
    Cow("Bessie")
]

for animal in animals:
    animal.speak() 
