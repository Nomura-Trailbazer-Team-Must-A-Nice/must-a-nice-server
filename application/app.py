import logging
from flask import Flask, request, current_app, jsonify
from flask_jwt_extended import create_access_token, current_user
from google.oauth2 import id_token
from google.auth.transport import requests

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
    
    def get_or_create_user(idinfo):
        if not (user := User.objects(email=idinfo.get('email')).first()):
            user = User(email=idinfo.get('email'), first_name=idinfo.get('given_name'), last_name=idinfo.get('family_name'))
            user.save()
        return user
    
    @flask_app.route('/api/token_verification', methods=['POST'])
    def token_verification():
        token = request.get_json().get('token')
        client_id = current_app.config["GOOGLE_WEBCLIENT_ID"]

        idinfo = id_token.verify_oauth2_token(token, requests.Request(), client_id)
        user = get_or_create_user(idinfo)
        token = create_access_token(user)
        return jsonify({
            'user': user.to_dict(),
            'token': token
        })
    
    return flask_app, db