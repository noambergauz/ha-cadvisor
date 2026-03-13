# Home Assistant cAdvisor Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Monitor Docker containers in Home Assistant using [cAdvisor](https://github.com/google/cadvisor).

## Features

- Auto-discovers all Docker containers
- Creates a device per container with grouped sensors
- Monitors CPU, memory, network I/O, disk I/O, and filesystem usage
- Configurable scan interval

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant
2. Go to **Integrations** → **⋮** → **Custom repositories**
3. Add this repository URL and select **Integration**
4. Install "cAdvisor"
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/cadvisor` folder to your `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "cAdvisor"
3. Enter your cAdvisor host and port (default: 8080)

## cAdvisor Setup

Run cAdvisor as a Docker container:

```yaml
services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    restart: always
```

## Sensors

Each container exposes the following sensors:

| Sensor | Description |
|--------|-------------|
| CPU usage | CPU usage percentage |
| Memory usage | Memory usage in bytes |
| Memory usage percent | Memory usage percentage |
| Memory limit | Memory limit in bytes |
| Network received | Total bytes received |
| Network transmitted | Total bytes transmitted |
| Disk read | Total disk bytes read |
| Disk write | Total disk bytes written |
| Filesystem usage | Filesystem usage in bytes |
| Filesystem usage percent | Filesystem usage percentage |
| Started | Container start timestamp (shows uptime) |
| Status | Container running status |
| Image | Docker image name and tag |
| Container ID | Short container ID (disabled by default) |

## Binary Sensors

| Binary Sensor | Description |
|---------------|-------------|
| Running | On when container is running, off when stopped |

The Status sensor includes Docker labels as attributes (if any).

## Options

- **Scan interval** — How often to poll cAdvisor (default: 30 seconds, min: 10, max: 300)

## Troubleshooting

1. Ensure cAdvisor is accessible from Home Assistant
2. Check that the port mapping is correct
3. View Home Assistant logs for error messages

## License

MIT
