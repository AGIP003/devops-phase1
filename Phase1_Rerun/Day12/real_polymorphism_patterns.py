class Payment:
    def process(self, amount):
        pass

class CreditCard(Payment):
    def process(self, amount):
        fee = amount * 0.02
        return amount + fee

class PayPal(Payment):
    def process(self, amount):
        fee = amount * 0.03
        return amount + fee

payments = [
    CreditCard(),
    PayPal()
]


for payment in payments:
    total = payment.process(100)
    print(f"Total: ${total:.2f}")
