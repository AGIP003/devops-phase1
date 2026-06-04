from flask import Flask
from flask_mail import Mail, Message
from config import get_config

app = Flask(__name__)
app.config.from_object(get_config())
mail = Mail(app)

with app.app_context():
    msg = Message('Test Email', recipients=['blessedmuchemi@gmail.com'])
    msg.body = "Test email from Flask."
    mail.send(msg)
    print("Email sent successfully")