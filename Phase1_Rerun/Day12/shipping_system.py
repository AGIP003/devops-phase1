class Shipping:
    def calculate_cost(self, weight, distance):
        pass

class StandardShipping(Shipping):
    def calculate_cost(self, weight, distance):
        return (weight * 3) + (distance * 0.20)

class ExpressShipping(Shipping):
    def calculate_cost(self, weight, distance):
        return (weight * 5) + (distance * 0.50)

class SeaShipping(Shipping):
    def calculate_cost(self, weight, distance):
        return (weight * 1) + (distance * 0.10)

shipping_methods = [
    StandardShipping(),
    ExpressShipping(),
    SeaShipping()
]

package = {"weight": 200, "distance": 1000}

for method in shipping_methods:
    cost = method.calculate_cost(package["weight"], package["distance"])

    print(f"Cost: ${cost:.2f}")

