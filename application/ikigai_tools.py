import boto3
from datetime import datetime
import time
import pytz
import os
import re
from application.google.utils import create_and_update_document, create_and_update_presentation, create_google_event, find_free_time

def generate_conversation(model_id, system_prompts, messages):
    """
    Sends messages to a model.
    Args:
        bedrock_client: The Boto3 Bedrock runtime client.
        model_id (str): The model ID to use.
        system_prompts (JSON) : The system prompts for the model to use.
        messages (JSON) : The messages to send to the model.

    Returns:
        response (JSON): The conversation that the model generated.

    """

    print(f"Generating message with model {model_id}")

    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), 
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

    # Inference parameters to use.
    temperature = 0.5

    # Base inference parameters to use.
    inference_config = {"temperature": temperature}
    # Additional inference parameters to use.
    # top_k = 200
    # additional_model_fields = {"top_k": top_k}

    # Send the message.
    response = bedrock_runtime.converse(
        modelId=model_id,
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
        # additionalModelRequestFields=additional_model_fields,
    )

    # Log token usage.
    # token_usage = response["usage"]
    # print(f"Input tokens: {token_usage['inputTokens']}")
    # print(f"Output tokens: {token_usage['outputTokens']}")
    # print(f"Total tokens: {token_usage['totalTokens']}")
    # print(f"Stop reason: {response['stopReason']}")

    text_response = response["output"]["message"]["content"][0]["text"]

    return text_response

def retrieve_email_history():
    def list_s3_buckets():
        s3 = boto3.client('s3')
        response = s3.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        return buckets

    def list_s3_objects(bucket_name):
        s3 = boto3.client('s3')
        response = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            objects = [obj['Key'] for obj in response['Contents']]
            return objects
        else:
            return []

    def read_text_from_s3(bucket_name, file_key):
        s3 = boto3.client('s3')
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        text = response['Body'].read().decode('utf-8')
        return text
    
    buckets = list_s3_buckets()

    email_history = ""

    for bucket in buckets:
        objects = list_s3_objects(bucket)

        for object in objects:
            text_content = read_text_from_s3(bucket, object)
            email_history += text_content

    return email_history

def summarize_email_history():
    """
    Summarizes an email history using a generative AI model.
    Args:
        email_id (str): The email ID of the user to summarize.
    Returns:
        summary (str): The summarized email history.
    """
    email_history = retrieve_email_history()
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    system_prompts = [
        {"text": "You are an app that creates summaries of email conversation histories."}
    ]
    message_1 = {
        "role": "user",
        "content": [{"text": f"Summarize the following text: {email_history}. Also include additional information such as the context of the email and explaining the relevant terms."}],
    }
    messages = [message_1]

    summarized_email = generate_conversation(model_id, system_prompts, messages)
    return summarized_email

def schedule_customer_meeting():
    """
    Schedules a meeting with a customer.
    """
    email_history = retrieve_email_history()
    customer_name = "Customer"
    pattern_name = r'From: "(.*?)" <'
    match_name = re.search(pattern_name, email_history)

    if match_name:
        customer_name = match_name.group(1)

    pattern_subject = r'Subject: (.*?)\n'
    match_subject = re.search(pattern_subject, email_history)

    if match_subject:
        subject = match_subject.group(1)

    event = create_google_event(f"Meeting with {customer_name}", subject)

    response = f"The meeting with {customer_name} about {subject} has been scheduled on your Google Calendar. The meeting will be held from {event['start']['dateTime']} until {event['end']['dateTime']} in the {event['start']['timeZone']} timezone."

    return response

def get_current_time():
    """
    Gets the current day, date, and time.
    Returns:
        current_time (str): The current time.
    """
    now = datetime.now(pytz.timezone('Asia/Singapore'))
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    current_day = now.strftime("%A")

    response = f"Today is {current_day}, {current_date}, and the current time is {current_time}."
    
    return response

def generate_meeting_brief():
    """
    Generates a meeting brief based on the user's email history and calendar availability.
    Args:
        email_id (str): The email ID of the user.
    Returns:
        meeting_brief (str): The generated meeting brief.
    """

    email_history = retrieve_email_history()

    model_id = "anthropic.claude-3-haiku-20240307-v1:0"

    system_prompts_recommendation = [
        {"text": "You are an app that reads through email conversation histories, and generates recommendations on what the user should do."}
    ]
    message_1_recommendation = {
        "role": "user",
        "content": [{"text": 
                     f"""You are given the email history between the user and the customer:
                     {email_history}.
                     Based on this email history, generate a recommendation on what the user should do next.
                     """
                     }],
    }
    messages_recommendation = [message_1_recommendation]

    system_prompts_work = [
        {"text": "You are an app that reads through email conversation histories, and summarizes the work the user has done."}
    ]
    message_1_work = {
        "role": "user",
        "content": [{"text": 
                     f"""You are given the email history between the user and the customer:
                     {email_history}.
                     Based on this email history, summarize the work the user has done.
                     """
                     }],
    }
    messages_work = [message_1_work]

    # document_template_id = "16apEd2r6HGvgcBTJIRfXWz_wtbRlVGeAyaZpa1GHozM"
    # presentation_template_id = "1_pbE-1CLeEzwS-6E2mO_zAH2L83rmtngWXLGwWrvqGA"
    summary = summarize_email_history()
    recommendation = generate_conversation(model_id, system_prompts_recommendation, messages_recommendation)
    workdone = generate_conversation(model_id, system_prompts_work, messages_work)
    # doc_link = create_and_update_document(document_template_id, summary, recommendation, workdone)
    # pres_link = create_and_update_presentation(presentation_template_id, summary, recommendation, workdone)
    # response = f"The meeting brief has been generated. You can view the document [here]({doc_link}) and the presentation [here]({pres_link})."
    # return response
    meeting_brief = f"""Meeting Brief:
    Summary: {summary}
    Recommendation: {recommendation}
    Work Done: {workdone}
    """
    return meeting_brief
