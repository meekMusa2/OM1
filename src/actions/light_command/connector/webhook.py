import logging
import os
import aiohttp
from dotenv import load_dotenv
from actions.base import ActionConfig, ActionConnector
from actions.light_command.interface import WebhookLightInput

class WebhookLightConnector(ActionConnector[WebhookLightInput]):
    """Connector that calls the webhook to control lights."""
    
    def __init__(self, config: ActionConfig):
        super().__init__(config)
        load_dotenv()
        
        self.webhook_url = os.getenv("WEBHOOK_URL", "http://localhost:5000/webhook/light_command")
        logging.info(f"Webhook Light Connector initialized: {self.webhook_url}")
    
    async def connect(self, output_interface: WebhookLightInput) -> None:
        """Send command to webhook."""
        try:
            action = output_interface.action.lower()
            
            logging.info(f"Sending webhook command: {action}")
            
            payload = {"command": action}
            headers = {"Content-Type": "application/json"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logging.info(f"Webhook call successful: {result}")
                    else:
                        error_text = await response.text()
                        logging.error(f"Webhook error {response.status}: {error_text}")
                        raise Exception(f"Webhook returned {response.status}")
        
        except Exception as e:
            logging.error(f"Failed to call webhook: {str(e)}")
            raise
