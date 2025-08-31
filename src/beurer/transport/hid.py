from enum import Enum
import time
import hid
import struct
import binascii
import threading
import queue
from datetime import datetime

from beurer.transport.transport import Transport, TransportType

import logging
logger = logging.getLogger(__name__)

class HID(Transport):
    """
    USB HID transport implementation
    """

    def __init__(self):
        self.transport_type = TransportType.USB_HID
        self.t = []

    def setVID(self, vids):
        """
        Set supported USB Vendor IDs
        """
        self.supportedVID = [int(vid, 16) if isinstance(vid, str) else int(vid) for vid in vids]

    def setPID(self, pids):
        """
        Set supported USB Product IDs
        """
        self.supportedPID = [int(pid, 16) if isinstance(pid, str) else int(pid) for pid in pids]

    def getType(self) -> TransportType:
        return self.transport_type

    def discover(self):
        devices = []
        hid_devices = hid.enumerate()
        for hid_device in hid_devices:
            if hid_device['vendor_id'] in self.supportedVID:
                if hid_device['product_id'] in self.supportedPID:
                    devices.append(hid_device)
        return devices

    def connect(self, hid_path):
        self.hid = hid.device()
        self.hid.open_path(hid_path)

        self.manufacturer = self.hid.get_manufacturer_string()
        self.product = self.hid.get_product_string()
        self.serial_number = self.hid.get_serial_number_string()
        logger.info(f'Connected to \'{self.product}\' by \'{self.manufacturer}\'')

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

        self.getModel()
        self.getUser()
        self.setTime(datetime(2025, 8, 30, 16, 24, 25))
        self.configure()

    def setBpmQueue(self, bpm_queue):
        self.bpm_data = bpm_queue

    def setSpo2Queue(self, spo2_queue):
        self.spo2_data = spo2_queue

    def configure(self):
        data = [0x80] + [0x00] * 63
        self.tx_queue.put(data)

        data = [0x9b] + [0x01] + [0x1c] + [0x00] * 61
        self.tx_queue.put(data)

        data = [0x9b] + [0x00] + [0x1b] + [0x00] * 61
        self.tx_queue.put(data)

    def getModel(self):
        data = [0x81] + [0x01] + [0x00] * 62
        self.tx_queue.put(data)

    def getUser(self):
        data = [0x8e] + [0x03] + [0x11] + [0x00] * 61
        self.tx_queue.put(data)

    def setTime(self, dt):
        data = [0x83]
        data += [dt.year - 2000] + [dt.month] + [dt.day] + [dt.hour] + [dt.minute] + [dt.second] + [dt.weekday()] + [0x4]
        data += (64 - len(data)) * [0x00]
        self.tx_queue.put(data)

    def disconnect(self):
        self.hid.close()
        self.running = False
        for thread in self.t:
            thread.join()

    def handle_packet(self, data):
        if data[:2] == b'f1':
            self.model = bytes.fromhex(data[2:10].decode()).decode()
            logger.info(f"Pulse oximeter model: {self.model}")
        if data[:4] == b'fe03':
            self.user = bytes.fromhex(data[4:18].decode()).decode()
            logger.info(f"Username: {self.user}")
        if data[:4] == b'eb01':
            bpm = int(data[6:8],16)
            spo2 = int(data[8:10],16)
            if bpm < 127:
                self.bpm_data.put(bpm)
            if spo2 < 127:
                self.spo2_data.put(spo2)

            return
        if data[:4] == b'eb00':
            values = [data[i+4:i+12] for i in range(0, 36, 12)]
            #print(f"{values[0].decode()},{values[1].decode()},{values[2].decode()}")


    def receive_packet(self):
        num = 0
        while self.running:
            data = self.hid.read(64, timeout_ms=1000)
            if data:
                data = binascii.hexlify(bytearray(data))
                logger.debug(f"Device->PC: {data.decode()}")

                self.handle_packet(data)
            
                num = num + 1
            if num > 10:
                num = 0
                data = [0x9a] + [0x1a] + [0x00] * 62
                self.tx_queue.put(data)
    
    def transmit_packet(self):
        while self.running:
            try:
                data = self.tx_queue.get(timeout=1)
            except queue.Empty:
                pass
            if data:
                logger.debug(f"PC->Device: {binascii.hexlify(bytearray(data)).decode()}")
                self.hid.write(data)
