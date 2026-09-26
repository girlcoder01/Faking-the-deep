"""
Sends the deepfake detection result to the Arduino over USB serial,
so it can be shown on the LCD.

Usage from detect.py or app.py:

    from arduino_serial import send_to_arduino
    send_to_arduino(result["label"], result["confidence"])

If the Arduino isn't connected, this fails quietly (prints a warning)
rather than crashing the whole app -- the video analysis should still
work even without the hardware plugged in.
"""

import time

try:
    import serial
except ImportError:
    serial = None


def find_arduino_port():
    """
    Best-effort guess at the Arduino's serial port.
    On Mac, it's usually something like /dev/cu.usbmodem14101 or
    /dev/cu.usbserial-XXXX. On Windows, it's usually COM3, COM4, etc.

    If this doesn't find it automatically, run this in the terminal
    to list available ports and set ARDUINO_PORT manually below:
        Mac:     ls /dev/cu.*
        Windows: check Device Manager, or the Arduino IDE's Tools > Port menu
    """
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "usbmodem" in p.device or "usbserial" in p.device or "COM" in p.device:
            return p.device
    return None


# If auto-detection doesn't work for your machine, hardcode it here, e.g.:
ARDUINO_PORT = "/dev/cu.usbmodem1301"
BAUD_RATE = 9600


def send_to_arduino(label: str, confidence: float, port: str = None):
    if serial is None:
        print("pyserial not installed -- skipping Arduino update. "
              "Run: pip install pyserial")
        return

    target_port = port or ARDUINO_PORT or find_arduino_port()
    if target_port is None:
        print("Could not find an Arduino connected over USB -- skipping display update.")
        return

    tag = "FAKE" if "FAKE" in label.upper() else "REAL"
    message = f"{tag}:{confidence}\n"

    try:
        with serial.Serial(target_port, BAUD_RATE, timeout=2) as ser:
            time.sleep(2)  # Arduino resets when serial connection opens; give it time to boot
            ser.write(message.encode("utf-8"))
            print(f"Sent to Arduino ({target_port}): {message.strip()}")
    except Exception as e:
        print(f"Could not send to Arduino: {e}")
