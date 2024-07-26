import boto3
from datetime import datetime
import time
import pytz
import os
from application.google.utils import create_and_update_document, create_and_update_presentation

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
    token_usage = response["usage"]
    print(f"Input tokens: {token_usage['inputTokens']}")
    print(f"Output tokens: {token_usage['outputTokens']}")
    print(f"Total tokens: {token_usage['totalTokens']}")
    print(f"Stop reason: {response['stopReason']}")

    text_response = response["output"]["message"]["content"][0]["text"]

    return text_response

def summarize_email_history(email_id):
    """
    Summarizes an email history using a generative AI model.
    Args:
        email_id (str): The email ID of the user to summarize.
    Returns:
        summary (str): The summarized email history.
    """
    # extract email history from S3 bucket, for now using a placeholder
    start_time = time.time()

    s3_client = boto3.client(
        service_name="s3",
        region_name="us-east-1",
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), 
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

    bucket_name = "ikigai-emails-66a2929acaf08306921c9ed9"
    email_history = "This is a placeholder for the email history." # TODO: get from s3
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    system_prompts = [
        {"text": "You are an app that creates summaries of email conversation histories."}
    ]
    message_1 = {
        "role": "user",
        "content": [{"text": f"Summarize the following text: {email_history}."}],
    }
    messages = [message_1]

    summarized_email = generate_conversation(model_id, system_prompts, messages)
    end_time = time.time()
    print(f"Time taken to summarize email history: {end_time - start_time} seconds.")
    return summarized_email

def get_calendar_availability():
    """
    Gets the calendar availability of a user using Google API.
    Returns:
        calendar_availability (str): The calendar availability of the user.
    """
    pass

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

def generate_meeting_brief(email_id):
    """
    Generates a meeting brief based on the user's email history and calendar availability.
    Args:
        email_id (str): The email ID of the user.
    Returns:
        meeting_brief (str): The generated meeting brief.
    """

    email_history = None # TODO: get from S3

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

    document_template_id = "16apEd2r6HGvgcBTJIRfXWz_wtbRlVGeAyaZpa1GHozM"
    presentation_template_id = "1_pbE-1CLeEzwS-6E2mO_zAH2L83rmtngWXLGwWrvqGA"
    summary = summarize_email_history(email_id)
    recommendation = generate_conversation(model_id, system_prompts_recommendation, messages_recommendation)
    workdone = generate_conversation(model_id, system_prompts_work, messages_work)
    
    doc_link = create_and_update_document(document_template_id, summary, recommendation, workdone)
    if doc_link:
        print(f"The link to the new document is: {doc_link}")

    pres_link = create_and_update_presentation(presentation_template_id, summary, recommendation, workdone)
    if pres_link:
        print(f"The link to the new presentation is: {pres_link}")
    pass
