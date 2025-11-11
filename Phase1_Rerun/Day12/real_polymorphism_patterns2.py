class Notification:
    def send(self, message):
        pass

class Email(Notification):
    def send(self, message):
        # Simulate email logic
        return f"EMAIL: {message} [sent via SMTP]"

class SMS(Notification):
    def send(self, message):
        # Simulate SMS logic  
        return f"SMS: {message} [sent via Twilio]"

# USAGE
notifications = [Email(), SMS()]
for notification in notifications:
    result = notification.send("Hello World")  # Polymorphism!
    print(result)
