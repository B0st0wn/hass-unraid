from utils import Preferences

async def var(self, msg_data, create_config):
    self.logger.debug("Array parser triggered")
    msg_data = f'[var]\n{msg_data}'
    prefs = Preferences(msg_data)
    var = prefs.as_dict()
    var_json = var['var']

    var_value = 'OFF'
    if 'started' in var_json['mdstate'].lower():
        var_value = 'ON'

    payload = {
        'name': 'Array',
        'device_class': 'running'
    }

    self.mqtt_publish(payload, 'binary_sensor', var_value, json_attributes=var_json, create_config=create_config)
