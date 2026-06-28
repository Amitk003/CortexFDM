import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from controller.camera import MockCamera, MockCameraError
from controller.serial_bridge import SerialBridge, SerialBridgeError
from controller.cerebras_client import CerebrasClient, CerebrasClientError
from controller.gcode_translator import translate, TranslationError
from config.settings import SAMPLING_INTERVAL_SECONDS


def run():
    camera = None
    bridge = None

    try:
        camera = MockCamera()
        print(f"[CONTROLLER] Loaded {camera.total_images} images from camera folder")
    except MockCameraError as e:
        print(f"[CONTROLLER ERROR] Camera: {e}")
        return

    try:
        cerebras = CerebrasClient()
        print(f"[CONTROLLER] Cerebras client initialized (model: gemma-4-31b)")
    except CerebrasClientError as e:
        print(f"[CONTROLLER ERROR] Cerebras: {e}")
        return

    try:
        bridge = SerialBridge()
        bridge.connect()
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
