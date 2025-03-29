import re
import math
import httpx
from lxml import etree
from utils import Preferences
from humanfriendly import parse_size
import time
import psutil

from parsers.uptime import system_uptime
from parsers.cpu import cpu_temperature_avg, cpuload
from parsers.memory import update1
from parsers.network import update3
from parsers.tempsensors import temperature
from parsers.parity import parity
from parsers.array import var
from parsers.disks import disks
from parsers.shares import shares
from parsers.vms import vms

async def default(self, msg_data, create_config):
    pass

async def session(self, msg_data, create_config):
    self.csrf_token = msg_data
