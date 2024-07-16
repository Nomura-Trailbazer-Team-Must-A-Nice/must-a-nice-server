from flask import Flask

from config import BaseConfig
from application.configure_extensions import configure_extensions
from application.mongodb.user import User

def create_app(config_class=BaseConfig):
    flask_app = Flask(__name__, static_url_path='/static')
    flask_app.config.from_object(config_class)
    db = configure_extensions(flask_app)

    @flask_app.route('/api/test_create_user')
    def test_create_user():
        User(email="example@mail.com", first_name="Test user").save()
        return "Success"
    
    return flask_app, db