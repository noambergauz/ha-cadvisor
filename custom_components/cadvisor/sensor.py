import re
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CadvisorConfigEntry
from .const import DOMAIN, SENSOR_TYPES, CadvisorSensorEntityDescription
from .coordinator import CadvisorCoordinator, ContainerStats


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CadvisorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up cAdvisor sensors based on a config entry."""
    coordinator = entry.runtime_data

    entities: list[CadvisorSensor] = []
    for _container_id, container in coordinator.data.containers.items():
        for description in SENSOR_TYPES:
            entities.append(CadvisorSensor(coordinator, entry.entry_id, container, description))

    async_add_entities(entities)


def _sanitize_id(value: str) -> str:
    """Sanitize a string for use in entity IDs."""
    return re.sub(r"[^a-z0-9_]", "_", value.lower())


class CadvisorSensor(CoordinatorEntity[CadvisorCoordinator], SensorEntity):
    """Representation of a cAdvisor sensor."""

    entity_description: CadvisorSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CadvisorCoordinator,
        entry_id: str,
        container: ContainerStats,
        description: CadvisorSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._container_id = container.container_id
        self._attr_unique_id = (
            f"{entry_id}_{_sanitize_id(container.container_id)}_{description.key}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, container.container_id)},
            name=container.name,
            manufacturer="Docker",
            model=container.image,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and self.coordinator.data is not None
            and self._container_id in self.coordinator.data.containers
        )

    @property
    def native_value(self) -> float | int | datetime | str | None:
        """Return the state of the sensor."""
        if not self.available:
            return None

        container = self.coordinator.data.containers.get(self._container_id)
        if not container:
            return None

        value = self._get_value(container, self.entity_description.value_path)

        # Convert ISO timestamp string to datetime for timestamp sensors
        if self.entity_description.key == "started" and isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None

        # Status sensor always returns "running" if container is in data
        if self.entity_description.key == "status":
            return "running"

        # Container ID sensor returns short ID (first 12 chars)
        if self.entity_description.key == "container_id":
            return container.container_id[:12]

        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self.available:
            return None

        container = self.coordinator.data.containers.get(self._container_id)
        if not container:
            return None

        # Only add labels attribute to the status sensor
        if self.entity_description.key != "status":
            return None

        if container.labels:
            return {"labels": container.labels}

        return None

    def _get_value(self, container: ContainerStats, path: str) -> Any:
        """Get value from container stats using dot-notation path."""
        parts = path.split(".")
        value: Any = container

        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            elif isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value
