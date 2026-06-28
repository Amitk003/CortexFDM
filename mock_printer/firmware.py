import socket
import sys
import time
from config.settings import MOCK_PRINTER_HOST, MOCK_PRINTER_PORT, SOCKET_TIMEOUT


MOCK_PRINTER_STATE = {
    "extruder_temp": 200,
    "bed_temp": 60,
    "target_extruder_temp": 200,
    "target_bed_temp": 60,
    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
    "speed_factor": 100,
    "relative_mode": False,
    "line_number": 0,
    "printing": True,
}


def parse_gcode(line):
    line = line.strip()
    if not line:
        return None
    parts = line.upper().replace(";", " ").split()
    if not parts:
        return None
    cmd = parts[0]
    params = {}
    for p in parts[1:]:
        if len(p) > 1 and p[0].isalpha():
            try:
                params[p[0]] = float(p[1:])
            except ValueError:
                pass
    return cmd, params


def handle_command(cmd, params):
    state = MOCK_PRINTER_STATE

    if cmd == "M104":
        if "S" in params:
            state["target_extruder_temp"] = int(params["S"])
        log(f"Set extruder temp to {state['target_extruder_temp']}")

    elif cmd == "M140":
        if "S" in params:
            state["target_bed_temp"] = int(params["S"])
        log(f"Set bed temp to {state['target_bed_temp']}")

    elif cmd == "M220":
        if "S" in params:
            state["speed_factor"] = int(params["S"])
        log(f"Set speed factor to {state['speed_factor']}%")

    elif cmd == "M84":
        state["printing"] = False
        log("Motors disabled")

    elif cmd == "G91":
        state["relative_mode"] = True
        log("Set relative positioning mode")

    elif cmd == "G90":
        state["relative_mode"] = False
        log("Set absolute positioning mode")

    elif cmd == "G28":
        if "X" in params or not params:
            state["position"]["x"] = 0.0
        if "Y" in params or not params:
            state["position"]["y"] = 0.0
        if "Z" in params or not params:
            state["position"]["z"] = 0.0
        log("Homing completed")

    elif cmd == "G1":
        for axis in ("X", "Y", "Z"):
            if axis in params:
                if state["relative_mode"]:
                    state["position"][axis.lower()] += params[axis]
                else:
                    state["position"][axis.lower()] = params[axis]
        log(f"Move to X{state['position']['x']:.1f} Y{state['position']['y']:.1f} Z{state['position']['z']:.1f}")

    elif cmd == "M105":
        return f"ok T:{state['target_extruder_temp']} /{state['extruder_temp']} B:{state['target_bed_temp']} /{state['bed_temp']}"

    elif cmd == "M114":
        return f"ok X:{state['position']['x']:.1f} Y:{state['position']['y']:.1f} Z:{state['position']['z']:.1f}"

    return "ok"


def log(message):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[MOCK PRINTER {timestamp}] {message}")
    sys.stdout.flush()


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((MOCK_PRINTER_HOST, MOCK_PRINTER_PORT))
    server.listen(1)
    log(f"Listening on {MOCK_PRINTER_HOST}:{MOCK_PRINTER_PORT}")
    log("Waiting for controller to connect...")

    conn, addr = server.accept()
    log(f"Controller connected from {addr}")
    conn.settimeout(SOCKET_TIMEOUT)

    buffer = ""
    try:
        while True:
            try:
                data = conn.recv(4096)
                if not data:
                    log("Controller disconnected")
                    break
                buffer += data.decode("utf-8")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    log(f"Received: {line}")
                    parsed = parse_gcode(line)
                    if parsed is None:
                        response = "ok"
                    else:
                        cmd, params = parsed
                        response = handle_command(cmd, params)

                    if response:
                        conn.sendall((response + "\n").encode("utf-8"))

            except socket.timeout:
                continue
            except ConnectionResetError:
                log("Connection reset by controller")
                break
    except KeyboardInterrupt:
        log("Shutting down")
    finally:
        conn.close()
        server.close()
        log("Server stopped")


if __name__ == "__main__":
    main()
