class Vehicle:
    """Base class for all vehicles."""
    
    def __init__(self, brand, year, price):
        self.brand = brand
        self.year = year
        self.price = price
    
    def display_info(self):
        """Display vehicle information - to be overridden by subclasses."""
        return f"{self.year} {self.brand} - ${self.price:,.2f}"
    
    def show_info(self):
        """Alias for display_info - maintain consistency."""
        return self.display_info()


class Car(Vehicle):
    """Car class with door count."""
    
    def __init__(self, brand, year, price, num_doors):
        super().__init__(brand, year, price)
        self.num_doors = num_doors
    
    def honk(self):
        """Car-specific method."""
        print(f"🚗 {self.brand} goes HONK HONK!")
    
    def display_info(self):
        """Override to include car-specific details."""
        base_info = super().display_info()
        return f"{base_info} | {self.num_doors} doors"


class Motorcycle(Vehicle):
    """Motorcycle class with sidecar information."""
    
    def __init__(self, brand, year, price, has_sidecar):
        super().__init__(brand, year, price)
        self.has_sidecar = has_sidecar
    
    def wheelie(self):
        """Motorcycle-specific method with proper logic."""
        if self.has_sidecar:
            print(f"❌ {self.brand} motorcycle cannot wheelie with a sidecar!")
        else:
            print(f"🏍️  {self.brand} motorcycle pops a wheelie!")
    
    def display_info(self):
        """Override to include motorcycle-specific details."""
        base_info = super().display_info()
        sidecar_status = "with sidecar" if self.has_sidecar else "without sidecar"
        return f"{base_info} | {sidecar_status}"


class Truck(Vehicle):
    """Truck class with cargo capacity."""
    
    def __init__(self, brand, year, price, cargo_capacity):
        super().__init__(brand, year, price)
        self.cargo_capacity = cargo_capacity  # in kg
    
    def load_cargo(self):
        """Truck-specific method."""
        print(f"🚛 {self.brand} truck loading {self.cargo_capacity:,} kg of cargo!")
    
    def display_info(self):
        """Override to include truck-specific details."""
        base_info = super().display_info()
        return f"{base_info} | {self.cargo_capacity:,} kg capacity"


# Test the hierarchy properly
if __name__ == "__main__":
    print("=" * 50)
    print("VEHICLE HIERARCHY DEMO")
    print("=" * 50)
    
    # Create instances with correct syntax
    car = Car("Ferrari", 2002, 200000, 2)           # No $ symbol, proper syntax
    motorcycle = Motorcycle("Honda", 2003, 15000, True)
    truck = Truck("FAW", 2010, 40000, 20000)
    
    # Test each vehicle
    print("\n🚗 CAR:")
    print(car.display_info())
    car.honk()
    
    print("\n🏍️  MOTORCYCLE:")
    print(motorcycle.display_info())
    motorcycle.wheelie()
    
    print("\n🚛 TRUCK:")
    print(truck.display_info())
    truck.load_cargo()
    
    # Demonstrate polymorphism
    print("\n" + "=" * 50)
    print("POLYMORPHISM DEMO - Same interface, different behavior")
    print("=" * 50)
    
    vehicles = [car, motorcycle, truck]
    
    for vehicle in vehicles:
        print(f"\n{vehicle.display_info()}")
        # Each vehicle type behaves differently
        if isinstance(vehicle, Car):
            vehicle.honk()
        elif isinstance(vehicle, Motorcycle):
            vehicle.wheelie()
        elif isinstance(vehicle, Truck):
            vehicle.load_cargo()
