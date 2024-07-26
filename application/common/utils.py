import boto3

from datetime import timedelta

from datetime import timedelta

from base64 import urlsafe_b64decode 

def sync_google_with_s3(client, user):
    s3_client = boto3.client('s3')
    bucket = s3_client.create_bucket(Bucket=f'ikigai-emails-{user.id}')
    s3_resoruce = boto3.resource('s3')
    bucket = s3_resoruce.Bucket(f'ikigai-emails-{user.id}')
    bucket.objects.all().delete()
    threads = client.get('https://www.googleapis.com/gmail/v1/users/me/threads?q=after:2024/01/01 is:important OR is:starred').json()
    while 'threads' in threads:
        for thread in threads['threads']:
            thread_id = thread['id']
            messages = client.get(f'https://www.googleapis.com/gmail/v1/users/me/threads/{thread_id}').json()
            message_contents = []

            for message in messages['messages']:
                message_content = {}
                if 'payload' in message:
                    for header in message['payload']['headers']:
                        if header['name'] == 'Date':
                            message_content['date'] = header['value']
                        if header['name'] == 'From':
                            message_content['from'] = header['value']
                        if header['name'] == 'Subject':
                            message_content['subject'] = header['value']
                        if header['name'] == 'To':
                            message_content['to'] = header['value']

                    if message['payload']['mimeType'] == 'multipart/alternative':
                        for part in message['payload']['parts']:
                            if part['mimeType'] == 'text/plain':
                                message_content['body'] = urlsafe_b64decode(part['body']['data']).decode()
                    else:
                        for part in message['payload']['parts']:
                            if part['mimeType'] == 'multipart/alternative':
                                for subpart in part['parts']:
                                    if subpart['mimeType'] == 'text/plain':
                                        message_content['body'] = urlsafe_b64decode(subpart['body']['data']).decode()

                    message_contents.append(message_content)
            
            if message_contents:
                subject = message_contents[0]['subject']
                date = message_contents[0]['date']
                out_str = f"Subject: {subject}\n\n"
                for message in message_contents:
                    out_str += f"From: {message['from']}\n"
                    out_str += f"To: {message['to']}\n"
                    out_str += f"Date: {message['date']}\n"
                    out_str += f"Subject: {message['subject']}\n"
                    out_str += f"Body: {message.get('body')}\n\n"

                s3_client.put_object(Bucket=f'ikigai-emails-{user.id}', Key=f'{subject}-{date}.txt', Body=out_str)
        if 'nextPageToken' not in threads:
            break
        threads = client.get(f'https://www.googleapis.com/gmail/v1/users/me/threads?q=after:2024/01/01 is:important OR is:starred&pageToken={threads["nextPageToken"]}').json()
    return

def find_free_time(events1, events2):              
    events = events1 + events2
    events.sort(key=lambda x: x['start'])
    free_times = []
    last_end = events[0]['end']
    for event in events[1:]:
        if event['start'] > last_end:
            free_times.append({
                'start': last_end,
                'end': event['start']
            })
        if event['end'] > last_end:
            last_end = event['end']
    for free_time in free_times:
        if free_time['end'] - free_time['start'] >= timedelta(hours=1.5):
            return {'start': free_time['start'] + timedelta(minutes=15), 'end': free_time['start'] + timedelta(minutes=75)}
    return None