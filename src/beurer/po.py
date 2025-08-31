import logging
import queue

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
        self.bpm = queue.Queue()
        self.spo2 = queue.Queue()
        self.transport.setBpmQueue(self.bpm)
        self.transport.setSpo2Queue(self.spo2)

    def connect(self):
        self.transport.connect(self.hid_path)

    def getBpm(self, block=True):
        return self.bpm.get()

    def bpmAvailable(self):
        return not self.bpm.empty()

    def getSpo2(self, block=True):
        return self.spo2.get()

    def spo2Available(self):
        return not self.spo2.empty()

    def cleanup(self):
        self.transport.disconnect()
