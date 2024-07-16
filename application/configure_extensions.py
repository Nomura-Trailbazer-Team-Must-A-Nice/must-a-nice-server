import datetime

from flask_cors import CORS
from flask_mongoengine import MongoEngine
from flask_login import LoginManager
from flask_jwt_extended import JWTManager

def configure_extensions(app):
    # CORS with allow credentials
    # CORS(app,
    #      origins=app.config['CORS_ORIGINS'],
    #      supports_credentials=True)

    # connect mongodb
    db = MongoEngine(app)

    # flask JWT configuration
    app.config["JWT_SECRET_KEY"] = app.config['JWT_SECRETS']
    app.config["JWT_ALGORITHM"] = app.config['JWT_ALGORITHM']
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(days=3)
    jwt = JWTManager(app)

    # flask login
    from flask_login import LoginManager
    login = LoginManager(app)

    return db
