from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()
from flask_mail import Mail
mail = Mail()
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
    #storage_uri="memory://"
    )