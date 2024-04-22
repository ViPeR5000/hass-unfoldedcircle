"""Update sensor."""

import logging
from typing import Any

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, UNFOLDED_CIRCLE_COORDINATOR
from .entity import UnfoldedCircleEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id][UNFOLDED_CIRCLE_COORDINATOR]
    async_add_entities([Update(coordinator)])


class Update(UnfoldedCircleEntity, UpdateEntity):
    """Update Entity."""

    _attr_icon = "mdi:update"

    def __init__(self, coordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self.coordinator.api.name}_update_status"
        self._attr_name = f"{self.coordinator.api.name} Firmware"
        self._attr_device_class = UpdateDeviceClass.FIRMWARE
        self._attr_auto_update = self.coordinator.api.automatic_updates
        self._attr_installed_version = self.coordinator.api.sw_version
        self._attr_latest_version = self.coordinator.api.latest_sw_version
        self._attr_release_notes = self.coordinator.api.release_notes
        self._attr_entity_category = EntityCategory.CONFIG

        self._attr_supported_features = UpdateEntityFeature(
            UpdateEntityFeature.INSTALL
            | UpdateEntityFeature.PROGRESS
            | UpdateEntityFeature.RELEASE_NOTES
        )
        self._attr_title = f"{self.coordinator.api.name} Firmware"

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        """Install an update."""
        if self.coordinator.api.update_in_progress is True:
            return
        await self.coordinator.api.update_remote()
        self._attr_in_progress = "0"  # Starts progress bar unlike when True
        self.async_write_ha_state()

    async def async_release_notes(self) -> str:
        return self.coordinator.api.release_notes

    async def async_update(self) -> None:
        """Update update information."""
        await self.coordinator.api.get_remote_update_information()
        self._attr_latest_version = self.coordinator.api.latest_sw_version
        self._attr_installed_version = self.coordinator.api.sw_version

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.api.update_in_progress is True:
            # 0 is interpreted as false. "0" display progress bar
            if self.coordinator.api.update_percent == 0:
                self._attr_in_progress = "0"
            else:
                self._attr_in_progress = self.coordinator.api.update_percent
        else:
            self._attr_in_progress = False
            self._attr_installed_version = self.coordinator.api.sw_version
            self._attr_latest_version = self.coordinator.api.latest_sw_version
        self.async_write_ha_state()
