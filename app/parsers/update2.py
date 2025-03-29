from utils import Preferences

async def update2(self, msg_data, create_config):
    self.logger.debug("update2 parser triggered")
    prefs = Preferences(f'[update2]\n{msg_data}')
    parsed = prefs.as_dict().get('update2', {})

    self.logger.debug(f"Parsed update2 data:\n{parsed}")

    for key, value in parsed.items():
        payload = {
            'name': f'Update2 {key}',
            'icon': 'mdi:information-outline'
        }
        self.mqtt_publish(payload, 'sensor', value, create_config=create_config)
