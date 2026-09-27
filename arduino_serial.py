"""
Sends the deepfake detection result to the Arduino over USB serial,
so it can be shown on the LCD.
"""

import time

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None


def find_arduino_port():
    """Finds any connected Arduino serial device on Mac/Windows/Linux."""
    if serial is None:
        return None
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if any(keyword in p.device.lower() for keyword in ["usbmodem", "usbserial", "com", "ttyusb", "ttyacm"]):
            return p.device
    return None


ARDUINO_PORT = None
BAUD_RATE = 9600


def send_to_arduino(label: str, confidence: float, port: str = None):
    if serial is None:
        print("pyserial not installed -- skipping Arduino update. Run: pip install pyserial")
        return

    target_port = port or find_arduino_port() or ARDUINO_PORT
    if target_port is None:
        print("Could not find an Arduino connected over USB -- skipping display update.")
        return

    tag = "FAKE" if "FAKE" in label.upper() else "REAL"
    message = f"{tag}:{confidence}\n"

    try:
        with serial.Serial(target_port, BAUD_RATE, timeout=2) as ser:
            time.sleep(2)  
            ser.write(message.encode("utf-8"))
            print(f"Sent to Arduino ({target_port}): {message.strip()}")
    except Exception as e:
        print(f"Could not send to Arduino on {target_port}: {e}")
