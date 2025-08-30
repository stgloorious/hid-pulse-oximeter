#!/usr/bin/env python3

import hid
import sys
import binascii
import time

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

from beurer.po import discover

running = True

logger.info('Discovering devices...')
devices = discover()

if len(devices) == 0:
    logger.error('No supported devices found')
    sys.exit(1)

logger.info('Connecting to first device')
device = devices[0]
device.connect()

try:
    while True:
        device.getData()
except KeyboardInterrupt:
    device.cleanup()


