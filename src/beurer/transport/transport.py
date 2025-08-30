from enum import Enum

class TransportType(Enum):
    """
    Types of supported transport implementations
    """
    USB_HID = 1

class Transport:
    """
    Abstract transport base class
    """

    def __init__(self, type: TransportType):
        self.type = type

    def discover(self):
        pass

    def connect(self):
        pass
