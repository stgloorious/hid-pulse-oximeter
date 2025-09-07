#!/usr/bin/env python3
"""
Example script that connects to the Beurer PO 80 pulse oximeter over USB HID
and prints out live BPM and SpO2 values.
"""

import sys
import logging

from beurer.po import discover

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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
        if device.bpm_available() and device.spo2_available():
            logger.info('BPM: %s SpO2: %s%%', device.get_bpm(), device.get_spo2())

except KeyboardInterrupt:
    device.cleanup()
