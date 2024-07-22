import logging
from flask import Flask, request, current_app, jsonify, session
from flask_jwt_extended import create_refresh_token, create_access_token, current_user, get_jwt_identity, jwt_required, get_jwt, decode_token
from flask_session import Session
from google.oauth2 import id_token
from google.auth.transport import requests

from config import BaseConfig
from application.configure_extensions import configure_extensions
from application.mongodb.user import User
from application.mongodb.token_blocklist import TokenBlocklist

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
    
    @flask_app.route('/api/login', methods=['POST'])
    def login():
        google_token = request.get_json().get('token')
        client_id = current_app.config["GOOGLE_WEBCLIENT_ID"]

        try:
            idinfo = id_token.verify_oauth2_token(google_token, requests.Request(), client_id)
        except ValueError as e:
            logging.error(e)
            return jsonify({
                'msg': "Invalid token"
            }), 400

        user = get_or_create_user(idinfo)
        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)
        session['google_token'] = google_token
        return jsonify({
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        })
    
    @flask_app.route('/api/logout', methods=['DELETE'])
    @jwt_required()
    def logout():
        access_jti = get_jwt().get('jti')

        try:
            refresh_jti = decode_token(request.get_json().get('refresh_token'))['jti']
        except:
            return jsonify({
                'msg': "Refresh token not passed in body or is invalid"
            }), 400

        try:
            TokenBlocklist(jti=access_jti).save()
        except Exception as e:
            logging.error(e)
            return jsonify({
                'msg': "Token is already revoked"
            }), 400
        
        try:
            TokenBlocklist(jti=refresh_jti).save()
        except Exception as e:
            logging.error(e)
            return jsonify({
                'msg': "Token is already revoked"
            }), 400

        session.pop('google_token', None)

        return jsonify({
            'msg': "You have successfully logged out"
        })
    
    @flask_app.route("/api/refresh", methods=["POST"])
    @jwt_required(refresh=True)
    def refresh():
        identity = get_jwt_identity()
        user = User.objects(email=identity).first()
        access_token = create_access_token(identity=user)
        return jsonify({
            'access_token': access_token
        })
    
    @flask_app.route("/api/test_session", methods=["GET"])
    @jwt_required()
    def test_session():
        return jsonify({
            'user': current_user.to_dict(),
            'msg': session['google_token']
        })
    
    return flask_app, db