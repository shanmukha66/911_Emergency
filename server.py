from flask import Flask, request, jsonify
import json
import os
import logging
import asyncio
from twilio.twiml.voice_response import VoiceResponse
from agents.transcript_agent_minimax.twilio_handler import TwilioHandler
from agents.fetch_agent import emergency_protocol, emergency_agent
from twilio.request_validator import RequestValidator
from dotenv import load_dotenv
from functools import wraps
import threading
import urllib.parse

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
twilio_handler = TwilioHandler()

# Twilio request validator
validator = RequestValidator(os.getenv('TWILIO_AUTH_TOKEN'))

# Path to the JSON file
json_file_path = "data.json"

def validate_twilio_request(f):
    """Validates that incoming requests genuinely originated from Twilio"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the full URL from the request
        forwarded_proto = request.headers.get('X-Forwarded-Proto', 'http')
        host = request.headers.get('X-Forwarded-Host', request.host)
        url = f"{forwarded_proto}://{host}{request.path}"
        
        # Log validation details for debugging
        logging.debug(f"Validating Twilio request for URL: {url}")
        logging.debug(f"Headers: {request.headers}")
        logging.debug(f"Form data: {request.form}")
        
        # X-Twilio-Signature header
        signature = request.headers.get('X-TWILIO-SIGNATURE', '')
        logging.debug(f"Twilio signature: {signature}")

        # Validate request
        if not validator.validate(url, request.form, signature):
            logging.error("Twilio request validation failed")
            return 'Invalid request', 403

        return f(*args, **kwargs)
    return decorated_function

# Initialize data file if it doesn't exist
if not os.path.exists(json_file_path):
    initial_data = {
        "wildlife": [],
        "police": [],
        "water": [],
        "fire": [],
        "medical": []
    }
    with open(json_file_path, 'w') as f:
        json.dump(initial_data, f)
    logging.info(f"Initialized data file at {json_file_path} with empty categories.")

@app.route('/voice', methods=['POST'])
@validate_twilio_request
def handle_call():
    """Handle incoming voice calls"""
    try:
        response = twilio_handler.handle_incoming_call()
        return response, 200
    except Exception as e:
        logging.error(f"Error handling call: {e}")
        return str(e), 500

@app.route('/voice/transcribe', methods=['POST'])
@validate_twilio_request
def handle_transcription():
    """Handle speech transcription results"""
    try:
        speech_result = request.form
        processed_data = twilio_handler.process_speech(speech_result)
        
        # Create a task to send data to emergency processing agent
        async def send_to_agent():
            await emergency_protocol.process_emergency(emergency_agent.context, processed_data)
        
        # Run the async task in the background
        asyncio.create_task(send_to_agent())
        
        # Create a response that doesn't interrupt the ongoing call
        response = VoiceResponse()
        return str(response), 200
    except Exception as e:
        logging.error(f"Error processing transcription: {e}")
        return str(e), 500

@app.route('/status/callback', methods=['POST'])
@validate_twilio_request
def handle_status_callback():
    """Handle call status callbacks"""
    try:
        call_status = request.form.get('CallStatus')
        call_sid = request.form.get('CallSid')
        
        logging.info(f"Call {call_sid} status: {call_status}")
        
        if call_status in ['completed', 'failed', 'busy', 'no-answer']:
            twilio_handler.end_call(call_sid)
        
        return '', 200
    except Exception as e:
        logging.error(f"Error handling status callback: {e}")
        return str(e), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Log HTTP request details
        logging.info(f"Received {request.method} request at {request.url}")
        logging.debug(f"Request headers: {request.headers}")
        logging.debug(f"Request data: {request.data}")

        data = request.json
        logging.debug(f"Parsed JSON data: {data}")

        # Read existing data
        with open(json_file_path, 'r') as f:
            existing_data = json.load(f)

        # Append new data to the appropriate categories
        for category, cases in data.items():
            if category in existing_data:
                for case in cases:
                    # Check if the case_number already exists in the category
                    if case['case_number'] not in [existing_case['case_number'] for existing_case in existing_data[category]]:
                        existing_data[category].append(case)
                        logging.debug(f"Added new case to category '{category}': {case}")
                    else:
                        logging.debug(f"Duplicate case number '{case['case_number']}' found in category '{category}', not adding.")

        # Write updated data back to the file
        with open(json_file_path, 'w') as f:
            json.dump(existing_data, f)
        logging.info("Data updated successfully.")

        response = jsonify({"status": "success", "message": "Data received and updated."})
        logging.info(f"Response: {response.get_json()}")
        return response, 200

    except Exception as e:
        logging.exception("An error occurred while processing the webhook.")
        response = jsonify({"status": "error", "message": "An error occurred while processing the request."})
        logging.info(f"Response: {response.get_json()}")
        return response, 500

def run_agent():
    emergency_agent.run()

if __name__ == '__main__':
    # Start the Fetch AI agent in a separate thread
    agent_thread = threading.Thread(target=run_agent)
    agent_thread.daemon = True
    agent_thread.start()
    
    # Start the Flask server
    app.run(host='0.0.0.0', port=8000, debug=True, use_reloader=False)
