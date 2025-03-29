import json

async def docker(self, msg_data, create_config):
    self.logger.debug("Docker parser triggered")

    if not msg_data.strip():
        self.logger.error("Received empty Docker msg_data")
        return

    try:
        data = json.loads(msg_data)
    except json.JSONDecodeError as e:
        self.logger.error(f"Failed to parse Docker msg_data: {e}")
        self.logger.debug(f"Docker raw msg_data:\n{msg_data}")
        return

    for name, info in data.items():
        payload = {
            'name': f'Docker {name}',
            'icon': 'mdi:docker'
        }
        state = 'running' if info.get('running') else 'stopped'
        self.mqtt_publish(payload, 'sensor', state, json_attributes=info, create_config=create_config)
