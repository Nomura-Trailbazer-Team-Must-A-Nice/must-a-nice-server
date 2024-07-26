import json

from datetime import datetime, timezone

from requests_oauthlib import OAuth2Session
from flask import session

from application.common.utils import find_free_time
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/presentations"
]

def authenticate():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

def create_and_update_document(document_template_id, summary, recommendation, workdone):
    creds = authenticate()
    try:
        docs_service = build("docs", "v1", credentials=creds)
        drive_service = build("drive", "v3", credentials=creds)
        
        # Copy the document
        copy_title = "Email Summary with Mr. Jimmy"
        copied_file = drive_service.files().copy(
            fileId=document_template_id,
            body={"name": copy_title}
        ).execute()
        
        copied_doc_id = copied_file.get('id')

        requests = [
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{summary}',
                        'matchCase': True,
                    },
                    'replaceText': summary
                }
            },
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{recommendation}',
                        'matchCase': True,
                    },
                    'replaceText': recommendation
                }
            },
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{workdone}',
                        'matchCase': True,
                    },
                    'replaceText': workdone
                }
            }
        ]

        docs_service.documents().batchUpdate(
            documentId=copied_doc_id,
            body={'requests': requests}
        ).execute()

        document_link = f"https://docs.google.com/document/d/{copied_doc_id}/edit"
        return document_link

    except HttpError as err:
        print(err)
        return None

def create_and_update_presentation(presentation_template_id, summary, recommendation, workdone):
    creds = authenticate()
    try:
        slides_service = build("slides", "v1", credentials=creds)
        drive_service = build("drive", "v3", credentials=creds)
        
        # Copy the presentation
        copy_title = "Email Summary with Mr. Jimmy"
        copied_file = drive_service.files().copy(
            fileId=presentation_template_id,
            body={"name": copy_title}
        ).execute()
        
        copied_presentation_id = copied_file.get('id')

        # Define requests to replace placeholders in slides
        requests = [
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{summary}',
                        'matchCase': True,
                    },
                    'replaceText': summary
                }
            },
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{recommendation}',
                        'matchCase': True,
                    },
                    'replaceText': recommendation
                }
            },
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{workdone}',
                        'matchCase': True,
                    },
                    'replaceText': workdone
                }
            }
        ]
        
        # Update the copied presentation with the requests
        slides_service.presentations().batchUpdate(
            presentationId=copied_presentation_id,
            body={'requests': requests}
        ).execute()

        presentation_link = f"https://docs.google.com/presentation/d/{copied_presentation_id}/edit"
        return presentation_link

    except HttpError as err:
        print(err)
        return None
