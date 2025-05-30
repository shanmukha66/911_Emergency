"""
This agent can request data from a website and send an alert to your wallet if a condition is met.
"""

from uagents import Agent, Context

class Request(Model):
    message: str

agent = Agent()

API_KEY = ""  # Replace with your API key

def fetch_top_chats():
    url = "https://api.hume.ai/v0/evi/chats"
    
    params = {
        'page_number': 0,
        'page_size': 3,  # Retrieve the top 3 chats
        'ascending_order': False  # Set descending order to get the latest chats first
    }
    
    headers = {
        'X-Hume-Api-Key': API_KEY
    }

    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        chat_ids = [chat["id"] for chat in data.get("chats_page", [])]
        return chat_ids
    else:
        print(f"Failed to fetch chats: {response.status}")
        return []

def process_chat_id(chat_id):
    # Example: define the second API call you want to perform with each chat ID
    url = f"https://api.hume.ai/v0/evi/chats/{chat_id}"

    params = {
        'page_size' : 100,
        'ascending_order': True  # Set descending order to get the latest chats first
    }

    headers = {
        'X-Hume-Api-Key': API_KEY
    }

    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        event_roles = [event["role"] for event in data.get("events_page", [])]
        event_text = [event["message_text"] for event in data.get("events_page", [])]

        # Create the dictionary with the index as the key and the role:text as the value
        events_dict = {
            index: {event_roles[index]: event_text[index]} for index in range(len(event_roles))
        }
        print(events_dict.items())
        return events_dict


    else:
        print(f"Failed to fetch chats: {response.status}")
        return []
            

def fetch_transcripts():

    # Fetch top 3 chats
    chat_ids = fetch_top_chats() ##ctx.send()
    transcripts = []
    
    if chat_ids:
        # Process each chat ID iteratively
        for chat_id in chat_ids:
            print(f"Processing chat ID: {chat_id}")
            transcripts.append(process_chat_id(chat_id))
    
    return transcripts


@agent.on_interval(period=5)
async def process_transcripts(ctx: Context):

    transcripts = fetch_transcripts()

    # Your API key
    OPENAI_API_KEY = ""

    # API endpoint
    url = "https://api.openai.com/v1/chat/completions"

    # System prompt
    system_prompt = """
    You are a 911 AI agent bot, you will segregate 911 call transcripts into departments of wildlife, police, water, medical and fire. 
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
    
    ctx.logger.info(output)


if __name__ == "__main__":
    agent.run()
