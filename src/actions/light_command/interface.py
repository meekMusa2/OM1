from dataclasses import dataclass
from actions.base import Interface

@dataclass
class WebhookLightInput:
    """Input interface for webhook light control."""
    action: str = ""

class WebhookLight(Interface):
    """Webhook light control interface."""
    input: WebhookLightInput
    output: WebhookLightInput
