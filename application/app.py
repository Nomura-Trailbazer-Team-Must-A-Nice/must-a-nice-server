import boto3
import os
import random
import string

from flask import Flask, request, jsonify

from config import BaseConfig
from application.configure_extensions import configure_extensions
from application.auth.auth import auth_bp, init_auth_views
from ikigai_tools import summarize_email_history, get_calendar_availability, get_current_time

def create_app(config_class=BaseConfig):
    flask_app = Flask(__name__, static_url_path='/static')
    flask_app.config.from_object(config_class)
    db = configure_extensions(flask_app)

    init_auth_views(auth_bp)
    flask_app.register_blueprint(auth_bp)

    def process_response(response, bedrock_agent_runtime, session_id):
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
                    if action_group == 'core-crm-actions' and function == 'summarize_email_history':
                        summarized_email_history = None
                        email_id = None
                        for param in parameters:
                            if param['name'] == 'email_id':
                                email_id = param['value']
                        if email_id:
                            summarized_email_history = summarize_email_history(email_id)
                        return_control_invocation_results.append( {
                            'functionResult': {
                                'actionGroup': action_group,
                                'function': function,
                                'responseBody': {
                                    'TEXT': {
                                        'body': '{ "summarized email history" : ' + str(summarized_email_history) + ' }'
                                    }
                                }
                            }}
                        )
                    if action_group == 'core-crm-actions' and function == 'get_calendar_availability':
                        calendar_availability = get_calendar_availability()
                        return_control_invocation_results.append( {
                            'functionResult': {
                                'actionGroup': action_group,
                                'function': function,
                                'responseBody': {
                                    'TEXT': {
                                        'body': '{ "calendar availability": ' + str(calendar_availability) + ' }'
                                    }
                                }
                            }}
                        )

                    if action_group == 'core-crm-actions' and function == 'get_current_time':
                        current_time = get_current_time()
                        return_control_invocation_results.append( {
                            'functionResult': {
                                'actionGroup': action_group,
                                'function': function,
                                'responseBody': {
                                    'TEXT': {
                                        'body': '{ "current time": ' + str(current_time) + ' }'
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
            print("New Response ", new_response)
            process_response(new_response, bedrock_agent_runtime, session_id)
    
    @flask_app.route('/api/handle_user_prompt', methods=['POST'])
    def handle_user_prompt():
        data = request.json
        prompt = data.get('prompt')

        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400

        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
        session_id = "NOMURAWIN8" # ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        first_response = bedrock_agent_runtime.invoke_agent(
            enableTrace=True,
            agentId=os.environ['IKIGAI_AGENT_ID'],
            agentAliasId=os.environ['IKIGAI_AGENT_ALIAS_ID'],
            sessionId=session_id,
            inputText=prompt,
        )

        process_response(first_response, bedrock_agent_runtime, session_id)

        return jsonify({'message': 'Prompt processed successfully', 'session_id': session_id}), 200
    
    return flask_app, db