import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_DOCKER_ENDPOINT, API_MACHINE_ENDPOINT, DEFAULT_TIMEOUT, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class ContainerStats:
    """Parsed container statistics."""

    container_id: str
    name: str
    image: str
    cpu_percent: float | None
    memory: dict[str, int]
    memory_percent: float | None
    network: dict[str, int]
    diskio: dict[str, int]
    filesystem: dict[str, int]
    filesystem_percent: float | None


@dataclass
class CadvisorData:
    """Data returned by the coordinator."""

    containers: dict[str, ContainerStats]
    machine_info: dict[str, Any]


class CadvisorApiClient:
    """API client for cAdvisor."""

    def __init__(self, host: str, port: int, session: aiohttp.ClientSession) -> None:
        self._base_url = f"http://{host}:{port}"
        self._session = session
        self._previous_stats: dict[str, dict[str, Any]] = {}

    async def test_connection(self) -> bool:
        """Test connection to cAdvisor."""
        try:
            async with self._session.get(
                f"{self._base_url}{API_MACHINE_ENDPOINT}",
                timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT),
            ) as response:
                response.raise_for_status()
                return True
        except (aiohttp.ClientError, TimeoutError):
            return False

    async def get_machine_info(self) -> dict[str, Any]:
        """Get machine information."""
        async with self._session.get(
            f"{self._base_url}{API_MACHINE_ENDPOINT}",
            timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT),
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def get_containers(self, num_cores: int) -> dict[str, ContainerStats]:
        """Fetch and parse container statistics."""
        async with self._session.get(
            f"{self._base_url}{API_DOCKER_ENDPOINT}",
            timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT),
        ) as response:
            response.raise_for_status()
            data = await response.json()

        containers: dict[str, ContainerStats] = {}
        for container_path, container_info in data.items():
            stats = self._parse_container(container_path, container_info, num_cores)
            if stats:
                containers[stats.container_id] = stats

        return containers

    def _parse_container(
        self, container_path: str, info: dict[str, Any], num_cores: int
    ) -> ContainerStats | None:
        """Parse a single container's data."""
        if not info.get("stats"):
            return None

        container_id = info.get("id", "")
        if not container_id:
            return None

        aliases = info.get("aliases", [])
        name = aliases[0] if aliases else container_id[:12]
        image = info.get("spec", {}).get("image", "unknown")

        latest_stats = info["stats"][-1]
        cpu_percent = self._calculate_cpu_percent(container_id, info["stats"], num_cores)
        memory = self._parse_memory(latest_stats)
        memory_percent = self._calculate_memory_percent(memory)
        network = self._parse_network(latest_stats)
        diskio = self._parse_diskio(latest_stats)
        filesystem = self._parse_filesystem(latest_stats)
        filesystem_percent = self._calculate_filesystem_percent(filesystem)

        return ContainerStats(
            container_id=container_id,
            name=name,
            image=image,
            cpu_percent=cpu_percent,
            memory=memory,
            memory_percent=memory_percent,
            network=network,
            diskio=diskio,
            filesystem=filesystem,
            filesystem_percent=filesystem_percent,
        )

    def _calculate_cpu_percent(
        self, container_id: str, stats: list[dict[str, Any]], num_cores: int
    ) -> float | None:
        """Calculate CPU usage percentage from cumulative nanoseconds."""
        if len(stats) < 2:
            return None

        prev = stats[-2]
        curr = stats[-1]

        try:
            prev_cpu = prev["cpu"]["usage"]["total"]
            curr_cpu = curr["cpu"]["usage"]["total"]
            prev_time = prev["timestamp"]
            curr_time = curr["timestamp"]

            # Parse ISO timestamps and calculate delta in nanoseconds
            from datetime import datetime

            prev_dt = datetime.fromisoformat(prev_time.replace("Z", "+00:00"))
            curr_dt = datetime.fromisoformat(curr_time.replace("Z", "+00:00"))
            time_delta_ns = (curr_dt - prev_dt).total_seconds() * 1_000_000_000

            if time_delta_ns <= 0:
                return None

            cpu_delta = curr_cpu - prev_cpu
            cpu_percent = (cpu_delta / time_delta_ns) * 100 * num_cores
            return max(0.0, min(100.0 * num_cores, cpu_percent))
        except (KeyError, TypeError, ValueError):
            return None

    def _parse_memory(self, stats: dict[str, Any]) -> dict[str, int]:
        """Parse memory statistics."""
        memory = stats.get("memory", {})
        return {
            "usage": memory.get("usage", 0),
            "limit": memory.get("limit", 0),
            "working_set": memory.get("working_set", 0),
        }

    def _calculate_memory_percent(self, memory: dict[str, int]) -> float | None:
        """Calculate memory usage percentage."""
        usage = memory.get("usage", 0)
        limit = memory.get("limit", 0)
        if limit > 0:
            return (usage / limit) * 100
        return None

    def _parse_network(self, stats: dict[str, Any]) -> dict[str, int]:
        """Parse network statistics (aggregate all interfaces)."""
        network = stats.get("network", {})
        interfaces = network.get("interfaces", [])

        rx_bytes = 0
        tx_bytes = 0
        for iface in interfaces:
            rx_bytes += iface.get("rx_bytes", 0)
            tx_bytes += iface.get("tx_bytes", 0)

        return {"rx_bytes": rx_bytes, "tx_bytes": tx_bytes}

    def _parse_diskio(self, stats: dict[str, Any]) -> dict[str, int]:
        """Parse disk I/O statistics."""
        diskio = stats.get("diskio", {})
        io_service_bytes = diskio.get("io_service_bytes", [])

        read_bytes = 0
        write_bytes = 0
        for device in io_service_bytes:
            device_stats = device.get("stats", {})
            read_bytes += device_stats.get("Read", 0)
            write_bytes += device_stats.get("Write", 0)

        return {"read": read_bytes, "write": write_bytes}

    def _parse_filesystem(self, stats: dict[str, Any]) -> dict[str, int]:
        """Parse filesystem statistics (use first/root filesystem)."""
        filesystems = stats.get("filesystem", [])
        if not filesystems:
            return {"usage": 0, "capacity": 0}

        fs = filesystems[0]
        return {
            "usage": fs.get("usage", 0),
            "capacity": fs.get("capacity", 0),
        }

    def _calculate_filesystem_percent(self, filesystem: dict[str, int]) -> float | None:
        """Calculate filesystem usage percentage."""
        usage = filesystem.get("usage", 0)
        capacity = filesystem.get("capacity", 0)
        if capacity > 0:
            return (usage / capacity) * 100
        return None


class CadvisorCoordinator(DataUpdateCoordinator[CadvisorData]):
    """Coordinator to fetch data from cAdvisor."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: CadvisorApiClient,
        update_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )
        self.client = client
        self._machine_info: dict[str, Any] = {}

    async def _async_update_data(self) -> CadvisorData:
        """Fetch data from cAdvisor API."""
        try:
            if not self._machine_info:
                self._machine_info = await self.client.get_machine_info()

            num_cores = self._machine_info.get("num_cores", 1)
            containers = await self.client.get_containers(num_cores)

            return CadvisorData(
                containers=containers,
                machine_info=self._machine_info,
            )
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with cAdvisor: {err}") from err
        except TimeoutError as err:
            raise UpdateFailed("Timeout communicating with cAdvisor") from err
