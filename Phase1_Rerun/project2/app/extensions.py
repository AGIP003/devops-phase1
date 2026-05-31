from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()
from flask_mail import Mail
mail = Mail()
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["20000 per day", "5000 per hour"],
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
    )
from flask_cors import CORS
