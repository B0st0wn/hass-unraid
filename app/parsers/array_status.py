# parsers/array_status.py
import re
import html
import json

async def array_status(self, msg_data, create_config):
    try:
        parsed = json.loads(msg_data)
        html_data = html.unescape(parsed['disk'][0])

        match_text = re.search(r"id=['\"]text-parity['\"]>(\w+)<", html_data)
        match_orb = re.search(r"fa fa-circle orb (\w+-orb)", html_data)

        if match_text:
            state = match_text.group(1).capitalize()
        elif match_orb:
            orb = match_orb.group(1)
            state = "Healthy" if "green" in orb else "Error" if "red" in orb else "Unknown"
        else:
            state = "Unknown"

        payload = {
            "name": "Array",
            "icon": "mdi:server"
        }

        self.mqtt_publish(payload, "sensor", state, create_config=create_config)

    except Exception:
        self.logger.exception("[array_status] Failed to parse array health")
