# Alexa Time Control

A Home Assistant custom component that extends Alexa media players with time-based access control and blocking functionality.

## Features

This integration creates four control entities for each Alexa device:

- **Start Time** (time): The time when the device becomes available (default: 08:00)
- **End Time** (time): The time when the device becomes unavailable (default: 20:00)
- **Enabled** (switch): Master switch to enable/disable time control
- **Blocked** (switch): Manual block switch to prevent device usage

## How It Works

When enabled, the component monitors the Alexa media player's state. If someone tries to play media (state changes to "playing"), it checks:

1. **Enabled status**: If the "Enabled" switch is off, no checks are performed
2. **Blocked status**: If "Blocked" is on, sends a TTS message: *"Your device is currently blocked"*
3. **Time constraints**: If current time is outside the start/end time range, sends a TTS message: *"Actually it is [current time], your alexa has been enabled up to [end time] and can be used at [start time] again"*

After sending the TTS message, the device is automatically stopped.

## Installation

### Manual Installation

1. Copy the `custom_components/alexa_time_control` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Go to **Settings** > **Devices & Services** > **Add Integration**
4. Search for "Alexa Time Control"
5. Select the Alexa media player you want to control

### HACS Installation (if published)

1. Open HACS
2. Go to "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL and select "Integration" as the category
5. Click "Install"
6. Restart Home Assistant
7. Follow steps 3-5 from Manual Installation

## Configuration

After adding the integration through the UI:

1. Select your Alexa media player device
2. The integration will create four entities under the existing Alexa device:
   - `time.{device}_start_time` (default: 08:00)
   - `time.{device}_end_time` (default: 20:00)
   - `switch.{device}_enabled` (default: off)
   - `switch.{device}_blocked` (default: off)

## Usage Examples

### Basic Time Control

Set allowed hours from 8:00 AM to 8:00 PM:
```yaml
time.bedroom_echo_start_time: "08:00:00"
time.bedroom_echo_end_time: "20:00:00"
switch.bedroom_echo_enabled: on
```

### Temporary Block

Block the device temporarily:
```yaml
switch.bedroom_echo_blocked: on
```

### Automation Example

Automatically block the device during bedtime:
```yaml
automation:
  - alias: "Block Alexa at Bedtime"
    trigger:
      - platform: time
        at: "21:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.bedroom_echo_blocked
  
  - alias: "Unblock Alexa in Morning"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.bedroom_echo_blocked
```

## Notes

- Times are specified in HH:MM:SS format using Home Assistant's time picker (e.g., "08:30:00" for 8:30 AM)
- The component supports ranges that cross midnight (e.g., 20:00 to 08:00 blocks from 8:00 PM to 8:00 AM)
- TTS messages are sent via the Alexa Media Player's notification service
- The integration requires the Alexa Media Player integration to be installed and configured
- The new entities are added to the existing Alexa device, not as a separate device

## Requirements

- Home Assistant 2023.1 or newer
- Alexa Media Player integration installed and configured
- At least one Alexa device set up in Home Assistant

## Troubleshooting

- **TTS not working**: Ensure the Alexa Media Player integration is properly configured and the notification service is available
- **State changes not detected**: Check that the Alexa entity ID is correct and the device is properly connected
- **Time checks not working**: Verify that your Home Assistant time zone is correctly configured

## License

MIT License - feel free to modify and distribute as needed.
