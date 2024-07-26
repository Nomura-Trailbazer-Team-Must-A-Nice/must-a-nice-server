import json

from datetime import datetime, timezone

from requests_oauthlib import OAuth2Session
from flask import session

from application.common.utils import find_free_time

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

def get_google_calendar_availability():
    client = get_google_client()
    current_time = datetime.now(timezone.utc).isoformat()
    url = f'https://www.googleapis.com/calendar/v3/calendars/primary/events?singleEvents=true'
    calendar = client.get(url).json()
    user_timezone = calendar['timeZone']
    events = []
    while 'items' in calendar:
        for event in calendar['items']:
            events.append({
                'start': datetime.fromisoformat(event['start']['dateTime']),
                'end': datetime.fromisoformat(event['end']['dateTime'])
            })
        if 'nextPageToken' not in calendar:
            break
        calendar = client.get(f'https://www.googleapis.com/calendar/v3/calendars/primary/events?singleEvents=true&pageToken={calendar["nextPageToken"]}').json()
    return events, user_timezone

def create_google_event(title, description, client_availability=[]):
    client = get_google_client()
    my_availability, user_timezone = get_google_calendar_availability()
    meeting_time = find_free_time(my_availability, client_availability)
    event = {
        'summary': title,
        'description': description,
        'start': {
            'dateTime': meeting_time['start'].isoformat(),
            'timeZone': user_timezone
        },
        'end': {
            'dateTime': meeting_time['end'].isoformat(),
            'timeZone': user_timezone
        }
    }
    client.post('https://www.googleapis.com/calendar/v3/calendars/primary/events', json=event)
    return event