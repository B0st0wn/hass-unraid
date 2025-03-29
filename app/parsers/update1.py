from utils import Preferences
from parsers.array import parse_array
from parsers.memory import parse_memory

async def update1(self, msg_data, create_config):
    self.logger.debug("update1 parser triggered")
    prefs = Preferences(f'[update1]\n{msg_data}')
    parsed = prefs.as_dict().get('update1', {})

    await parse_array(self, parsed, create_config)
    await parse_memory(self, parsed, create_config)
