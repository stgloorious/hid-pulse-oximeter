"""
Transport abstraction
"""

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

    def __init__(self, transport_type: TransportType):
        self.transport_type = transport_type

    def discover(self):
        """
        Search for attached devices and return a list
        """

    def connect(self, path):
        """
        Connect to a particular device
        """
