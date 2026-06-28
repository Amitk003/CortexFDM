import sys
import time
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from rich.live import Live

from controller.camera import MockCamera, MockCameraError
from controller.serial_bridge import SerialBridge, SerialBridgeError
from controller.cerebras_client import CerebrasClient, CerebrasClientError
from controller.gcode_translator import translate, TranslationError
from controller.ui import Dashboard
from config.settings import SAMPLING_INTERVAL_SECONDS


def run():
    camera = None
    bridge = None
    dashboard = Dashboard()

    try:
        camera = MockCamera()
        dashboard.camera_total = camera.total_images
        dashboard.add_log(f"Loaded {camera.total_images} images from camera folder")
    except MockCameraError as e:
        print(f"Camera error: {e}")

    try:
        camera = MockCamera()
        print(f"[CONTROLLER] Loaded {camera.total_images} images from camera folder")
    except MockCameraError as e:
        print(f"[CONTROLLER ERROR] Camera: {e}")
        return

    try:
        cerebras = CerebrasClient()
        dashboard.add_log("Cerebras client initialized (model: gemma-4-31b)")
    except CerebrasClientError as e:
        print(f"Cerebras error: {e}")
        print(f"[CONTROLLER] Cerebras client initialized (model: gemma-4-31b)")
    except CerebrasClientError as e:
        print(f"[CONTROLLER ERROR] Cerebras: {e}")
        return

    try:
        bridge = SerialBridge()
        bridge.connect()
        dashboard.add_log("Connected to mock printer")
        dashboard.current_telemetry = bridge.query_temperature()
        pos = bridge.query_position()
        dashboard.current_telemetry["position_x"] = pos.get("x")
        dashboard.current_telemetry["position_y"] = pos.get("y")
        dashboard.current_telemetry["position_z"] = pos.get("z")
    except SerialBridgeError as e:
        print(f"Printer error: {e}")
        return

    dashboard.add_log("Closed-loop started. Press Ctrl+C to stop.")

    try:
        with Live(dashboard.render(), refresh_per_second=4, screen=False) as live:
            while True:
                loop_start = time.time()
                dashboard.loop_count += 1

                # Step 1: Capture image
                try:
                    image_b64 = camera.get_next_frame()
                    dashboard.current_image = camera.current_filename
                    dashboard.add_log(f"Camera: {camera.current_filename}")
                except MockCameraError as e:
                    dashboard.add_log(f"Camera error: {e}")
                    live.update(dashboard.render())
                    time.sleep(SAMPLING_INTERVAL_SECONDS)
                    continue

                # Step 2: Query telemetry
                try:
                    telemetry = bridge.query_temperature()
                    position = bridge.query_position()
                    telemetry["position_x"] = position.get("x")
                    telemetry["position_y"] = position.get("y")
                    telemetry["position_z"] = position.get("z")
                    dashboard.current_telemetry = telemetry
                except SerialBridgeError as e:
                    dashboard.add_log(f"Telemetry error: {e}")
                    live.update(dashboard.render())
                    time.sleep(SAMPLING_INTERVAL_SECONDS)
                    continue

                # Step 3: AI diagnosis
                try:
                    diagnosis = cerebras.diagnose(image_b64, telemetry)
                    dashboard.current_diagnosis = diagnosis
                    defect = diagnosis.get("defect_type", "unknown")
                    action = diagnosis.get("action_required", "unknown")
                    dashboard.add_log(f"Diagnosis: {defect} -> {action}")
                except CerebrasClientError as e:
                    dashboard.add_log(f"AI error: {e}")
                    live.update(dashboard.render())
                    time.sleep(SAMPLING_INTERVAL_SECONDS)
                    continue

                # Step 4: Translate to G-code
                try:
                    gcode_commands = translate(diagnosis)
                    dashboard.last_gcode = gcode_commands
                    if gcode_commands:
                        dashboard.add_log(f"G-code: {' | '.join(gcode_commands)}")
                    else:
                        dashboard.add_log("No action needed")
                except TranslationError as e:
                    dashboard.add_log(f"Translation error: {e}")
                    live.update(dashboard.render())
                    time.sleep(SAMPLING_INTERVAL_SECONDS)
                    continue

                # Step 5: Send to printer
                if gcode_commands:
                    try:
                        responses = bridge.send_multiple(gcode_commands)
                        dashboard.add_log(f"Printer: {len(responses)} commands acknowledged")
                    except SerialBridgeError as e:
                        dashboard.add_log(f"Send error: {e}")
                        live.update(dashboard.render())
                        break

                dashboard.loop_time = time.time() - loop_start
                live.update(dashboard.render())
                time.sleep(SAMPLING_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        dashboard.add_log("Shutdown requested")
    finally:
        if bridge:
            bridge.disconnect()
            dashboard.add_log("Disconnected from mock printer")
        print()
        print("CortexFDM stopped.")
        print(f"[CONTROLLER] Connected to mock printer")
        temp = bridge.query_temperature()
        print(f"[CONTROLLER] Initial printer state - Temp: {temp}")
    except SerialBridgeError as e:
        print(f"[CONTROLLER ERROR] Printer: {e}")
        return

    print()
    print("[CONTROLLER] Closed-loop started. Press Ctrl+C to stop.")
    print()

    try:
        loop_count = 0
        while True:
            loop_count += 1
            timestamp = time.strftime("%H:%M:%S")
            print(f"[CONTROLLER] === Loop {loop_count} at {timestamp} ===")

            # Step 1: Capture image
            try:
                image_b64 = camera.get_next_frame()
                current_image = camera.current_filename
                print(f"[CONTROLLER] Camera: {current_image} ({loop_count % camera.total_images + 1}/{camera.total_images})")
            except MockCameraError as e:
                print(f"[CONTROLLER ERROR] Camera read failed: {e}")
                time.sleep(SAMPLING_INTERVAL_SECONDS)
                continue

            # Step 2: Query telemetry
            try:
                telemetry = bridge.query_temperature()
                position = bridge.query_position()
                telemetry["position_x"] = position.get("x")
                telemetry["position_y"] = position.get("y")
                telemetry["position_z"] = position.get("z")
                print(f"[CONTROLLER] Telemetry: {telemetry}")
            except SerialBridgeError as e:
                print(f"[CONTROLLER ERROR] Telemetry failed: {e}")
                time.sleep(SAMPLING_INTERVAL_SECONDS)
                continue

            # Step 3: AI diagnosis
            try:
                diagnosis = cerebras.diagnose(image_b64, telemetry)
                defect = diagnosis.get("defect_type", "unknown")
                action = diagnosis.get("action_required", "unknown")
                print(f"[CONTROLLER] Diagnosis: {defect} -> {action}")
            except CerebrasClientError as e:
                print(f"[CONTROLLER ERROR] AI diagnosis failed: {e}")
                time.sleep(SAMPLING_INTERVAL_SECONDS)
                continue

            # Step 4: Translate to G-code
            try:
                gcode_commands = translate(diagnosis)
                if not gcode_commands:
                    print(f"[CONTROLLER] No action needed")
                else:
                    print(f"[CONTROLLER] G-code: {' | '.join(gcode_commands)}")
            except TranslationError as e:
                print(f"[CONTROLLER ERROR] Translation failed: {e}")
                time.sleep(SAMPLING_INTERVAL_SECONDS)
                continue

            # Step 5: Send to printer
            if gcode_commands:
                try:
                    responses = bridge.send_multiple(gcode_commands)
                    print(f"[CONTROLLER] Printer acknowledged all {len(responses)} commands")
                except SerialBridgeError as e:
                    print(f"[CONTROLLER ERROR] Send failed: {e}")
                    break

            print(f"[CONTROLLER] Waiting {SAMPLING_INTERVAL_SECONDS}s...")
            print()
            time.sleep(SAMPLING_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print()
        print("[CONTROLLER] Shutdown requested")
    finally:
        if bridge:
            bridge.disconnect()
            print("[CONTROLLER] Disconnected from mock printer")
        print("[CONTROLLER] Stopped")


if __name__ == "__main__":
    run()
