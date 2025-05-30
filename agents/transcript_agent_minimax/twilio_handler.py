from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
import os
import logging
from dotenv import load_dotenv
from .minimax_tts import MinimaxTTS

# Load environment variables
load_dotenv()

class TwilioHandler:
    def __init__(self):
        # Twilio credentials from environment variables
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.client = Client(self.account_sid, self.auth_token)
        self.tts = MinimaxTTS()  # Initialize Minimax TTS
        logging.info(f"TwilioHandler initialized with phone number: {self.phone_number}")

    def handle_incoming_call(self):
        """
        Handle incoming 911 calls using Minimax TTS
        """
        logging.info("Handling incoming call")
        try:
            response = VoiceResponse()
            
            # Initial greeting using Minimax TTS
            greeting_response = self.tts.generate_twiml_response(
                "911, what's your emergency?",
                voice_id="female_01",  # Using female voice for emergency services
                speed=1.0
            )
            response.append(greeting_response)
            
            # Configure Gather with explicit speech settings
            gather = Gather(
                input='speech dtmf',
                action='/voice/transcribe',
                method='POST',
                timeout=10,
                language='en-US',
                speechTimeout='auto',
                enhanced=True,
                hints='emergency, help, fire, medical, police',
                speechModel='phone_call'
            )
            
            # Add the prompt using Minimax TTS
            prompt_response = self.tts.generate_twiml_response(
                "Please describe your emergency.",
                voice_id="female_01",
                speed=1.0
            )
            gather.append(prompt_response)
            
            # Add the Gather to the response
            response.append(gather)
            
            # Log the full TwiML for debugging
            logging.info(f"Generated TwiML response: {str(response)}")
            
            # If no input received, this will only execute after Gather is done
            no_input_response = self.tts.generate_twiml_response(
                "We didn't receive any input. Please call back if you have an emergency.",
                voice_id="female_01",
                speed=1.0
            )
            response.append(no_input_response)
            
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