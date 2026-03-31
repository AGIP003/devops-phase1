from app import create_app
from flask_cors import CORS

app = create_app()        
if __name__ == "__main__":
    app.run(ssl_context=('cert.pem', 'key.pem'))