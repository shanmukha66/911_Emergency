# Dial AI

## 911 Emergency Call System with AI Agents

### Description

We carefully evaluated different models to ensure the best fit for our use case, understanding that when someone calls 911, they are already in distress. Selecting a low latency voice model was crucial, and Vapi was the obvious choice for its ability to respond with human-like sensitivity. For real-time conversations, we integrated Vapi with Twilio through webhooks, allowing callers to speak directly into their phones as they would with a live operator.

We built the system using Fetch AI to manage the agents, with AgentVerse hosting them. In this setup, two agents communicate with each other in real time. When a call is placed, the first agent retrieves the chat ID and real-time transcripts using Twilio’s webhook. These transcripts are passed through the agent, which uses OpenAI’s API (GPT-4) to extract key information, organize it, and prioritize the emergency based on urgency. This agent communicates with another agent to pass the extracted information to the dispatcher console.

These agents work together, with one handling the live interactions and event classifications. The data from the first agent is formatted in JSON by the second agent and sent to a dashboard, where dispatchers can view emergencies stack-ranked by severity and location.

### Instructions to Run the Project

1. To initiate an instance of the project, please dial the following number: **+1(858)260-3506**.  
   This initiates an instance emulating a 9-1-1 call. 

2. After conversing with the AI agent, you can view the extracted and classified data in the dispatcher dashboard.
   
3. To view the dashboard (Run the following commands) :
   
   a) #Install Requirements:

      pip install -r requirements.txt
   
   b) #Start the Flask Server:
   
      python server.py

   c) #Expose the Flask Server using Ngrok:
   
      ngrok http 8080

   d) #Run the Streamlit App:
   
      streamlit run dashboard.py

### Agents from the Agentverse

- **Agent ID using Vapi as a voice assistant and OpenAI to process chats**:  
  `agent1qgr7ah8a3fx7y6anwu98pkh3h099ntmkvynhxaczpt8gvwc3hq0q7jkmz7q`

- **Agent ID using Hume as a voice assistant and OpenAI to process chats**:  
  `agent1q0e07ywlx29q442zhn3qg5ycns79ex67e5c93hv5qxlves347j8hyc3wk8l`
