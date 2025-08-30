import logging

from beurer.transport.transport import TransportType
from beurer.transport.hid import HID

logger = logging.getLogger(__name__)

def discover():
    # We only support USB HID
    transport = HID()
    # Beurer devices reuse the Vendor ID from the
    # GigaDevice microcontroller the device is based on
    transport.setVID([0x28e9])
    transport.setPID([0x028a])

    hids = transport.discover()
    devices = []
    for hid in hids:
        vid = hid['vendor_id']
        pid = hid['product_id']
        path = hid['path']
        product_string = hid['product_string']
        logger.info(f'Found HID device \'{product_string}\' ({hex(vid)},{hex(pid)},{path.decode('utf-8')})')
        devices.append(BeurerPO(path))

    return devices

class BeurerPO:
    """
    Beurer PulseOximeter Device
    """
    def __init__(self, hid_path):
        self.transport = HID()
        self.hid_path = hid_path

    def connect(self):
        self.transport.connect(self.hid_path)

    def getData(self):
        return 0

    def cleanup(self):
        self.transport.disconnect()
