"""
This agent requests and processes call transcripts using Minimax API for voice processing
and Groq for analysis and categorization.
"""

from uagents import Agent, Context
from simple_protocol import simples
import requests
import json
import os
import groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Request(Model):
    message: str

agent = Agent()
agent.include(simples)

def fetch_transcripts():
    """
    Fetch transcripts using Minimax API
    """
    # Minimax API configuration
    MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
    MINIMAX_GROUP_ID = os.getenv("MINIMAX_GROUP_ID")
    
    # Define the API endpoint for Minimax Pro Chat API
    url = "https://api.minimax.chat/v1/text/chatcompletion_pro"
    
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Get the last 3 conversations
    payload = {
        "model": "abab5.5-chat",
        "messages": [
            {
                "sender_type": "USER",
                "text": "Please provide the last 3 emergency call transcripts."
            }
        ],
        "reply_constraints": {
            "sender_type": "BOT"
        },
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            reply = data.get('reply', '')
            
            # Parse the response into our transcript format
            transcripts = []
            if reply:
                # Split the reply into individual transcripts
                # This assumes Minimax returns transcripts in a structured format
                # You may need to adjust this parsing based on actual response format
                conversations = reply.split('\n\n')
                for i, conv in enumerate(conversations[:3]):  # Take only last 3
                    transcripts.append({
                        'id': f'conv_{i}',
                        'transcript': conv,
                        'customer_number': 'Unknown',  # This would come from your call data
                        'analysis': {
                            'summary': ''  # Will be filled by Groq analysis
                        }
                    })
            return transcripts
        else:
            print(f"Failed to fetch transcripts: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching transcripts: {e}")
        return []

def send_report(report):
    """
    Send processed report to the webhook endpoint
    """
    url = "https://a4ff-199-115-241-212.ngrok-free.app/webhook"
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(report))
        if response.status_code == 200:
            print("Report sent successfully")
            return True
        else:
            print(f"Failed to send report: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error sending report: {e}")
        return False

@agent.on_interval(period=60)
async def process_transcripts(ctx: Context):
    """
    Periodically process transcripts and generate reports using Groq
    """
    transcripts = fetch_transcripts()
    
    # Groq configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    client = groq.Client(api_key=GROQ_API_KEY)
    
    # System prompt for emergency categorization
    system_prompt = """
    You are a 911 AI agent bot, you will segregate 911 call transcripts into departments of wildlife, police, water, medical and fire. If you feel an incident needs attention 
    from multiple departments, you can add it to all.
    In each department, stack rank the calls based on severity. Give the output in JSON format, with each department containing a list of cases.
    Each case should include the following fields:
    - case number
    - location
    - dispatch
    - situation
    - open status (yes/no)
    - stack rank for each department.
    """

    # Prepare user prompt with transcripts
    user_prompt = f"The following are the three 911 call transcripts which you need to segregate: {transcripts}"

    try:
        # Call Groq API
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="mixtral-8x7b-32768",  # Using Mixtral model for better performance
            temperature=0.5,
            max_tokens=4000
        )
        
        # Extract the response
        output = chat_completion.choices[0].message.content
        
        # Process the output
        lines = output.splitlines()
        if len(lines) > 2:
            truncated_lines = lines[1:-1]
            output = "\n".join(truncated_lines)
        
        # Send the processed report
        send_report(output)
        ctx.logger.info("Successfully processed and sent report")
        
    except Exception as e:
        ctx.logger.error(f"Error in processing transcripts: {e}")
    
    ctx.logger.info("Processing complete") 