class Vehicle:
    def __init__(self, speed):
        self.speed = speed

    def travel_time(self, distance):
        return distance / self.speed

class Car(Vehicle):
    pass

class Bike(Vehicle):
    def travel_time(self, distance):
        return distance / self.speed

Vehicles = [
    Car(60),
    Bike(15)
]

distance = 120

for vehicle in Vehicles:
    hours = vehicle.travel_time(distance)
    print(f"Travel time: {hours} hours")


