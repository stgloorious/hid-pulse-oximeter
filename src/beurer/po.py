"""
Class representing the Beurer pulse oximeter device
"""

import logging
import queue

from beurer.transport.usb_hid import HID

logger = logging.getLogger(__name__)

def discover():
    """
    Discover connected Beurer devices over USB HID and return them
    in a list of BeurerPO objects.
    """
    # We only support USB HID
    transport = HID()
    # Beurer devices reuse the Vendor ID from the
    # GigaDevice microcontroller the device is based on
    transport.set_vids([0x28e9])
    transport.set_pids([0x028a])

    hids = transport.discover()
    devices = []
    for hid in hids:
        vid = hid['vendor_id']
        pid = hid['product_id']
        path = hid['path'].decode('utf-8')
        ps = hid['product_string']
        logger.info('Found HID device \'%s\' (%s, %s, %s)', ps, hex(vid), hex(pid), path)
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
        self.transport.set_bpm_queue(self.bpm)
        self.transport.set_spo2_queue(self.spo2)

    def connect(self):
        """
        Connect to the physical device this object represents.
        """
        self.transport.connect(self.hid_path)

    def get_bpm(self):
        """
        Return all stored bpm (beats per minute) values and remove them
        from the queue.
        """
        return self.bpm.get()

    def bpm_available(self):
        """
        Check whether the bpm queues holds a non-zero number of new values
        """
        return not self.bpm.empty()

    def get_spo2(self):
        """
        Return all stored SpO2 values and remove them from the queue.
        """
        return self.spo2.get()

    def spo2_available(self):
        """
        Check whether the SpO2 queues holds a non-zero number of new values
        """
        return not self.spo2.empty()

    def cleanup(self):
        """
        Disconnect from the device and delete allocated resources.
        """
        self.transport.disconnect()
