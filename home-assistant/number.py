"""Emmesteel Power Level Entity."""

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import CMD_POWER_DN, CMD_POWER_UP, CONF_PROXY, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Emmesteel power level."""
    async_add_entities([EmmesteelPower(hass, entry)], True)


class EmmesteelPower(NumberEntity):
    """Representation of an Emmesteel towel warmer switch."""

    _attr_icon = "mdi:radiator"
    _attr_supported_features = None
    _attr_preset_modes = []

    def __init__(self, hass, entry) -> None:
        """Initialize the power level."""

        self.hass = hass

        self._api = hass.data[DOMAIN][entry.entry_id]
        self._proxy = entry.data[CONF_PROXY]

        self._name = "Emmesteel Towel Warmer Power Level"
        self._attr_mode = "box" 
        self._attr_unique_id = f"emmesteel-power-proxy-{self._proxy}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._proxy)},
            name=self._name,
            manufacturer="Emmesteel",
        )

        # Levels
        self._native_value = 5  # initial power level
        self._native_step = 1
        self._native_min_value = 1
        self._native_max_value = 5

    @property
    def name(self):
        """Return the name of the number entity."""
        return self._name

    @property
    def native_value(self):
        """Return the current power level."""
        return self._native_value

    @property
    def native_min_value(self):
        """Return the minimum power level."""
        return self._native_min_value

    @property
    def native_max_value(self):
        """Return the maximum power level."""
        return self._native_max_value

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the device."""
        return {"proxy": self._proxy}

    @property
    def native_step(self):
        """Return the incremental step size."""
        return self._native_step

    async def async_set_native_value(self, value: float) -> None:
        """Set a new power level via the UI."""
        desired_value = int(value)

        delta = desired_value - (self._native_value or 0)
        cmd = CMD_POWER_UP if delta > 0 else CMD_POWER_DN
        _LOGGER.debug(
            "Setting Emmesteel power level to: %s (current= %s)",
            desired_value,
            self._native_value,
        )

        for _ in range(abs(delta)):
            state = await self._api.send_cmd(cmd)

        self._native_value = state.level
        self.async_write_ha_state()

    async def async_power_up(self, **kwargs):
        """Increase Power."""
        _LOGGER.debug(f"Increasing power (value={self._native_value})")
        updated_state = await self._api.send_cmd(CMD_POWER_UP)
        self._is_on = updated_state.is_on
        self._native_value = updated_state.level
        self.async_write_ha_state()

    async def async_power_down(self, **kwargs):
        """Decrease Power."""
        _LOGGER.debug(f"Decreasing power (value={self._native_value})")
        updated_state = await self._api.send_cmd(CMD_POWER_DN)
        self._is_on = updated_state.is_on
        self._native_value = updated_state.level
        self.async_write_ha_state()

    async def async_update(self):
        """Fetch new state data for the switch."""
        state = await self._api.get_state()
        self._native_value = state.level or 0
        _LOGGER.debug("Emmesteel towel warmer state updated: %s", state)
