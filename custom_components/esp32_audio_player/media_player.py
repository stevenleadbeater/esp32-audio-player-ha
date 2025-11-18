"""Media player platform for ESP32 Audio Player."""
from __future__ import annotations

import logging
import aiohttp
import async_timeout

from homeassistant.components import mqtt
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
    BrowseMedia,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_DEVICE_ID

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ESP32 Audio Player media player."""
    config = config_entry.data

    async_add_entities([
        ESP32AudioPlayer(
            hass,
            config[CONF_NAME],
            config[CONF_DEVICE_ID],
            config[CONF_HOST],
        )
    ])


class ESP32AudioPlayer(MediaPlayerEntity):
    """Representation of an ESP32 Audio Player."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:speaker-wireless"
    _attr_supported_features = (
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.PLAY_MEDIA
        | MediaPlayerEntityFeature.BROWSE_MEDIA
    )

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        device_id: str,
        host: str,
    ) -> None:
        """Initialize the media player."""
        self.hass = hass
        self._name = name
        self._device_id = device_id
        self._host = host
        self._state = MediaPlayerState.IDLE
        self._volume = 0.5
        self._available = False

        self._attr_unique_id = device_id
        self._attr_name = name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": name,
            "manufacturer": "Custom",
            "model": "ESP32-S2 Audio Player",
        }

        # MQTT topics
        self._state_topic = f"esp32_audio/{device_id}/state"
        self._volume_topic = f"esp32_audio/{device_id}/volume"
        self._availability_topic = f"esp32_audio/{device_id}/availability"

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topics."""

        @callback
        def state_received(msg):
            """Handle state updates."""
            payload = msg.payload
            if payload == "playing":
                self._state = MediaPlayerState.PLAYING
            elif payload == "idle":
                self._state = MediaPlayerState.IDLE
            else:
                self._state = MediaPlayerState.IDLE
            self.async_write_ha_state()

        @callback
        def volume_received(msg):
            """Handle volume updates."""
            try:
                self._volume = float(msg.payload) / 100.0
                self.async_write_ha_state()
            except ValueError:
                _LOGGER.error("Invalid volume value: %s", msg.payload)

        @callback
        def availability_received(msg):
            """Handle availability updates."""
            self._available = msg.payload == "online"
            self.async_write_ha_state()

        await mqtt.async_subscribe(self.hass, self._state_topic, state_received, 0)
        await mqtt.async_subscribe(self.hass, self._volume_topic, volume_received, 0)
        await mqtt.async_subscribe(self.hass, self._availability_topic, availability_received, 0)

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the player."""
        return self._state

    @property
    def volume_level(self) -> float:
        """Return the volume level."""
        return self._volume

    @property
    def available(self) -> bool:
        """Return if the device is available."""
        return self._available

    async def _send_http_command(self, endpoint: str, params: dict = None) -> bool:
        """Send HTTP command to the device."""
        url = f"http://{self._host}/{endpoint}"
        if params:
            param_str = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{url}?{param_str}"

        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            return True
                        _LOGGER.error("HTTP command failed: %s", response.status)
                        return False
        except Exception as e:
            _LOGGER.error("Error sending command to %s: %s", url, e)
            return False

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        await self._send_http_command("volume", {"level": volume})

    async def async_media_play(self) -> None:
        """Send play command."""
        # Resume not supported, would need last URL
        pass

    async def async_media_stop(self) -> None:
        """Send stop command."""
        await self._send_http_command("stop")

    async def async_play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs
    ) -> None:
        """Play media from a URL."""
        from homeassistant.components.media_source import async_resolve_media

        # Resolve media source URLs to actual HTTP URLs
        if media_id.startswith("media-source://"):
            try:
                sourced_media = await async_resolve_media(self.hass, media_id, self.entity_id)
                media_id = sourced_media.url
            except Exception as e:
                _LOGGER.error("Error resolving media source: %s", e)
                return

        _LOGGER.info("Playing media URL: %s", media_id)

        # URL encode the media_id
        from urllib.parse import quote
        encoded_url = quote(media_id, safe='')

        await self._send_http_command("play", {"url": encoded_url})

    async def async_browse_media(
        self, media_content_type: str | None = None, media_content_id: str | None = None
    ) -> BrowseMedia:
        """Implement the websocket media browsing helper."""
        from homeassistant.components.media_source import async_browse_media

        return await async_browse_media(
            self.hass,
            media_content_id,
            content_filter=lambda item: item.media_content_type.startswith("audio/"),
        )
