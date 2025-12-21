import re


def _normalize_memory_label(label: str):
    label = label.strip().lower()
    if label in ('ram', 'memory'):
        return 'RAM'
    if label in ('flash', 'boot'):
        return 'Flash'
    if label in ('log', 'logs', 'syslog'):
        return 'Log'
    if label in ('docker', 'containers'):
        return 'Docker'
    return None


def _extract_labeled_percentages(text: str):
    cleaned = re.sub(r'<[^>]+>', ' ', text)
    pattern = re.compile(r'(RAM|Memory|Flash|Log|Logs|Syslog|Docker|Containers)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*%', re.IGNORECASE)
    matches = pattern.findall(cleaned)
    labeled = {}
    for label, value in matches:
        normalized = _normalize_memory_label(label)
        if not normalized:
            continue
        labeled[normalized] = int(float(value))
    return labeled


async def update1(self, msg_data, create_config):
    memory_categories = ['RAM', 'Flash', 'Log', 'Docker']
    labeled = _extract_labeled_percentages(msg_data)
    matches = re.findall(r'(\d+(?:\.\d+)?\s*%)', msg_data)

    if labeled:
        for memory_name, memory_value in labeled.items():
            payload = {
                'name': f'{memory_name} Usage',
                'unit_of_measurement': '%',
                'icon': 'mdi:memory',
                'state_class': 'measurement'
            }
            self.mqtt_publish(payload, 'sensor', memory_value, create_config=create_config)
    else:
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

    if not labeled and not matches:
        self.logger.warning('[update1] No memory usage percentages found in payload')

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
