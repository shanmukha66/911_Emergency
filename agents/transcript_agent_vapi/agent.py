"""
This agent requests, fetches call transcripts of most recent 911 calls periodically and generates a report
"""

from uagents import Agent, Context
from simple_protocol import simples
import requests
import json
import os
import groq

class Request(Model):
    message: str

agent = Agent()

agent.include(simples)

def fetch_transcripts():

    # Define the API endpoint and parameters
    url = "https://api.vapi.ai/call"
    params = {
        'assistantId': 'ID',
        'phoneNumberId': 'PID',
        'limit': 3  # Retrieve the top 3 elements
    }

    # Authorization header
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer Token'
    }

    # Make the GET request to the API
    response = requests.get(url, params=params, headers=headers)

    # Check if the response is successful
    if response.status_code == 200:
        data = response.json()  # Parse the JSON response

        # Prepare a list of dictionaries with 'id', 'transcript', and 'customer number'
        transcripts = [
            {
                'id': item.get('id'),
                'transcript': item.get('transcript'),
                'customer_number': item.get('customer', {}).get('number'),
                'analysis' : item.get('analysis',{}).get('summary')   
            }
            for item in data
        ]

        return transcripts

    else:
        return []

def send_report(report):
    # Define the API endpoint
    url = "https://a4ff-199-115-241-212.ngrok-free.app/webhook"

    # Define the JSON data to be sent in the POST request
    data = report
    # Define the headers
    headers = {
        'Content-Type': 'application/json'
    }

    # Make the POST request to the API
    response = requests.post(url, headers=headers, data=json.dumps(data))

    # Check if the response is successful
    if response.status_code == 200:
        print("Request was successful!")
        print("Response data:", response.json())  # Print the response data (if any)
    else:
        print(f"Failed to make the request: {response.status_code}")
        print(response.text)  # Print the response message for debugging

            

@agent.on_interval(period=60)
async def process_transcripts(ctx: Context):

    transcripts = fetch_transcripts()

    # Your API key
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    client = groq.Client(api_key=GROQ_API_KEY)

    # System prompt
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

    # User prompt made from event transcripts
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
        response_content = chat_completion.choices[0].message.content
        
        # Process the output
        lines = response_content.splitlines()
        if len(lines) > 2:
            truncated_lines = lines[1:-1]
            output = "\n".join(truncated_lines)
        
        ctx.logger.info(output)
        
    except Exception as e:
        ctx.logger.error(f"Error in processing transcripts: {e}")
        print(f"Failed to get a response: {str(e)}")

    ctx.logger.info("Processing complete")


if __name__ == "__main__":
    agent.run()
