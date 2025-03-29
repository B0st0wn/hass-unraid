from utils import Preferences

async def var(self, msg_data, create_config):
    self.logger.debug("Array parser triggered")
    prefs = Preferences(f'[var]\n{msg_data}')
    parsed = prefs.as_dict().get('var', {})

    var_value = 'OFF'
    if 'mdstate' in parsed and 'started' in parsed['mdstate'].lower():
        var_value = 'ON'

    payload = {
        'name': 'Array',
        'device_class': 'running'
    }

    self.mqtt_publish(payload, 'binary_sensor', var_value, json_attributes=parsed, create_config=create_config)
