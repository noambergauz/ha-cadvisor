import re

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CadvisorConfigEntry
from .const import DOMAIN
from .coordinator import CadvisorCoordinator, ContainerStats


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CadvisorConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up cAdvisor binary sensors based on a config entry."""
    coordinator = entry.runtime_data

    entities: list[ContainerRunningSensor] = []
    for _container_id, container in coordinator.data.containers.items():
        entities.append(ContainerRunningSensor(coordinator, entry.entry_id, container))

    async_add_entities(entities)


def _sanitize_id(value: str) -> str:
    """Sanitize a string for use in entity IDs."""
    return re.sub(r"[^a-z0-9_]", "_", value.lower())


class ContainerRunningSensor(CoordinatorEntity[CadvisorCoordinator], BinarySensorEntity):
    """Binary sensor indicating if a container is running."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_translation_key = "running"

    def __init__(
        self,
        coordinator: CadvisorCoordinator,
        entry_id: str,
        container: ContainerStats,
    ) -> None:
        super().__init__(coordinator)
        self._container_id = container.container_id
        self._attr_unique_id = f"{entry_id}_{_sanitize_id(container.container_id)}_running"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, container.container_id)},
            name=container.name,
            manufacturer="Docker",
            model=container.image,
        )

    @property
    def is_on(self) -> bool:
        """Return true if the container is running."""
        return (
            self.coordinator.data is not None
            and self._container_id in self.coordinator.data.containers
        )

    @property
    def available(self) -> bool:
        """Return if entity is available (coordinator is working)."""
        return self.coordinator.last_update_success
