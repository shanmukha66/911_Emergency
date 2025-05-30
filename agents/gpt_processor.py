import groq
import os
import logging
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class EmergencyProcessor:
    def __init__(self):
        self.client = groq.Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.system_prompt = """You are an emergency call processing AI assistant. Your role is to:
1. Analyze emergency call transcripts
2. Categorize the emergency (medical, fire, police, etc.)
3. Extract key information (location, severity, people involved)
4. Determine priority level (1-5, where 1 is most urgent)
5. Provide a structured response with recommended actions

Format your response as JSON with the following structure:
{
    "category": "medical|fire|police|wildlife|water",
    "priority": 1-5,
    "location": "extracted location",
    "description": "brief description",
    "key_details": {
        "people_involved": "number or description",
        "immediate_risks": ["list", "of", "risks"],
        "resources_needed": ["list", "of", "required", "resources"]
    },
    "recommended_actions": ["list", "of", "immediate", "actions"],
    "additional_notes": "any other important information"
}

Remember to:
- Set priority 1 for life-threatening emergencies
- Set priority 2 for severe but not immediately life-threatening
- Set priority 3 for urgent but stable situations
- Set priority 4 for non-urgent situations
- Set priority 5 for informational calls

Always maintain a professional and focused analysis."""

    async def process_emergency_call(self, transcript):
        """Process emergency call transcript through Groq"""
        try:
            logging.info(f"Processing emergency call through Groq: {transcript}")
            
            completion = self.client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Process this emergency call transcript and provide a JSON response: {transcript}"}
                ],
                temperature=0.2,  # Lower temperature for more consistent responses
                max_completion_tokens=1024,
                top_p=1,
                stream=False  # We don't want streaming for this use case
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
                    "category": "unknown",
                    "priority": 1,  # Default to high priority if parsing fails
                    "description": transcript,
                    "error": "Failed to parse AI response"
                }
            
        except Exception as e:
            logging.error(f"Error processing emergency call through Groq: {e}")
            raise 