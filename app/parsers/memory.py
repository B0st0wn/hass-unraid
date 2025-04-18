import re

async def update1(self, msg_data, create_config):
    memory_categories = ['RAM', 'Flash', 'Log', 'Docker']
    matches = re.findall(r'(\d+(?:\.\d+)?\s*%)', msg_data)
    print("=== update1 msg_data ===")
    print(msg_data)


    for memory_name, memory_usage in zip(memory_categories, matches):
        memory_value = ''.join(c for c in memory_usage if c.isdigit())
        if memory_value:
            memory_value = int(memory_value)
            payload = {
                'name': f'{memory_name} Usage',
                'unit_of_measurement': '%',
                'icon': 'mdi:memory',
                'state_class': 'measurement'
            }
            self.mqtt_publish(payload, 'sensor', memory_value, create_config=create_config)

    for fan_id, fan_rpm in enumerate(re.findall(r'(\d+)\s*RPM', msg_data)):
        fan_id += 1
        fan_name = f'Fan {fan_id}'
        fan_value = ''.join(c for c in fan_rpm if c.isdigit())
        if fan_value:
            fan_value = int(fan_value)
            payload = {
                'name': f'{fan_name} Speed',
                'unit_of_measurement': 'RPM',
                'icon': 'mdi:fan',
                'state_class': 'measurement'
            }
            self.mqtt_publish(payload, 'sensor', fan_value, create_config=create_config)
