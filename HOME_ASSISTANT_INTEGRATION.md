# OM1 Home Assistant Integration for Tuya Smart Bulb

This integration enables OM1 to control Home Assistant devices (specifically Tuya smart bulbs) via a webhook-based REST API architecture.

## Architecture
```
OM1 → Custom Action (light_command) → Webhook Receiver → Home Assistant REST API → Tuya Bulb
```

## Features

- ✅ Turn light on/off via OM1
- ✅ Adjust brightness (0-100%)
- ✅ LLM-powered natural language understanding
- ✅ Modular webhook architecture (reusable for other devices)
- ✅ Full error handling and logging

## Files Added

- `src/actions/light_command/interface.py` - Action interface definition
- `src/actions/light_command/connector/webhook.py` - Webhook connector
- `src/webhook_receiver.py` - Standalone webhook server that calls Home Assistant API
- `config/voice_light_control.json5` - OM1 configuration for voice-controlled lighting

## Setup Instructions

### Prerequisites

- Home Assistant instance (accessible via network)
- Tuya smart bulb integrated with Home Assistant
- Python 3.10+
- OM1 installed and configured

### Installation

1. **Clone this repository**
```bash
   git clone https://github.com/meekMusa2/OM1.git
   cd OM1
```

2. **Install dependencies**
```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
```

3. **Configure Home Assistant credentials**
   
   Create or edit `.env` file:
```bash
   OM_API_KEY=your_openmind_api_key_here
   HA_URL=http://YOUR_HA_IP:8123
   HA_TOKEN=your_home_assistant_long_lived_token
   HA_ENTITY_ID=light.your_bulb_entity_id
```

   To get your Home Assistant long-lived token:
   - Go to your Home Assistant
   - Profile → Security → Long-Lived Access Tokens
   - Create token and copy it

4. **Start the webhook receiver** (Terminal 1)
```bash
   uv run src/webhook_receiver.py
```

   You should see:
```
   INFO:     Uvicorn running on http://0.0.0.0:5000
```

5. **Start OM1** (Terminal 2)
```bash
   uv run src/run.py voice_light_control
```

   You should see:
```
   INFO - Webhook Light Connector initialized
   INFO - LLM initialized with 2 function schemas
   INFO - Starting OM1 with standard configuration
```

## Usage

Once both services are running, OM1 will automatically control your light based on the system prompt examples. The LLM decides when to trigger light commands.

### Supported Commands

The webhook supports these commands:
- `turn_on` - Turn the light on
- `turn_off` - Turn the light off
- `set_brightness_X` - Set brightness to X percent (0-100)

### Testing Manually

You can test the webhook directly:
```bash
curl -X POST http://localhost:5000/webhook/light_command \
  -H "Content-Type: application/json" \
  -d '{"command": "turn_on"}'
```

## How It Works

1. **OM1 processes input** - The LLM receives the system prompt and decides what action to take
2. **Action triggered** - OM1 calls the `light_command` action with parameters like `turn_on`
3. **Webhook connector** - The connector sends an HTTP POST to the webhook receiver
4. **Home Assistant API call** - The webhook translates the command and calls HA's REST API
5. **Device control** - Home Assistant executes the command on the Tuya bulb

## Configuration Details

### Action Configuration

The `light_command` action is defined in `config/voice_light_control.json5`:
```json5
{
  "name": "light_command",
  "llm_label": "light_command",  // Must match exactly (case-sensitive)
  "implementation": "passthrough",
  "connector": "webhook"  // References webhook.py in connector/
}
```

**Important**: The `llm_label` must be lowercase and match the `name` field exactly.

### System Prompt

The system prompt teaches the LLM when and how to use the light commands:
```
If someone says 'Turn on the light', you should:
    light_command: 'turn_on'
    speak: 'Turning on the light for you'
```

## Troubleshooting

### Webhook connection refused
- **Error**: `Cannot connect to host localhost:5000`
- **Solution**: Make sure the webhook receiver is running in a separate terminal

### Action not found
- **Error**: `Attempted to call non-existent action: lightcommand`
- **Solution**: Ensure `llm_label` in config matches the action name exactly (case-sensitive)

### Home Assistant authentication failed
- **Error**: `HA API error 401`
- **Solution**: Verify your HA_TOKEN in `.env` is correct and not expired

### Bulb not responding
- **Error**: Webhook succeeds but bulb doesn't change
- **Solution**: Check `HA_ENTITY_ID` matches your bulb's exact entity ID in Home Assistant

## Extending This Integration

This webhook architecture can be extended to control other Home Assistant devices:

1. Add new commands to the webhook receiver
2. Update the action interface to support new command types
3. Modify the system prompt to teach the LLM about new capabilities

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or PR.

## Demo

[Link to demo video will be added]

## Credits

Built for OpenMind OM1 Bounty Program - Issue #366
