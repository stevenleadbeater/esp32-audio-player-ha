# ESP32 Audio Player

A Home Assistant custom integration for ESP32-based audio players using the ESP8266Audio library.

## Features

- Full media_player entity support
- Play media URLs (MP3, WAV)
- Volume control
- State reporting via MQTT
- Multiple device support

## Installation

### HACS (Recommended)

1. Add this repository to HACS as a custom repository
2. Install "ESP32 Audio Player"
3. Restart Home Assistant
4. Go to Settings > Devices & Services > Add Integration
5. Search for "ESP32 Audio Player"

### Manual Installation

1. Copy `custom_components/esp32_audio_player` to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Add the integration via the UI

## Configuration

When adding the integration, you'll need:

- **Name**: Friendly name for the device (e.g., "Living Room Speaker")
- **Device ID**: Must match the DEVICE_NAME in your firmware (e.g., "esp32-audio-01")
- **IP Address**: The IP address of your ESP32 device

## Firmware

This integration works with the custom ESP32 audio player firmware. See the `firmware/` directory for the PlatformIO project.

## Usage

```yaml
service: media_player.play_media
target:
  entity_id: media_player.living_room_speaker
data:
  media_content_id: "http://your-server/audio.mp3"
  media_content_type: music
```

## Multiple Devices

To add multiple speakers:

1. Flash each ESP32 with a unique `DEVICE_NAME` in the firmware
2. Add each device as a separate integration entry in Home Assistant

## Requirements

- Home Assistant 2023.1.0 or newer
- MQTT broker (e.g., Mosquitto)
- MQTT integration configured in Home Assistant
