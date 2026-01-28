from flask import Flask, send_from_directory
from flask_cors import CORS
from app.extensions import mongo
from app.webhook.routes import webhook
import os


# Creating our flask app
def create_app():

    app = Flask(__name__, static_folder='static', static_url_path='/static')
    
    # Enable CORS
    CORS(app)
    
    # MongoDB Configuration
    app.config['MONGO_URI'] = 'mongodb+srv://m45474516_db_user:8vV6c2b3kxfjsGbr@techstax.kcay55h.mongodb.net/tech_stax'
    mongo.init_app(app)
    
    # Root route to serve index.html
    @app.route('/')
    def index():
        return send_from_directory(os.path.join(os.path.dirname(__file__), '..', 'static'), 'index.html')
    
    # registering all the blueprints
    app.register_blueprint(webhook)
    
    return app
