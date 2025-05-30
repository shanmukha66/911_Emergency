"""
This agent requests, fetches call transcripts of most recent 911 calls periodically and generates a report
"""

from uagents import Agent, Context
from simple_protocol import simples
 
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
    OPENAI_API_KEY = ""

    # API endpoint
    url = "https://api.openai.com/v1/chat/completions"

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


    # JSON payload to be sent to the API
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    }

    # Headers for the API request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    # Send the request to the OpenAI API
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    # Check if the response is successful
    if response.status_code == 200:
        # Parse the response
        data = response.json()
       
        # Extract the actual response content from the 'choices' array
        response_content = data['choices'][0]['message']['content']

    else:
        print(f"Failed to get a response: {response.status_code}")
        print(response.text)

    # Print the response from the API
    output = data['choices'][0]['message']['content']
    
    lines = output.splitlines()

    # Check if the string has more than two lines
    if len(lines) > 2:
        # Remove the first and last lines
        truncated_lines = lines[1:-1]
    else:
        # If the string has 2 lines or less, return an empty string
        return ""

    output = "\n".join(truncated_lines)
   
    send_report(output)

    ctx.logger.info("Done")


if __name__ == "__main__":
    agent.run()
