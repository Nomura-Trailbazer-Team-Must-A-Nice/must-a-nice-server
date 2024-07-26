import logging
import json

from flask import Blueprint, request, jsonify, current_app, session
from flask_jwt_extended import create_refresh_token, create_access_token, jwt_required, get_jwt, get_jwt_identity, decode_token
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError

from application.mongodb.user import User
from application.mongodb.token_blocklist import TokenBlocklist
from application.auth.utils import get_or_create_user, save_token
from application.google.utils import get_google_client, create_google_event, get_google_calendar_availability
from application.common.utils import sync_google_with_s3

auth_bp = Blueprint("auth_v1", __name__, url_prefix="/api/auth")

def init_auth_views(bp):
    AuthController(bp)

class AuthController:
    def __init__(self, bp):
        @bp.route('/login', methods=['POST'])
        def login():
            # (Receive auth_code by HTTPS POST)
            auth_code = request.get_json().get('serverAuthCode')
            with open('./application/auth/client_secret_111215959056-ajrsif3algjo4o02qs77poqrh77lajgi.apps.googleusercontent.com.json') as f:
                secrets = json.load(f)
                f.close()
            client_id = "111215959056-iv8f05tp31s8m86h9ifhhqnr45mfvd4k.apps.googleusercontent.com"
            client_secret = "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"
            scopes = ['openid', 'https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/calendar', 'https://mail.google.com']

            google = OAuth2Session(client_id=client_id, scope=scopes)
            tokens = google.fetch_token(token_url='https://oauth2.googleapis.com/token', code=auth_code, client_secret=client_secret)
            session['google_tokens'] = tokens

            google_client = get_google_client()
            user_info = google_client.get('https://www.googleapis.com/oauth2/v1/userinfo').json()

            calendar_availability = get_google_calendar_availability()
            print(calendar_availability)

            free_time = create_google_event("Test", "Test")

            user = get_or_create_user(user_info)
            access_token = create_access_token(user)
            refresh_token = create_refresh_token(user)

            sync_google_with_s3(google_client, user)
            return jsonify({
                'access_token': access_token,
                'refresh_token': refresh_token
            })
        
        @bp.route('/test_login', methods=['GET'])
        def test_login():
            session['test'] = "Fuck this shit"
            return jsonify(True)
        
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

            session.pop('google_tokens', None)

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
        
        @bp.route("/test_google", methods=["POST"])
        @jwt_required()
        def test_google():
            with open('./application/auth/client_secret_111215959056-ajrsif3algjo4o02qs77poqrh77lajgi.apps.googleusercontent.com.json') as f:
                secrets = json.load(f)
                f.close()
            client_id = secrets['web']['client_id']
            token = session.get('google_tokens')
            try:
                google = OAuth2Session(client_id, token=token)
                user_info = google.get('https://www.googleapis.com/oauth2/v1/userinfo').json()
            except TokenExpiredError as e:
                token = google.refresh_token('https://oauth2.googleapis.com/token')
                save_token(token)
            google = OAuth2Session(client_id, token=token)
            user_info = google.get('https://www.googleapis.com/oauth2/v1/userinfo').json()
            return jsonify(user_info)
        
        @bp.route("/test_session", methods=["POST"])
        def test_session():
            test = session['test']
            return jsonify({
                'test': test
            })
