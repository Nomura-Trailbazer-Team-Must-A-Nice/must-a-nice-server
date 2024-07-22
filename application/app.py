from flask import Flask, request, jsonify, current_app
import boto3
import os
from dotenv import load_dotenv
import random
import string
import logging
from flask_jwt_extended import create_access_token, current_user
from google.oauth2 import id_token
from google.auth.transport import requests

from config import BaseConfig
from application.configure_extensions import configure_extensions
from application.mongodb.user import User

def create_app(config_class=BaseConfig):
    flask_app = Flask(__name__, static_url_path='/static')
    flask_app.config.from_object(config_class)
    db = configure_extensions(flask_app)

    def process_response(response):
        print('\nprocess_response', response)

        completion = ''
        return_control_invocation_results = []

        for event in response.get('completion'):

            if 'returnControl' in event:
                return_control = event['returnControl']
                print('\n- returnControl', return_control)
                invocation_id = return_control['invocationId']
                invocation_inputs = return_control['invocationInputs']

                print(f"\nInvocation Inputs: {invocation_inputs}")

                for invocation_input in invocation_inputs:
                    function_invocation_input = invocation_input['functionInvocationInput']
                    action_group = function_invocation_input['actionGroup']
                    function = function_invocation_input['function']
                    parameters = function_invocation_input['parameters']
                    print(f"\nAction Group: {action_group}, Function: {function}")
                    if action_group == 'core-crm-actions' and function == 'schedule_meeting':
                        print("SCHEDULED MEETING CALLED")
                        return_control_invocation_results.append( {
                            'functionResult': {
                                'actionGroup': action_group,
                                'function': function,
                                'responseBody': {
                                    'TEXT': {
                                        'body': '{ "customer id": 12345 }' # Simulated API
                                    }
                                }
                            }}
                        )
                    if action_group == 'core-crm-actions' and function == 'summarized_email_thread':
                        print("SUMMARIZED EMAIL CALLED")
                        return_control_invocation_results.append( {
                            'functionResult': {
                                'actionGroup': action_group,
                                'function': function,
                                'responseBody': {
                                    'TEXT': {
                                        'body': '{ "customer id": 12345 }' # Simulated API
                                    }
                                }
                            }}
                        )
            
            elif 'chunk' in event:
                chunk = event["chunk"]
                print('\n- chunk', chunk)
                completion = completion + chunk["bytes"].decode()
            
            elif 'trace' in event:
                trace = event["trace"]
                print('\n- trace', trace)

            else:
                print('\nevent', event)

        if len(completion) > 0:
            print('\ncompletion\n')
            print(completion)

        if len(return_control_invocation_results) > 0:
            print('\n- returnControlInvocationResults', return_control_invocation_results)
            new_response = bedrock_agent_runtime.invoke_agent(
                enableTrace=True,
                agentId=os.environ['IKIGAI_AGENT_ID'],
                agentAliasId=os.environ['IKIGAI_AGENT_ALIAS_ID'],
                sessionId=session_id,
                sessionState={
                    'invocationId': invocation_id,
                    'returnControlInvocationResults': return_control_invocation_results
                },
            )
            process_response(new_response)


    @flask_app.route('/api/test_create_user')
    def test_create_user():
        User(email="example@mail.com", first_name="Test user").save()
        return "Success"
    
    @flask_app.route('/api/handle_user_prompt', methods=['POST'])
    def handle_user_prompt():
        data = request.json
        prompt = data.get('prompt')

        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400

        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
        session_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        first_response = bedrock_agent_runtime.invoke_agent(
            enableTrace=True,
            agentId=os.environ['IKIGAI_AGENT_ID'],
            agentAliasId=os.environ['IKIGAI_AGENT_ALIAS_ID'],
            sessionId=session_id,
            inputText=prompt,
        )

        process_response(first_response)

        return jsonify({'message': 'Prompt processed successfully', 'session_id': session_id}), 200

    return flask_app, db

load_dotenv()

if __name__ == '__main__':
    app, db = create_app()
    app.run(debug=True)

    def get_or_create_user(idinfo):
        if not (user := User.objects(email=idinfo.get('email')).first()):
            user = User(email=idinfo.get('email'), first_name=idinfo.get('given_name'), last_name=idinfo.get('family_name'))
            user.save()
        return user
    
    @flask_app.route('/api/token_verification', methods=['POST'])
    def token_verification():
        token = request.get_json().get('token')
        client_id = current_app.config["GOOGLE_WEBCLIENT_ID"]

        idinfo = id_token.verify_oauth2_token(token, requests.Request(), client_id)
        user = get_or_create_user(idinfo)
        token = create_access_token(user)
        return jsonify({
            'user': user.to_dict(),
            'token': token
        })
