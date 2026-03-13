from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from . import CadvisorConfigEntry

REDACT_KEYS = {CONF_HOST, "host", "ip", "address"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: CadvisorConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data

    containers_data = {}
    if coordinator.data:
        for container_id, container in coordinator.data.containers.items():
            containers_data[container_id[:12]] = {
                "name": container.name,
                "image": container.image,
                "cpu_percent": container.cpu_percent,
                "memory_percent": container.memory_percent,
                "memory_usage": container.memory.get("usage"),
                "memory_limit": container.memory.get("limit"),
            }

    return {
        "config_entry": async_redact_data(dict(entry.data), REDACT_KEYS),
        "options": dict(entry.options),
        "container_count": len(containers_data),
        "containers": containers_data,
    }
