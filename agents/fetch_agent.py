from uagents import Agent, Context, Protocol, Model
from uagents.setup import fund_agent_if_low
import os
import json
import logging

class EmergencyData(Model):
    category: str
    cases: list

class EmergencyProtocol(Protocol):
    def __init__(self):
        super().__init__("emergency_protocol")
        
    async def process_emergency(self, emergency_data: EmergencyData):
        """Process emergency data and communicate with dispatcher"""
        try:
            # Process the emergency data
            logging.info(f"Processing emergency: {emergency_data}")
            
            # Create a context for the dispatcher protocol
            ctx = Context()
            ctx.logger = logging.getLogger("dispatcher")
            
            # Send to dispatcher agent using the dispatcher protocol
            await dispatcher_protocol.handle_emergency(ctx, emergency_data)
            
        except Exception as e:
            logging.error(f"Error processing emergency: {e}")

class DispatcherProtocol(Protocol):
    def __init__(self):
        super().__init__("dispatcher_protocol")
    
    async def handle_emergency(self, ctx: Context, emergency_data: EmergencyData):
        """Handle emergency data from the processing agent"""
        try:
            # Update the dispatcher dashboard
            with open('data.json', 'r+') as f:
                data = json.load(f)
                # Update relevant categories
                if emergency_data.category in data:
                    data[emergency_data.category].extend(emergency_data.cases)
                
                # Write back to file
                f.seek(0)
                json.dump(data, f)
                f.truncate()
            
            ctx.logger.info("Emergency data updated in dispatcher dashboard")
            
        except Exception as e:
            ctx.logger.error(f"Error handling emergency: {e}")

# Create the emergency processing agent
emergency_agent = Agent(
    name="emergency_processor",
    seed="emergency_processor_seed",  # Replace with a secure seed
    port=8001  # Using port 8001 for the emergency agent
)

# Create the dispatcher agent
dispatcher_agent = Agent(
    name="emergency_dispatcher",
    seed="emergency_dispatcher_seed",  # Replace with a secure seed
    port=8002  # Using port 8002 for the dispatcher agent
)

# Register protocols
emergency_protocol = EmergencyProtocol()
dispatcher_protocol = DispatcherProtocol()

emergency_agent.include(emergency_protocol)
dispatcher_agent.include(dispatcher_protocol)

# Fund agents if needed
fund_agent_if_low(emergency_agent.wallet.address())
fund_agent_if_low(dispatcher_agent.wallet.address())

# Store agent addresses
os.environ["EMERGENCY_AGENT_ADDRESS"] = emergency_agent.address
os.environ["DISPATCHER_AGENT_ADDRESS"] = dispatcher_agent.address

@emergency_agent.on_interval(period=5.0)
async def check_new_emergencies(ctx: Context):
    """Periodically check for new emergency data"""
    try:
        # Check for new emergency data (this would come from Twilio/Minimax)
        # For now, we'll just log
        ctx.logger.info("Checking for new emergencies...")
        
    except Exception as e:
        ctx.logger.error(f"Error checking emergencies: {e}")

@dispatcher_agent.on_message(model=EmergencyData)
async def handle_emergency_message(ctx: Context, sender: str, msg: EmergencyData):
    """Handle incoming emergency messages"""
    await dispatcher_protocol.handle_emergency(ctx, msg)

if __name__ == "__main__":
    # Run both agents
    emergency_agent.run()
    dispatcher_agent.run() 