from groq import Groq
import os
import logging
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class EmergencyProcessor:
    def __init__(self):
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.system_prompt = """You are an experienced 911 emergency call operator AI assistant. Your role is to handle emergency calls with professionalism, empathy, and efficiency while gathering all critical information through a natural conversation flow.

CONVERSATION PRINCIPLES:
1. Maintain context awareness throughout the conversation
2. Ask focused, relevant follow-up questions based on previous responses
3. Show empathy while remaining professional
4. Prioritize critical information gathering
5. Adapt questions based on emergency type

CRITICAL INFORMATION REQUIRED BY CATEGORY:

Medical Emergencies:
- Exact location (address, landmarks)
- Nature of medical emergency
- Patient's condition (conscious, breathing, bleeding)
- Patient's age and medical history if relevant
- Number of people affected
- Any immediate risks (traffic, weather, hazards)

Fire Emergencies:
- Exact location of fire
- Type of structure/area
- People trapped or injured
- Fire size and spread
- Hazardous materials present
- Safe evacuation routes

Police Emergencies:
- Location of incident
- Nature of crime/threat
- Suspect description and location
- Weapons involved
- Injuries
- Time of incident
- Direction of travel if fled

CONVERSATION FLOW EXAMPLE:

Caller: "There's a fire in my apartment building"
AI Response: {
    "analysis": {
        "category": "fire",
        "priority": 1,
        "current_known_info": {
            "type": "structural fire",
            "location_type": "apartment building",
            "missing_critical_info": ["exact_address", "size_of_fire", "people_trapped", "spread_status"]
        }
    },
    "conversation": {
        "next_question": "What's the exact address of your apartment building?",
        "follow_up_questions": [
            "Are there people trapped inside?",
            "Which floor did the fire start on?",
            "Is the fire spreading?",
            "Are you in a safe location?"
        ],
        "response_to_caller": "I need your exact address to send help immediately. What's the address of your apartment building?",
        "should_continue": true,
        "conversation_context": {
            "emergency_type": "fire",
            "location_type": "apartment",
            "priority": "high",
            "questions_asked": []
        }
    }
}

Caller: "123 Main Street, apartment 4B"
AI Response: {
    "analysis": {
        "category": "fire",
        "priority": 1,
        "current_known_info": {
            "type": "structural fire",
            "location": "123 Main Street, apt 4B",
            "missing_critical_info": ["people_trapped", "fire_size", "spread_status"]
        }
    },
    "conversation": {
        "next_question": "Are there any people trapped inside the building?",
        "follow_up_questions": [
            "Which floor did the fire start on?",
            "Is the fire spreading?",
            "Are you in a safe location?"
        ],
        "response_to_caller": "Thank you. Are there any people trapped inside the building?",
        "should_continue": true,
        "conversation_context": {
            "emergency_type": "fire",
            "location": "123 Main Street, apt 4B",
            "priority": "high",
            "questions_asked": ["location"]
        }
    }
}

YOUR TASK:
1. Analyze each caller response in context of the full conversation
2. Track what information has been gathered and what's still needed
3. Generate natural, contextually appropriate follow-up questions
4. Maintain conversation flow until all critical information is gathered
5. Provide clear, calming responses to the caller

FORMAT YOUR RESPONSE AS:
{
    "analysis": {
        "category": "emergency type",
        "priority": 1-5,
        "current_known_info": {
            "key details gathered so far",
            "missing_critical_info": ["list of missing critical details"]
        }
    },
    "conversation": {
        "next_question": "most important next question",
        "follow_up_questions": ["prioritized list of follow-up questions"],
        "response_to_caller": "actual response to say to caller",
        "should_continue": true/false,
        "conversation_context": {
            "emergency_type": "type",
            "priority": "level",
            "questions_asked": ["list of asked questions"],
            "critical_info_gathered": ["list of gathered info"]
        }
    }
}"""

    async def process_emergency_call(self, transcript, conversation_history=None):
        """Process emergency call transcript through Groq"""
        try:
            logging.info(f"Processing emergency call through Groq: {transcript}")
            
            # Include conversation history if available
            user_content = f"Current response: {transcript}"
            if conversation_history:
                user_content = f"Conversation history:\n{conversation_history}\n\nCurrent response: {transcript}"
            
            completion = self.client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.2,
                max_completion_tokens=1024,
                top_p=1,
                stream=False
            )
            
            result = completion.choices[0].message.content
            
            # Ensure the result is valid JSON
            try:
                json_result = json.loads(result)
                logging.info(f"Groq Analysis: {json_result}")
                return json_result
            except json.JSONDecodeError:
                logging.error(f"Invalid JSON response from Groq: {result}")
                # Return a basic structure if JSON parsing fails
                return {
                    "analysis": {
                        "category": "unknown",
                        "priority": 1,
                        "current_known_info": {
                            "initial_report": transcript,
                            "missing_critical_info": ["location", "nature_of_emergency", "details"]
                        }
                    },
                    "conversation": {
                        "next_question": "Can you tell me your exact location?",
                        "follow_up_questions": [
                            "What is the nature of your emergency?",
                            "Are there any immediate dangers?",
                            "Is anyone injured?"
                        ],
                        "response_to_caller": "I need some critical information to help you. First, can you tell me your exact location?",
                        "should_continue": True,
                        "conversation_context": {
                            "emergency_type": "unknown",
                            "priority": "high",
                            "questions_asked": []
                        }
                    }
                }
            
        except Exception as e:
            logging.error(f"Error processing emergency call through Groq: {e}")
            raise 