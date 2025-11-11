class Dog:
    #Class Variable - shared by all dogs
    species = "Canis familiaris"
    total_dogs = 0 #Track how many dogs are created

    def __init__(self, name, age):
        # Instance Variable - unique to each dog
        self.name = name
        self.age = age
     
        Dog.total_dogs += 1
 
    def info(self):
        print(f"{self.name} is a {self.age}- year-old {Dog.species}")

    @classmethod
    def get_total_dogs(cls):
        return f"Total dogs created: {cls.total_dogs}"

dog1 = Dog("Rex", 3)
dog2 = Dog("Max", 5)
dog3 = Dog("Bella", 2)


print("=== Instance Variables (Different for each) ===")
print(f"Dog 1: {dog1.name}, Age: {dog1.age}")
print(f"Dog 2: {dog2.name}, Age: {dog2.age}")


print("\n=== Class Variables (Same for all) ===")
print(f"Dog 1 species: {dog1.species}")
print(f"Dog 2 species: {dog2.species}")
print(f"Dog 3 species: {dog3.species}")


print("\n=== Class Variable Tracking ===")
print(Dog.get_total_dogs())


# What happens if we change class variable?
Dog.species = "Canis lupus familiaris"
print("\n=== After Changing Class Variable ===")
print(f"Dog 1 species: {dog1.species}")  # All dogs affected!
print(f"Dog 2 species: {dog2.species}")

