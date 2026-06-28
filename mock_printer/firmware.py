import socket
import sys
import time
from config.settings import (
    MOCK_PRINTER_HOST,
    MOCK_PRINTER_PORT,
    SOCKET_TIMEOUT,
)


class PrinterState:
    def __init__(self):
        self.extruder_temp = 200
        self.bed_temp = 60
        self.target_extruder_temp = 200
        self.target_bed_temp = 60
        self.position_x = 0.0
        self.position_y = 0.0
        self.position_z = 0.0
        self.speed_factor = 100
        self.relative_mode = False
        self.line_number = 0
        self.printing = True

    def home(self, axes):
        if "X" in axes or not axes:
            self.position_x = 0.0
        if "Y" in axes or not axes:
            self.position_y = 0.0
        if "Z" in axes or not axes:
            self.position_z = 0.0

    def move(self, params):
        for axis, attr in [("X", "position_x"), ("Y", "position_y"), ("Z", "position_z")]:
            if axis in params:
                value = params[axis]
                if self.relative_mode:
                    setattr(self, attr, getattr(self, attr) + value)
                else:
                    setattr(self, attr, value)

    def report_temperature(self):
        return (
            f"ok T:{self.target_extruder_temp}"
            f" /{self.extruder_temp}"
            f" B:{self.target_bed_temp}"
            f" /{self.bed_temp}"
        )

    def report_position(self):
        return (
            f"ok X:{self.position_x:.1f}"
            f" Y:{self.position_y:.1f}"
            f" Z:{self.position_z:.1f}"
        )


class GCodeParser:
    @staticmethod
    def parse(line):
        line = line.strip()
        if not line:
            return None, {}
        parts = line.upper().replace(";", " ").split()
        if not parts:
            return None, {}
        cmd = parts[0]
        params = {}
        for p in parts[1:]:
            if len(p) > 1 and p[0].isalpha():
                try:
                    params[p[0]] = float(p[1:])
                except ValueError:
                    pass
        return cmd, params


class MockPrinter:
    def __init__(self):
        self.state = PrinterState()
        self.parser = GCodeParser()
        self.server = None
        self.conn = None
        self.running = False

    def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((MOCK_PRINTER_HOST, MOCK_PRINTER_PORT))
        self.server.listen(1)
        self._log(f"Listening on {MOCK_PRINTER_HOST}:{MOCK_PRINTER_PORT}")
        self._log("Waiting for controller to connect...")

        self.conn, addr = self.server.accept()
        self._log(f"Controller connected from {addr}")
        self.conn.settimeout(SOCKET_TIMEOUT)
        self.running = True

    def stop(self):
        self.running = False
        if self.conn:
            self.conn.close()
        if self.server:
            self.server.close()
        self._log("Server stopped")

    def run(self):
        buffer = ""
        try:
            self.start()
            while self.running:
                try:
                    data = self.conn.recv(4096)
                    if not data:
                        self._log("Controller disconnected")
                        break
                    buffer += data.decode("utf-8")

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                        self._handle_line(line)

                except socket.timeout:
                    continue
                except ConnectionResetError:
                    self._log("Connection reset by controller")
                    break
        except KeyboardInterrupt:
            self._log("Shutting down")
        finally:
            self.stop()

    def _handle_line(self, line):
        self._log(f"Received: {line}")
        cmd, params = self.parser.parse(line)

        if cmd is None:
            self._send("ok")
            return

        response = self._execute(cmd, params)
        if response:
            self._send(response)

    def _execute(self, cmd, params):
        s = self.state

        if cmd == "M104":
            if "S" in params:
                s.target_extruder_temp = int(params["S"])
            self._log(f"Set extruder temp to {s.target_extruder_temp}")

        elif cmd == "M140":
            if "S" in params:
                s.target_bed_temp = int(params["S"])
            self._log(f"Set bed temp to {s.target_bed_temp}")

        elif cmd == "M220":
            if "S" in params:
                s.speed_factor = int(params["S"])
            self._log(f"Set speed factor to {s.speed_factor}%")

        elif cmd == "M84":
            s.printing = False
            self._log("Motors disabled")

        elif cmd == "G91":
            s.relative_mode = True
            self._log("Set relative positioning mode")

        elif cmd == "G90":
            s.relative_mode = False
            self._log("Set absolute positioning mode")

        elif cmd == "G28":
            axes_to_home = set()
            for axis in ("X", "Y", "Z"):
                if axis in params:
                    axes_to_home.add(axis)
            if not axes_to_home:
                axes_to_home = {"X", "Y", "Z"}
            s.home(axes_to_home)
            self._log("Homing completed")

        elif cmd == "G1":
            s.move(params)
            pos = s.report_position()
            self._log(f"Move to {pos[3:]}")

        elif cmd == "M105":
            return s.report_temperature()

        elif cmd == "M114":
            return s.report_position()

        return "ok"

    def _send(self, message):
        self.conn.sendall((message + "\n").encode("utf-8"))

    @staticmethod
    def _log(message):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[MOCK PRINTER {timestamp}] {message}")
        sys.stdout.flush()


def main():
    printer = MockPrinter()
    printer.run()


if __name__ == "__main__":
    main()
