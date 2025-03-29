import psutil
from utils import Preferences

async def cpu_temperature_avg(self, create_config):
    temps = psutil.sensors_temperatures()
    if not temps:
        return
    all_temps = [entry.current for chip in temps.values() for entry in chip if hasattr(entry, 'current')]
    if not all_temps:
        return
    avg_temp = round(sum(all_temps) / len(all_temps), 1)
    payload = {
        'name': 'CPU Temperature',
        'unit_of_measurement': '°C',
        'device_class': 'temperature',
        'icon': 'mdi:chip',
        'state_class': 'measurement'
    }
    self.mqtt_publish(payload, 'sensor', avg_temp, create_config=create_config, retain=True)

async def cpuload(self, msg_data, create_config):
    prefs = Preferences(msg_data)
    state_value = int(prefs.as_dict()['cpu']['host'])
    payload = {
        'name': 'CPU Utilization',
        'unit_of_measurement': '%',
        'icon': 'mdi:chip',
        'state_class': 'measurement'
    }
    self.mqtt_publish(payload, 'sensor', state_value, create_config=create_config)
