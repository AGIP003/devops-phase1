class ShoppingCart:
    
    def __init__(self, customer_name):
        self.customer_name = customer_name
        #self.customer_total_items = customer_total_items
        self.items = {}
  
    def add_item(self, item_name, quantity, price):
        """Adding items to the cart """
        if  quantity <= 0:
            raise ValueError("Quantity must be positive!")
        self.items[item_name] = {'quantity':quantity, 'price': price}
            

    def remove_item(self, item_name):
        """Removing Items from the cart"""
        self.items.pop(item_name, None)
        

    def get_total(self):
        """Getting total price of items in the cart"""
        total = 0
        for item_name, data in self.items.items():
            total += data['price'] * data['quantity']
        return total
    
    def display_cart(self):
        print(f"Customer Name: {self.customer_name}")
        print("Items:")
        for item_name, data in self.items.items():
            print(f" - {item_name}: {data['quantity']} x {data['price']}")
        print(f"Total: {self.get_total()}")

    #def display_cart(self):
    #    """Displaying the items in the cart"""
    #    for item_name, data in self.items.items():
    #            print (f"Customer Name: {self.customer_name}\n"
    #                   f"Item: {self.items}\n"
    #                   f"Total items: {self.get_total()}")
    
customer1 = ShoppingCart("Jonte")
customer1.add_item("Eno", 2, 100)
customer1.add_item("Banana", 13, 50)
customer1.add_item("Kiwi", 2, 150)

print(customer1.get_total())
customer1.display_cart()

customer2 = ShoppingCart ("Jose")
customer2.add_item("Eggs", 2, 100)
customer2.add_item("Banana", 13, 50)
customer2.add_item("Cheese", 2, 750)

customer2.display_cart()