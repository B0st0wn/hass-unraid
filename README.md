# hass-unraid — Unraid → Home Assistant via MQTT (Fork by B0st0wn)

This container monitors your Unraid server and publishes metrics to MQTT so Home Assistant can discover and display your server status, Docker containers, VMs, and more.

> **This repo is a fork of `IDmedia/hass-unraid`.** It keeps the same goal but adds comprehensive GraphQL support and enhanced monitoring capabilities.

---

## What's different in this fork

* **GraphQL Support (NEW!)**: Native Unraid 7.2+ GraphQL API integration for more comprehensive and structured data
* **Docker Container Monitoring**: Binary sensors for each container showing running/stopped state with detailed attributes
* **Enhanced VM Monitoring**: Improved state detection, vCPU, memory, and architecture information
* **Modular parsers**: the original single parser file is split for readability and maintenance (e.g., `systems.py`, `disks.py`, `shares.py`, `vms.py`).
* **Bug fixes & robustness** for my environment (Unraid and network idiosyncrasies), especially around inconsistent WebSocket payloads and reconnect behavior.
* **Broader data coverage** including array status, parity checks, UPS monitoring, and share usage
* **Dual mode operation**: Choose between GraphQL (recommended) or legacy WebSocket mode

> **Privacy note:** All examples below use placeholders like `<UNRAID_HOST>`, `<MQTT_HOST>`, and `<SERVER_NAME>` — replace with your values.

---

## Requirements

* Unraid **7.2+** with GraphQL API (recommended) or **7.x+** with WebSocket endpoints
* An MQTT broker reachable from the container
* Home Assistant with the MQTT integration (auto discovery recommended)
* Unraid API key (for GraphQL mode - highly recommended)

---

## Quick start

### 1) Configuration file

Create `./data/config.yaml` next to your compose file:

```yaml
unraid:
  - name: <SERVER_NAME>
    host: <UNRAID_HOST>
    port: 443
    ssl: true
    username: <UNRAID_USER>
    password: <UNRAID_PASSWORD>
    api_key: <UNRAID_API_KEY>  # Required for GraphQL mode
    scan_interval: 30
    ups_scan_interval: 15      # Optional: UPS refresh interval (default: 30)
    system_scan_interval: 15   # Optional: System metrics refresh interval (default: 30)

mqtt:
  host: <MQTT_HOST>
  port: 1883
  username: <MQTT_USER>
  password: <MQTT_PASSWORD>
```

> **New in this fork**: Add `api_key` for GraphQL mode (Unraid 7.2+). Generate it at Settings → Management Access → API Keys.
>
> You can define multiple Unraid servers by adding more entries under `unraid:`.

### 2) Docker Compose

```yaml
services:
  hass-unraid:
    build: .
    container_name: hass-unraid
    restart: always
    network_mode: bridge
    environment:
      - TZ=<YOUR_TZ>
      - USE_GRAPHQL=true           # Set to false for legacy WebSocket mode
      - UPS_SCAN_INTERVAL=15       # Optional: UPS refresh rate in seconds (overrides config)
      - SYSTEM_SCAN_INTERVAL=15    # Optional: System metrics refresh rate in seconds (overrides config)
    volumes:
      - ./data:/data
```

> **GraphQL mode** (default, recommended): Set `USE_GRAPHQL=true` and provide an API key
>
> **WebSocket mode** (legacy): Set `USE_GRAPHQL=false` for older Unraid versions
>
> **Real-time updates**: Set `UPS_SCAN_INTERVAL` and `SYSTEM_SCAN_INTERVAL` to 10-15 seconds for near real-time monitoring of critical metrics (UPS battery, CPU, RAM, temperatures). Environment variables override config.yaml values.
>
> If you prefer `docker run`, mirror the same bind mount (`-v $(pwd)/data:/data`) and env.

### 3) Verify in Home Assistant

After a minute, check **Settings → Devices & Services → MQTT**. A device for `<SERVER_NAME>` should appear with sensors/entities. If not, inspect container logs.

---

## MQTT topics & entities (high level)

The container publishes under a server-specific prefix, commonly:

