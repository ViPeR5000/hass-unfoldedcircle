"""Platform for Number integration."""

import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)

from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import (
    UnfoldedCircleRemoteCoordinator,
    UnfoldedCircleDockCoordinator,
)
from .entity import UnfoldedCircleEntity, UnfoldedCircleDockEntity
from . import UnfoldedCircleConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class UnfoldedCircleNumberEntityDescription(NumberEntityDescription):
    """Class describing Unfolded Circle Remote number entities."""

    unique_id: str = ""
    control_fn: Callable = None


async def update_remote_display_settings(
    coordinator: UnfoldedCircleRemoteCoordinator, value: int
) -> None:
    await coordinator.api.patch_remote_display_settings(brightness=value)


async def update_remote_button_settings(
    coordinator: UnfoldedCircleRemoteCoordinator, value: int
) -> None:
    await coordinator.api.patch_remote_button_settings(brightness=value)


async def update_remote_sound_settings(
    coordinator: UnfoldedCircleRemoteCoordinator, value: int
) -> None:
    await coordinator.api.patch_remote_sound_settings(sound_effects_volume=value)


async def update_remote_display_timeout_settings(
    coordinator: UnfoldedCircleRemoteCoordinator, value: int
) -> None:
    await coordinator.api.patch_remote_power_saving_settings(display_timeout=value)


async def update_remote_wakeup_sensitivity_settings(
    coordinator: UnfoldedCircleRemoteCoordinator, value: int
) -> None:
    await coordinator.api.patch_remote_power_saving_settings(wakeup_sensitivity=value)


async def update_remote_sleep_timeout_settings(
    coordinator: UnfoldedCircleRemoteCoordinator, value: int
) -> None:
    await coordinator.api.patch_remote_power_saving_settings(sleep_timeout=value)


