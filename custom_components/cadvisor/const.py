from dataclasses import dataclass
from typing import Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfInformation

DOMAIN: Final = "cadvisor"

DEFAULT_PORT: Final = 8080
DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_TIMEOUT: Final = 10

CONF_SCAN_INTERVAL: Final = "scan_interval"

API_DOCKER_ENDPOINT: Final = "/api/v1.2/docker"
API_MACHINE_ENDPOINT: Final = "/api/v1.0/machine"


@dataclass(frozen=True, kw_only=True)
class CadvisorSensorEntityDescription(SensorEntityDescription):
    """Describes a cAdvisor sensor entity."""

    value_path: str


SENSOR_TYPES: tuple[CadvisorSensorEntityDescription, ...] = (
    CadvisorSensorEntityDescription(
        key="cpu_usage_percent",
        translation_key="cpu_usage_percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:cpu-64-bit",
        value_path="cpu_percent",
    ),
    CadvisorSensorEntityDescription(
        key="memory_usage",
        translation_key="memory_usage",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:memory",
        value_path="memory.usage",
    ),
    CadvisorSensorEntityDescription(
        key="memory_usage_percent",
        translation_key="memory_usage_percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:memory",
        value_path="memory_percent",
    ),
    CadvisorSensorEntityDescription(
        key="memory_limit",
        translation_key="memory_limit",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        entity_registry_enabled_default=False,
        icon="mdi:memory",
        value_path="memory.limit",
    ),
    CadvisorSensorEntityDescription(
        key="network_rx_bytes",
        translation_key="network_rx_bytes",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:download-network",
        value_path="network.rx_bytes",
    ),
    CadvisorSensorEntityDescription(
        key="network_tx_bytes",
        translation_key="network_tx_bytes",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:upload-network",
        value_path="network.tx_bytes",
    ),
    CadvisorSensorEntityDescription(
        key="disk_read_bytes",
        translation_key="disk_read_bytes",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:harddisk",
        value_path="diskio.read",
    ),
    CadvisorSensorEntityDescription(
        key="disk_write_bytes",
        translation_key="disk_write_bytes",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:harddisk",
        value_path="diskio.write",
    ),
    CadvisorSensorEntityDescription(
        key="filesystem_usage",
        translation_key="filesystem_usage",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:folder",
        value_path="filesystem.usage",
    ),
    CadvisorSensorEntityDescription(
        key="filesystem_usage_percent",
        translation_key="filesystem_usage_percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:folder",
        value_path="filesystem_percent",
    ),
    CadvisorSensorEntityDescription(
        key="started",
        translation_key="started",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-start",
        value_path="start_time",
    ),
    CadvisorSensorEntityDescription(
        key="status",
        translation_key="status",
        icon="mdi:docker",
        value_path="status",
    ),
    CadvisorSensorEntityDescription(
        key="image",
        translation_key="image",
        icon="mdi:package-variant",
        value_path="image",
    ),
    CadvisorSensorEntityDescription(
        key="container_id",
        translation_key="container_id",
        icon="mdi:identifier",
        entity_registry_enabled_default=False,
        value_path="container_id_short",
    ),
)
