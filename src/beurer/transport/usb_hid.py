"""
USB HID driver for Beurer PO 80
"""

import time
import binascii
import threading
import queue
from datetime import datetime
import logging
import hid
from beurer.transport.transport import Transport, TransportType

logger = logging.getLogger(__name__)

class HID(Transport):
    """
    USB HID transport implementation
    """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=super-init-not-called
    def __init__(self):
        # Child threads
        self.t = []

        # USB HID
        self.transport_type = TransportType.USB_HID
        self.supported_vids = []
        self.supported_pids = []
        self.hid = None

        # Device properties
        self.manufacturer = None
        self.product = None
        self.serial_number = None
        self.user = None
        self.model = None

        # Internal send/receive queues
        self.rx_queue = None
        self.tx_queue = None

        # Queues to access data from outside
        self.bpm_data = None
        self.spo2_data= None

        # Running flag (for Ctrl+C interruption)
        self.running = True

    def set_vids(self, vids):
        """
        Set supported USB Vendor IDs
        """
        self.supported_vids = [int(vid, 16) if isinstance(vid, str) else int(vid) for vid in vids]

    def set_pids(self, pids):
        """
        Set supported USB Product IDs
        """
        self.supported_pids = [int(pid, 16) if isinstance(pid, str) else int(pid) for pid in pids]

    def get_type(self) -> TransportType:
        """
        Return the type of transport (Enum beurer.transport.transport.TransportType)
        """
        return self.transport_type

    def discover(self):
        """
        Discover all Beurer devices connected over USB HID
        """
        devices = []
        hid_devices = hid.enumerate()
        for hid_device in hid_devices:
            if hid_device['vendor_id'] in self.supported_vids:
                if hid_device['product_id'] in self.supported_pids:
                    devices.append(hid_device)
        return devices

    def connect(self, path):
        """
        Connect to a device given its HID path
        """
        self.hid = hid.device()
        self.hid.open_path(path)

        self.manufacturer = self.hid.get_manufacturer_string()
        self.product = self.hid.get_product_string()
        self.serial_number = self.hid.get_serial_number_string()
        logger.info('Connected to \'%s\' by \'%s\'', self.product, self.manufacturer)

        self.rx_queue = queue.Queue()
        self.tx_queue = queue.Queue()

        thread = threading.Thread(target=self.receive_packet)
        self.running = True
        self.t.append(thread)
        thread.start()

        thread = threading.Thread(target=self.transmit_packet)
        self.running = True
        self.t.append(thread)
        thread.start()

        time.sleep(0.5)

        self.get_model()
        self.get_user()
        self.set_time(datetime(2025, 8, 30, 16, 24, 25))
        self.configure()

    def set_bpm_queue(self, bpm_queue):
        """
        Provide a queue as a data sink to store bpm data
        """
        self.bpm_data = bpm_queue

    def set_spo2_queue(self, spo2_queue):
        """
        Provide a queue as a data sink to store spo2 data
        """
        self.spo2_data = spo2_queue

    def configure(self):
        """
        Configure the device to send the data
        Some parts of the protocol are unknown
        """
        data = [0x80] + [0x00] * 63
        self.tx_queue.put(data)

        data = [0x9b] + [0x01] + [0x1c] + [0x00] * 61
        self.tx_queue.put(data)

        data = [0x9b] + [0x00] + [0x1b] + [0x00] * 61
        self.tx_queue.put(data)

    def get_model(self):
        """
        Get the model string from the device, e.g., 'PO80'
        """
        data = [0x81] + [0x01] + [0x00] * 62
        self.tx_queue.put(data)

    def get_user(self):
        """
        Get the username stored on the device (default=user)
        """
        data = [0x8e] + [0x03] + [0x11] + [0x00] * 61
        self.tx_queue.put(data)

    def set_time(self, dt):
        """
        Set the time of the device's RTC
        TODO: This does not seem to be working
        """
        data = [0x83]
        data += [dt.year - 2000] + [dt.month] + [dt.day] + [dt.hour]
        data += [dt.minute] + [dt.second] + [dt.weekday()] + [0x4]
        data += (64 - len(data)) * [0x00]
        self.tx_queue.put(data)

    def disconnect(self):
        """
        Close the USB HID connection to this device.
        """
        self.hid.close()
        self.running = False
        for thread in self.t:
            thread.join()

    def handle_packet(self, data):
        """
        Parse an incoming packet and handle it accordingly.
        """
        if data[:2] == b'f1':
            self.model = bytes.fromhex(data[2:10].decode()).decode()
            logger.info('Pulse oximeter model: %s', self.model)
        if data[:4] == b'fe03':
            self.user = bytes.fromhex(data[4:18].decode()).decode()
            logger.info('Username: %s', self.user)
        if data[:4] == b'eb01':
            bpm = int(data[6:8],16)
            spo2 = int(data[8:10],16)
            if bpm < 127:
                self.bpm_data.put(bpm)
            if spo2 < 127:
                self.spo2_data.put(spo2)

    def receive_packet(self):
        """
        Endless function of the receiving thread
        """
        num = 0
        while self.running:
            data = self.hid.read(64, timeout_ms=1000)
            if data:
                data = binascii.hexlify(bytearray(data))
                logger.debug('Device->PC: %s', data.decode())

                self.handle_packet(data)
                num = num + 1
            if num > 10:
                num = 0
                data = [0x9a] + [0x1a] + [0x00] * 62
                self.tx_queue.put(data)

    def transmit_packet(self):
        """
        Endless function of the transmitting thread
        """
        while self.running:
            try:
                data = self.tx_queue.get(timeout=1)
            except queue.Empty:
                pass
            if data:
                logger.debug('PC->Device: %s', binascii.hexlify(bytearray(data)).decode())
                self.hid.write(data)
