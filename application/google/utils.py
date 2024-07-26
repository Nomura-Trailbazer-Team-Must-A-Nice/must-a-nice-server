import json

from requests_oauthlib import OAuth2Session
from flask import session

def get_google_client():
    with open('./application/auth/client_secret_111215959056-ajrsif3algjo4o02qs77poqrh77lajgi.apps.googleusercontent.com.json') as f:
            secrets = json.load(f)
            f.close()
    tokens = session.get('google_tokens')
    client_id = secrets['web']['client_id']
    refresh_url = secrets['web']['token_uri']
    client_secret = secrets['web']['client_secret']

    extra = {
        'client_id': client_id,
        'client_secret': client_secret,
    }

    oauth = OAuth2Session(client_id, token=tokens, auto_refresh_url=refresh_url, 
                          auto_refresh_kwargs=extra, token_updater=lambda token: session.update(token))
    
    return oauth
