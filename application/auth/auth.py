import logging

from flask import Blueprint, request, jsonify, current_app, session
from flask_jwt_extended import create_refresh_token, create_access_token, jwt_required, get_jwt, get_jwt_identity, decode_token
from google.oauth2 import id_token
from google.auth.transport import requests

from application.mongodb.user import User
from application.mongodb.token_blocklist import TokenBlocklist
from application.auth.utils import get_or_create_user

auth_bp = Blueprint("auth_v1", __name__, url_prefix="/api/auth")

def init_auth_views(bp):
    AuthController(bp)

class AuthController:
    def __init__(self, bp):
        @bp.route('/login', methods=['POST'])
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
        
        @bp.route('/logout', methods=['DELETE'])
        @jwt_required()
        def logout():
            access_jti = get_jwt().get('jti')

            try:
                refresh_jti = decode_token(request.get_json().get('refresh_token'))['jti']
            except Exception as e:
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
        
        @bp.route("/refresh", methods=["POST"])
        @jwt_required(refresh=True)
        def refresh():
            identity = get_jwt_identity()
            user = User.objects(email=identity).first()
            access_token = create_access_token(identity=user)
            return jsonify({
                'access_token': access_token
            })
    