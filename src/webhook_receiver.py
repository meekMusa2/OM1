import logging
import os
import aiohttp
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI()

class LightCommand(BaseModel):
    command: str  # "turn_on", "turn_off", "set_brightness_80"
    source: str = "home_assistant"

# Home Assistant configuration
HA_URL = os.getenv("HA_URL", "http://192.168.126.14:8123")
HA_TOKEN = os.getenv("HA_TOKEN")
HA_ENTITY_ID = os.getenv("HA_ENTITY_ID", "light.smart_bulb")

if not HA_TOKEN:
    logging.warning("HA_TOKEN not found in environment - webhook will not be able to control lights")

@app.post("/webhook/light_command")
async def receive_light_command(command: LightCommand):
    """Receive light commands from Home Assistant and execute them."""
    try:
        logging.info(f"Received webhook command: {command.command} from {command.source}")
        
        action = command.command.lower()
        
        # Validate action
        if action not in ["turn_on", "turn_off"] and not action.startswith("set_brightness_"):
            raise ValueError(f"Unknown command: {action}")
        
        # Call Home Assistant API
        result = await call_home_assistant(action)
        
        return {
            "status": "success",
            "command": command.command,
            "message": f"Light command '{command.command}' executed successfully",
            "ha_response": result
        }
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def call_home_assistant(action: str):
    """Call Home Assistant API to control the light."""
    try:
        # Determine service and payload
        if action == "turn_on":
            service = "turn_on"
            payload = {"entity_id": HA_ENTITY_ID}
        elif action == "turn_off":
            service = "turn_off"
            payload = {"entity_id": HA_ENTITY_ID}
        elif action.startswith("set_brightness_"):
            service = "turn_on"
            try:
                brightness = int(action.split("_")[-1])
                # Convert 0-100 to 0-255
                brightness_255 = int((brightness / 100) * 255)
                payload = {"entity_id": HA_ENTITY_ID, "brightness": brightness_255}
            except (ValueError, IndexError):
                raise ValueError(f"Invalid brightness value in action: {action}")
        else:
            raise ValueError(f"Unknown action: {action}")
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {HA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Make API call
        url = f"{HA_URL}/api/services/light/{service}"
        logging.info(f"Calling Home Assistant: POST {url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    logging.info(f"Home Assistant API call successful: {action}")
                    return response_data
                else:
                    error_msg = f"Home Assistant API error {response.status}: {response_data}"
                    logging.error(error_msg)
                    raise Exception(error_msg)
    
    except Exception as e:
        logging.error(f"Failed to call Home Assistant: {str(e)}")
        raise

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "ok",
        "service": "OM1 Webhook Receiver",
        "ha_configured": HA_TOKEN is not None
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=5000)
