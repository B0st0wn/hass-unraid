# hass-unraid — Unraid → Home Assistant via MQTT (Fork by B0st0wn)

This container listens to Unraid’s WebSocket(s), parses events/metrics, and publishes them to MQTT so Home Assistant can discover and display your server.

> **This repo is a fork of `IDmedia/hass-unraid`.** It keeps the same goal but restructures and tweaks the code to better fit my setup.

---

## What’s different in this fork

* **Modular parsers**: the original single parser file is split for readability and maintenance (e.g., `systems.py`, `disks.py`, `shares.py`, `vms.py`).
* **Bug fixes & robustness** for my environment (Unraid and network idiosyncrasies), especially around inconsistent WebSocket payloads and reconnect behavior.
* **Broader WebSocket coverage** (e.g., Docker/vars/update streams) and **more MQTT fields** where they were missing or unstable.
* **VM telemetry** published to MQTT (power state, vCPU count, memory usage, IP addresses), enabling HA dashboards/automations.
* **Optional NIC speed sensors** published to MQTT for monitoring link rates.

> **Privacy note:** All examples below use placeholders like `<UNRAID_HOST>`, `<MQTT_HOST>`, and `<SERVER_NAME>` — replace with your values.

---

## Requirements

* Unraid **7.x+** with WebSocket endpoints enabled (default).
* An MQTT broker reachable from the container.
* Home Assistant with the MQTT integration (auto discovery recommended).

---

## Quick start

### 1) Configuration file

Create `./data/config.yaml` next to your compose file:

```yaml
unraid:
  - name: <SERVER_NAME>
    host: <UNRAID_HOST>
    port: 80
    ssl: false
    username: <UNRAID_USER>
    password: <UNRAID_PASSWORD>
    scan_interval: 30

mqtt:
  host: <MQTT_HOST>
  port: 1883
  username: <MQTT_USER>
  password: <MQTT_PASSWORD>
```

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
    volumes:
      - ./data:/data
```

> If you prefer `docker run`, mirror the same bind mount (`-v $(pwd)/data:/data`) and env.

### 3) Verify in Home Assistant

After a minute, check **Settings → Devices & Services → MQTT**. A device for `<SERVER_NAME>` should appear with sensors/entities. If not, inspect container logs.

---

## MQTT topics & entities (high level)

The container publishes under a server-specific prefix, commonly:

```
unraid/<SERVER_NAME>/...
```

Examples (entity support depends on Unraid state and enabled streams):

* `.../system/*` – CPU, RAM, uptime, array state
* `.../disks/<disk_id>/*` – temps, SMART flags, spin state, utilization
* `.../shares/<share_name>/*` – size, usage
* `.../docker/<container>/*` – status, CPU/RAM
* `.../vms/<vm_name>/*` – power state, vCPU, mem use, IPs
* `.../network/*` – link speed, carrier (optional)

> Topic naming may differ slightly from upstream where fixes/features were added; use MQTT Explorer to browse live topics.

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
