from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TwilioHandler:
    def __init__(self):
        # Twilio credentials from environment variables
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.client = Client(self.account_sid, self.auth_token)
        logging.info(f"TwilioHandler initialized with phone number: {self.phone_number}")

    def handle_incoming_call(self):
        """
        Handle incoming 911 calls and integrate with Minimax
        """
        logging.info("Handling incoming call")
        try:
            response = VoiceResponse()
            
            # Initial greeting
            response.say("911, what's your emergency?", voice='alice')
            logging.debug("Added initial greeting")
            
            # Gather the caller's response with transcription enabled
            gather = Gather(
                input='speech',
                timeout=3,
                language='en-US',
                transcribe=True,
                transcribeCallback='/voice/transcribe'
            )
            gather.say("Please describe your emergency.", voice='alice')
            response.append(gather)
            logging.debug("Added gather instructions")
            
            # If no input received
            response.say("We didn't receive any input. Please call back if you have an emergency.", voice='alice')
            
            logging.info("Successfully created voice response")
            return str(response)
        except Exception as e:
            logging.error(f"Error in handle_incoming_call: {e}")
            raise

    def process_speech(self, speech_result):
        """
        Process the speech input and send to Minimax
        """
        logging.info("Processing speech input")
        logging.debug(f"Speech result: {speech_result}")
        
        # This will be processed by the main agent
        result = {
            'transcript': speech_result.get('SpeechResult', ''),
            'call_sid': speech_result.get('CallSid'),
            'caller': speech_result.get('From'),
            'confidence': speech_result.get('Confidence'),
            'timestamp': speech_result.get('Timestamp')
        }
        logging.info(f"Processed speech result: {result}")
        return result

    def end_call(self, call_sid):
        """
        End the call and save any final information
        """
        logging.info(f"Ending call with SID: {call_sid}")
        try:
            call = self.client.calls(call_sid).update(status='completed')
            logging.info("Call ended successfully")
            return True
        except Exception as e:
            logging.error(f"Error ending call: {e}")
            return False

    def make_test_call(self, to_number):
        """
        Make a test call to verify the setup
        """
        logging.info(f"Making test call to: {to_number}")
        try:
            call = self.client.calls.create(
                url='http://demo.twilio.com/docs/voice.xml',
                to=to_number,
                from_=self.phone_number
            )
            logging.info(f"Test call created with SID: {call.sid}")
            return call.sid
        except Exception as e:
            logging.error(f"Error making test call: {e}")
            return None 