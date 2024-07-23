from __future__ import annotations

import datetime
import mongoengine

from flask_cors import CORS
from flask_mongoengine import MongoEngine
from flask_login import LoginManager
from flask_jwt_extended import JWTManager

from application.mongodb.user import User
from application.mongodb.token_blocklist import TokenBlocklist
from application.common.exceptions import AuthenticationException

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
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(days=1)
    jwt = JWTManager(app)

    # flask login
    from flask_login import LoginManager
    login = LoginManager(app)

    # Flask session 
    app.config["SESSION_MONGODB"] = mongoengine.connection.get_connection().client

    @jwt.user_identity_loader
    def user_identity_lookup(identity: User):
        # Register a callback function that takes whatever object is passed in as the
        # identity when creating JWTs and converts it to a JSON serializable format.
        return identity.email
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        # Register a callback function that loads a user from your database whenever
        # a protected route is accessed. This should return any python object on a
        # successful lookup, or None if the lookup failed for any reason (for example
        # if the user has been deleted from the database).
        user_email = jwt_data['sub']

        user = User.objects(email=user_email).first()
        if user is None:
            raise AuthenticationException("User id provided is not valid.")

        return user
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_, jwt_payload: dict) -> bool:
        jti = jwt_payload["jti"]
        token = TokenBlocklist.objects(jti=jti).first()

        return token is not None

    return db
