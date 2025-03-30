# parsers/array_status.py
import httpx

async def array_status(self, msg_data, create_config):
    self.logger.debug("[array_status] HTTP polling array state...")

    try:
        async with httpx.AsyncClient() as http:
            headers = {'Cookie': self.unraid_cookie}
            r = await http.get(f'{self.unraid_url}/plugins/mdStatus.php', headers=headers)
            data = r.json()

            mdstate = data.get("mdState", "unknown")
            var_value = 'ON' if mdstate == 'started' else 'OFF'

            payload = {
                'name': 'Array',
                'device_class': 'running'
            }

            self.logger.debug(f"[array_status] mdState: {mdstate}")
            self.mqtt_publish(payload, 'binary_sensor', var_value, json_attributes=data, create_config=create_config)

    except Exception:
        self.logger.exception("[array_status] Failed to poll array state")
