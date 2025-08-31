# USB HID Reader for Beurer PO 80 Pulse Oximeter
This is a simple program that connects to the Beurer PO 80 Pulse Oximeter over
USB HID and reads out pulse and oxygen saturation.

## Installation
You need a working Python 3 installation.
First, create a virtual environment:

```
git clone https://github.com/stgloorious/hid-pulse-oximeter.git
cd hid-pulse-oximeter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage
After connecting the device and turning it on, you can run the application:
```
cd src
./hid-pulse-oximeter.py
```

### Example Output
```
INFO:__main__:Discovering devices...
INFO:beurer.po:Found HID device 'Pulse Oximeter' (0x28e9,0x28a,1-4:1.0)
INFO:__main__:Connecting to first device
INFO:beurer.transport.hid:Connected to 'Pulse Oximeter' by '        '
INFO:beurer.transport.hid:Username:    user
INFO:__main__: BPM:94 SpO2:96
INFO:__main__: BPM:94 SpO2:96
INFO:__main__: BPM:94 SpO2:96
INFO:__main__: BPM:94 SpO2:95
INFO:__main__: BPM:95 SpO2:95
INFO:__main__: BPM:94 SpO2:95
INFO:__main__: BPM:94 SpO2:95
INFO:__main__: BPM:93 SpO2:95
INFO:__main__: BPM:92 SpO2:95
```

## Disclaimer
This software is an independent project and is not affiliated with, authorized,
sponsored, or endorsed by Beurer GmbH.
All trademarks and brand names are the property of their respective owners.
