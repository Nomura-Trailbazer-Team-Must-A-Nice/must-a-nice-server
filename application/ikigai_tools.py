import boto3
from datetime import datetime
import time
import pytz
import os

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
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), 
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

    email_history = """
    
    ---

    **Subject: Welcome to ABC Banking Services**

    ---

    **Email 1: Initial Outreach from You**

    *From:* You <your.email@example.com>  
    *To:* Customer <customer.email@example.com>  
    *Date:* July 10, 2024  
    *Subject:* Welcome to ABC Banking Services

    ---

    Dear [Customer's Name],

    I hope this email finds you well. My name is [Your Name], and I am a representative of ABC Banking Services. I am reaching out to you regarding our range of banking services that we believe could greatly benefit you.

    ABC Banking Services offers a variety of financial solutions tailored to meet the diverse needs of our clients. From personal banking to business accounts, loans, and investment services, we aim to provide exceptional service and value.

    We would love the opportunity to discuss how our services can align with your financial goals and needs. Could we schedule a meeting to explore this further? I am available for a call or an in-person meeting at your convenience.

    Please let me know your preferred date and time for the meeting, and I will do my best to accommodate your schedule.

    Thank you for considering ABC Banking Services. I look forward to your response.

    Best regards,

    [Your Name]  
    [Your Position]  
    ABC Banking Services  
    [Your Contact Information]

    ---

    **Email 2: Response from Customer**

    *From:* Customer <customer.email@example.com>  
    *To:* You <your.email@example.com>  
    *Date:* July 11, 2024  
    *Subject:* Re: Welcome to ABC Banking Services

    ---

    Dear [Your Name],

    Thank you for reaching out to me. I am interested in learning more about the services offered by ABC Banking Services.

    I am available for a meeting next week. Would July 15th at 2:00 PM work for you? If not, please suggest an alternative time.

    Looking forward to your confirmation.

    Best regards,

    [Customer's Name]

    ---

    **Email 3: Confirmation from You**

    *From:* You <your.email@example.com>  
    *To:* Customer <customer.email@example.com>  
    *Date:* July 11, 2024  
    *Subject:* Re: Welcome to ABC Banking Services

    ---

    Dear [Customer's Name],

    Thank you for your prompt response. July 15th at 2:00 PM works perfectly for me.

    We can meet at our main branch located at 123 Main Street, or we can arrange a call if that is more convenient for you. Please let me know your preference.

    I look forward to discussing how ABC Banking Services can support your financial needs.

    Best regards,

    [Your Name]  
    [Your Position]  
    ABC Banking Services  
    [Your Contact Information]

    ---

    **Email 4: Final Details from Customer**

    *From:* Customer <customer.email@example.com>  
    *To:* You <your.email@example.com>  
    *Date:* July 12, 2024  
    *Subject:* Re: Welcome to ABC Banking Services

    ---

    Dear [Your Name],

    Thank you for confirming the meeting. I would prefer to meet in person at your main branch on July 15th at 2:00 PM.

    Looking forward to our meeting.

    Best regards,

    [Customer's Name]

    ---

    **Email 5: Meeting Reminder from You**

    *From:* You <your.email@example.com>  
    *To:* Customer <customer.email@example.com>  
    *Date:* July 14, 2024  
    *Subject:* Reminder: Meeting on July 15th at 2:00 PM

    ---

    Dear [Customer's Name],

    This is a friendly reminder for our meeting scheduled on July 15th at 2:00 PM at our main branch located at 123 Main Street.

    If you have any questions or need to reschedule, please let me know.

    Looking forward to our discussion.

    Best regards,

    [Your Name]  
    [Your Position]  
    ABC Banking Services  
    [Your Contact Information]

    ---
    """
        # Inference parameters to use.
    temperature = 0.5

    model_id = "anthropic.claude-3-haiku-20240307-v1:0"
    system_prompts = [
        {"text": "You are an app that creates summaries of email conversation histories."}
    ]
    message_1 = {
        "role": "user",
        "content": [{"text": f"Summarize the following text: {email_history}."}],
    }
    messages = [message_1]

    # Base inference parameters to use.
    inference_config = {"temperature": temperature}

    # Send the message.
    response = bedrock_runtime.converse(
        modelId=model_id,
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
        # additionalModelRequestFields=additional_model_fields,
    )
    text_response = response["output"]["message"]["content"][0]["text"]
    end_time = time.time()
    print(f"Time taken to summarize email history: {end_time - start_time} seconds.")
    return text_response

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
