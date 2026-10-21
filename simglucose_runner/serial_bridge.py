import serial

class SerialBridge:
    """ Send simulated glucose readings to the physical CGM over USB serial """

    def __init__(self, port="COM14", baudrate=115200, timeout=1):
        self.connection = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
        )

    def connect(self):
        """ Open the serial connection if it is not already open. """
        if not self.connection.is_open:
            self.connection.open()

    def send_glucose(self, glucose_mg_dL):
        """ Send one glucose value as a newline terminated string """
        message = f"{glucose_mg_dL:2f}\n"
        self.connection.write(message.encode("utf-8"))

    def close(self):
        """ Close the serial connection """
        if self.connection.is_open:
            self.connection.close()