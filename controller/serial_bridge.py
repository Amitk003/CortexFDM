import socket
from config.settings import (
    MOCK_PRINTER_HOST,
    MOCK_PRINTER_PORT,
    SOCKET_TIMEOUT,
)


class SerialBridgeError(Exception):
    pass


class SerialBridge:
    def __init__(self):
        self.sock = None
        self.buffer = ""
        self._connected = False

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(SOCKET_TIMEOUT)
        try:
            self.sock.connect((MOCK_PRINTER_HOST, MOCK_PRINTER_PORT))
            self._connected = True
        except socket.error as e:
            self.sock = None
            raise SerialBridgeError(f"Failed to connect to mock printer: {e}")

    def disconnect(self):
        self._connected = False
        if self.sock:
            try:
                self.sock.close()
            except socket.error:
                pass
            self.sock = None

    @property
    def connected(self):
        return self._connected

    def send_gcode(self, command):
        if not self.sock:
            raise SerialBridgeError("Not connected to mock printer")
        try:
            self.sock.sendall((command + "\n").encode("utf-8"))
            response = self._read_response()
            return response
        except socket.error as e:
            self._connected = False
            raise SerialBridgeError(f"Communication error: {e}")

    def send_multiple(self, commands):
        responses = []
        for cmd in commands:
            resp = self.send_gcode(cmd)
            responses.append(resp)
        return responses

    def query_temperature(self):
        response = self.send_gcode("M105")
        result = {"extruder_target": None, "extruder_actual": None, "bed_target": None, "bed_actual": None}
        try:
            parts = response.replace(",", "").split()
            for p in parts:
                if p.startswith("T:"):
                    result["extruder_target"] = int(p[2:])
                elif p.startswith("/") and result["extruder_actual"] is None:
                    val = p[1:]
                    if val.replace("-", "").isdigit():
                        result["extruder_actual"] = int(val)
                elif p.startswith("B:"):
                    val = p[2:]
                    if val.replace("-", "").isdigit():
                        result["bed_target"] = int(val)
                elif p.startswith("/") and result["bed_actual"] is None:
                    val = p[1:]
                    if val.replace("-", "").isdigit():
                        result["bed_actual"] = int(val)
        except (ValueError, IndexError):
            pass
        return result

    def query_position(self):
        response = self.send_gcode("M114")
        result = {"x": None, "y": None, "z": None}
        try:
            parts = response.split()
            for p in parts:
                if p.startswith("X:"):
                    result["x"] = float(p[2:])
                elif p.startswith("Y:"):
                    result["y"] = float(p[2:])
                elif p.startswith("Z:"):
                    result["z"] = float(p[2:])
        except (ValueError, IndexError):
            pass
        return result

    def _read_response(self):
        while True:
            if "\n" in self.buffer:
                line, self.buffer = self.buffer.split("\n", 1)
                return line.strip()
            try:
                data = self.sock.recv(4096)
                if not data:
                    self._connected = False
                    raise SerialBridgeError("Mock printer disconnected")
                self.buffer += data.decode("utf-8")
            except socket.timeout:
                raise SerialBridgeError("Timeout waiting for response from mock printer")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
