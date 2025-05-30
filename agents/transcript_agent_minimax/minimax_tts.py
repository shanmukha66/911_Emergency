import os
import requests
from dotenv import load_dotenv
import logging
import base64
import json

# Load environment variables
load_dotenv()

class MinimaxTTS:
    def __init__(self):
        self.api_key = os.getenv("MINIMAX_API_KEY")
        self.group_id = os.getenv("MINIMAX_GROUP_ID")
        self.base_url = f"https://api.minimaxi.chat/v1/t2a_v2?GroupId={self.group_id}"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if not self.api_key or not self.group_id:
            logging.error("Minimax API key or group ID not found in environment variables")
            logging.debug(f"API Key present: {bool(self.api_key)}")
            logging.debug(f"Group ID present: {bool(self.group_id)}")

    def generate_speech(self, text, voice_id="female_01", speed=1.0):
        """
        Generate speech from text using Minimax TTS API
        voice_id options: female_01, female_02, male_01, male_02
        speed: 0.5 to 2.0
        """
        try:
            if not self.api_key or not self.group_id:
                logging.error("Minimax credentials not properly configured")
                return None

            payload = {
                "text": text,
                "voice_id": voice_id,
                "speed": speed,
                "vol": 1.0,
                "pitch": 0
            }

            logging.info(f"Making Minimax TTS request to {self.base_url}")
            logging.debug(f"Request payload: {payload}")
            logging.debug(f"Headers: {self.headers}")

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload
            )

            logging.debug(f"Minimax response status: {response.status_code}")
            logging.debug(f"Minimax response headers: {response.headers}")
            logging.debug(f"Minimax response content: {response.text[:200]}")  # Log first 200 chars of response

            if response.status_code == 200:
                try:
                    audio_data = response.json()
                    logging.debug(f"Response JSON keys: {audio_data.keys()}")
                    
                    # Try different possible response structures
                    audio_content = (
                        audio_data.get('audio') or 
                        audio_data.get('data', {}).get('audio') or
                        audio_data.get('response', {}).get('audio')
                    )
                    
                    if audio_content:
                        # Convert audio content to proper format for Twilio
                        audio_url = f"data:audio/mp3;base64,{audio_content}"
                        return audio_url
                    else:
                        logging.error(f"No audio content found in response structure: {audio_data}")
                        return None
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse JSON response: {e}")
                    return None
            else:
                logging.error(f"Minimax TTS API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logging.error(f"Error generating speech with Minimax: {e}")
            return None

    def generate_twiml_response(self, text, voice_id="female_01", speed=1.0):
        """
        Generate TwiML response with Minimax TTS audio
        """
        from twilio.twiml.voice_response import VoiceResponse

        try:
            # Generate speech using Minimax
            audio_url = self.generate_speech(text, voice_id, speed)
            
            # Create TwiML response
            response = VoiceResponse()
            
            if audio_url:
                # Add the audio content as a Play verb
                response.play(audio_url)
            else:
                # Fallback to Twilio's TTS if Minimax fails
                logging.warning("Falling back to Twilio TTS")
                response.say(text, voice='alice')
            
            return str(response)

        except Exception as e:
            logging.error(f"Error generating TwiML with Minimax: {e}")
            # Fallback to Twilio's TTS
            response = VoiceResponse()
            response.say(text, voice='alice')
            return str(response) 