UNFOLDED_CIRCLE_NUMBER: tuple[UnfoldedCircleNumberEntityDescription, ...] = (
    UnfoldedCircleNumberEntityDescription(
        key="display_brightness",
        device_class=None,
        entity_category=EntityCategory.CONFIG,
        name="Display Brightness",
        unique_id="display_brightness",
        icon="mdi:brightness-5",
        control_fn=update_remote_display_settings,
        native_min_value=0,
        native_max_value=100,
    ),
    UnfoldedCircleNumberEntityDescription(
        key="button_backlight_brightness",
        device_class=None,
        entity_category=EntityCategory.CONFIG,
        name="Button Backlight Brightness",
        unique_id="button_backlight_brightness",
        icon="mdi:keyboard-settings-outline",
        control_fn=update_remote_button_settings,
        native_min_value=0,
        native_max_value=100,
    ),
    UnfoldedCircleNumberEntityDescription(
        key="sound_effects_volume",
        device_class=None,
        entity_category=EntityCategory.CONFIG,
        name="Sound Effects Volume",
        unique_id="sound_effects_volume",
        icon="mdi:volume-medium",
        control_fn=update_remote_sound_settings,
        native_min_value=0,
        native_max_value=100,
    ),
    UnfoldedCircleNumberEntityDescription(
        key="display_timeout",
        device_class=None,
        entity_category=EntityCategory.CONFIG,
        name="Display Timeout",
        unique_id="display_timeout",
        icon="mdi:vibrate",
        control_fn=update_remote_display_timeout_settings,
        native_min_value=0,
        native_max_value=60,
    ),
    UnfoldedCircleNumberEntityDescription(
        key="wakeup_sensitivity",
        device_class=None,
        entity_category=EntityCategory.CONFIG,
        name="Wake Sensitivity",
        unique_id="wakeup_sensitivity",
        icon="mdi:sleep-off",
        control_fn=update_remote_wakeup_sensitivity_settings,
        native_min_value=0,
        native_max_value=3,
    ),
    UnfoldedCircleNumberEntityDescription(
        key="sleep_timeout",
        device_class=None,
        entity_category=EntityCategory.CONFIG,
        name="Sleep Timeout",
        unique_id="sleep_timeout",
        icon="mdi:power-sleep",
        control_fn=update_remote_sleep_timeout_settings,
        native_min_value=0,
        native_max_value=1800,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: UnfoldedCircleConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Number platform."""
    # Setup connection with devices
    coordinator = config_entry.runtime_data.coordinator
    dock_coordinators = config_entry.runtime_data.dock_coordinators
    async_add_entities(
        UCRemoteNumber(coordinator, Number) for Number in UNFOLDED_CIRCLE_NUMBER
    )

    for dock_coordinator in dock_coordinators:
        async_add_entities(
            UCDockNumber(dock_coordinator, description)
            for description in UNFOLDED_CIRCLE_DOCK_NUMBER
        )


class UCRemoteNumber(UnfoldedCircleEntity, NumberEntity):
    """Class representing an unfolded circle number."""

    entity_description = UNFOLDED_CIRCLE_NUMBER

    def __init__(
        self, coordinator, description: UnfoldedCircleNumberEntityDescription
    ) -> None:
        """Initialize a Number."""
        super().__init__(coordinator)
        self._description = description
        self.coordinator = coordinator
        self.entity_description = description
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.api.model_number}_{self.coordinator.api.serial_number}_{description.unique_id}"
        self._attr_name = description.name
        key = "_" + description.key
        self._attr_native_value = coordinator.data.get(key)
        self._attr_icon = description.icon
        self._attr_entity_category = description.entity_category
        self._attr_device_class = description.device_class
        self._attr_min_value = description.min_value
        self._attr_max_value = description.max_value

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        # Add websocket events according to corresponding entities
        self.coordinator.subscribe_events["configuration"] = True
        await super().async_added_to_hass()

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        value_int = int(value)
        await self.entity_description.control_fn(self.coordinator, value_int)
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = getattr(
            self.coordinator.api, self.entity_description.key
        )
        self.async_write_ha_state()


async def update_dock_led_brightness(
    coordinator: UnfoldedCircleDockCoordinator, value: int
) -> None:
    command_value = str(value)
    await coordinator.api.send_command(
        command="SET_LED_BRIGHTNESS", command_value=command_value
    )


async def update_dock_ethernet_led_brightness(
    coordinator: UnfoldedCircleDockCoordinator, value: int
) -> None:
    command_value = str(value)
    await coordinator.api.send_command(
        command="SET_ETHERNET_LED_BRIGHTNESS", command_value=command_value
    )


UNFOLDED_CIRCLE_DOCK_NUMBER: tuple[UnfoldedCircleNumberEntityDescription, ...] = (
    UnfoldedCircleNumberEntityDescription(
        key="led_brightness",
        device_class=None,
        entity_category=EntityCategory.CONFIG,
        name="LED Brightness",
        unique_id="display_brightness",
        icon="mdi:brightness-5",
        control_fn=update_dock_led_brightness,
        native_min_value=0,
        native_max_value=100,
    ),
    UnfoldedCircleNumberEntityDescription(
        key="ethernet_led_brightness",
        device_class=None,
        entity_category=EntityCategory.CONFIG,
        name="Ethernet LED Brightness",
        unique_id="button_backlight_brightness",
        icon="mdi:lan",
        control_fn=update_dock_ethernet_led_brightness,
        native_min_value=0,
        native_max_value=100,
        entity_registry_enabled_default=False,
        entity_registry_visible_default=False,
    ),
)


class UCDockNumber(UnfoldedCircleDockEntity, NumberEntity):
    """Class representing an unfolded circle number."""

    entity_description = UNFOLDED_CIRCLE_NUMBER

    def __init__(
        self, coordinator, description: UnfoldedCircleNumberEntityDescription
    ) -> None:
        """Initialize a Number."""
        super().__init__(coordinator)
        self._description = description
        self.coordinator = coordinator
        self.entity_description = description
        self._attr_unique_id = f"{self.coordinator.api.model_number}_{self.coordinator.api.serial_number}_{description.unique_id}"
        self._attr_has_entity_name = True
        self._attr_name = description.name
        key = "_" + description.key
        self._attr_native_value = coordinator.data.get(key)
        self._attr_icon = description.icon
        self._attr_entity_category = description.entity_category
        self._attr_device_class = description.device_class
        self._attr_min_value = description.min_value
        self._attr_max_value = description.max_value

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        # Add websocket events according to corresponding entities
        self.coordinator.subscribe_events["configuration"] = True
        await super().async_added_to_hass()

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        value_int = int(value)
        await self.entity_description.control_fn(self.coordinator, value_int)
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = getattr(
            self.coordinator.api, self.entity_description.key
        )
        self.async_write_ha_state()