```
unraid/<SERVER_NAME>/...
```

### GraphQL Mode Sensors (Unraid 7.2+)

* **Docker Containers** (NEW!):
  * `binary_sensor.docker_<container>_state` – Running/stopped state
  * Attributes: container ID, image, status, auto-start, port mappings

* **Virtual Machines**:
  * `binary_sensor.vm_<name>_state` – Running/stopped/paused state
  * `sensor.vm_<name>_vcpus` – Virtual CPU count
  * `sensor.vm_<name>_memory` – Memory allocation (MB)
  * Attributes: UUID, architecture, emulator

* **Array & Parity**:
  * `sensor.array_state` – Array state (STARTED, STOPPED, etc.)
  * `sensor.array_usage` – Array usage percentage
  * `sensor.parity_<name>_status` – Parity disk status
  * `sensor.last_parity_check` – Last parity check results

* **Disks & Shares**:
  * `sensor.disk_<name>_*` – Temperature, usage, status
  * `sensor.share_<name>_usage` – Share usage percentage

* **UPS** (if available):
  * `sensor.ups_<name>_battery` – Battery level (%)
  * `sensor.ups_<name>_load` – Load percentage
  * `sensor.ups_<name>_runtime` – Estimated runtime (minutes)

* **System**:
  * `sensor.cpu_temperature` – CPU temperature
  * `sensor.cpu_utilization` – CPU usage %
  * `sensor.system_uptime` – Server uptime

### WebSocket Mode Sensors (Legacy)

Similar sensors without Docker/VM running state detection. See [GRAPHQL_MIGRATION.md](GRAPHQL_MIGRATION.md) for details.

> Use MQTT Explorer to browse live topics and see all available sensors.

---

---

## Repo layout (fork)

```
app/
  systems.py        # system/array parsing → MQTT
  disks.py          # disk/SMART parsing → MQTT
  shares.py         # share metrics → MQTT
  vms.py            # VM metrics → MQTT
  ... (helpers, client, main)
extras/
  ... (compose, helper scripts)
Dockerfile
README.md
```

---

## Home Assistant dashboard templates

The `templates/` folder contains copy/paste examples for the **modern Home Assistant dashboard editor** (a.k.a. “storage mode”, the default as of 2025). Even though the files are written as YAML for readability, each file mirrors the JSON structure that the HA GUI expects, so you can open the file, copy everything, and paste it directly into the *Raw configuration editor* of any dashboard.

Available templates:

* `unraid_power_dashboard.yaml` – tile-based UPS board with gauges, trend tiles, and a conditional alert.
* `unraid_power_compact_dashboard.yaml` – text/tile hybrid UPS summary similar to the NAS stats card.
* `unraid_nas_stats_dashboard.yaml` – Markdown-driven NAS overview (uptime, array health, log usage, cache, disk loop).
* `unraid_overview_dashboard.yaml` – combines the NAS card and the UPS board into one page for “at a glance” monitoring.

To use any template:

1. In Home Assistant go to **Settings → Dashboards**, create (or open) a dashboard, choose **Edit dashboard**, then **Raw configuration editor**.
2. Paste the contents of the template file. If you only want a single view, replace the whole document; otherwise merge just the `views:` entries into your existing JSON.
3. Replace the placeholder entity IDs (the files use `sensor.nas_*`) with the IDs that match your MQTT discovery entities. For the NAS card you can also adjust the disk list (`[1,2,3,4]`) or add parity/cache rows.
4. Save. The GUI will convert the YAML into the native storage JSON and the new cards will appear instantly.

---

## Troubleshooting

* **No MQTT device in HA**: confirm broker creds, that `Home Assistant → MQTT` is connected, and that the container can reach `<MQTT_HOST>`.
* **Missing entities**: browse actual topics with MQTT Explorer to verify publish; some fields only appear when the related Unraid feature is active.
* **WebSocket drops**: check Unraid auth/session timeout; consider increasing `scan_interval` slightly; verify reverse proxies aren’t buffering long-running WS.

---

---

## Credits

* Original author(s): IDmedia and contributors.
* This fork focuses on structure, resilience, and extra telemetry for Home Assistant.
