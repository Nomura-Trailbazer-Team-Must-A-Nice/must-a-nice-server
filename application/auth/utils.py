from flask import session

from application.mongodb.user import User

def get_or_create_user(idinfo):
    if not (user := User.objects(email=idinfo.get('email')).first()):
        user = User(email=idinfo.get('email'), first_name=idinfo.get('given_name'), last_name=idinfo.get('family_name'))
        user.save()
    return user

def save_token(access_token):
    session['google_access_token'] = access_token