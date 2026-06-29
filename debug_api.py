import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras

from controller.camera import MockCamera
from config.settings import CEREBRAS_MODEL, CEREBRAS_TEMPERATURE

load_dotenv()


def main():
    api_key = os.getenv("CEREBRAS_API_KEY")
    if not api_key:
        print("CEREBRAS_API_KEY not found in .env")
        return

    client = Cerebras(api_key=api_key)
    cam = MockCamera()

    log_path = Path(__file__).resolve().parent / "debug_api.log"
    with open(log_path, "w", encoding="utf-8") as log:
        log.write("=" * 60 + "\n")
        log.write("CORTEXFDM API DEBUG LOG\n")
        log.write("=" * 60 + "\n\n")

        for i in range(len(cam.image_list)):
            name = cam.current_filename
            image_b64 = cam.get_next_frame()
            telemetry = {
                "extruder_target": 200,
                "extruder_actual": 200,
                "bed_target": 60,
                "bed_actual": 60,
                "position_x": 0,
                "position_y": 0,
                "position_z": 5,
            }

            messages = [
                {
                    "role": "system",
                    "content": "You are a 3D printing expert. Describe what you see in this 3D print image in detail. Is the print quality good or are there defects? What specific defects do you see?",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Describe this 3D print in detail. Current temperature: {telemetry['extruder_actual']}C.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_b64},
                        },
                    ],
                },
            ]

            log.write(f"--- Image: {name} ---\n")
            log.write(f"Telemetry: {json.dumps(telemetry, indent=2)}\n")
            log.write(f"Image data URI length: {len(image_b64)} chars\n")
            log.write(f"Sending request to Cerebras...\n")

            try:
                response = client.chat.completions.create(
                    model=CEREBRAS_MODEL,
                    messages=messages,
                    temperature=CEREBRAS_TEMPERATURE,
                    max_tokens=500,
                )
                content = response.choices[0].message.content or ""
                log.write(f"MODEL RESPONSE:\n{content}\n\n")
                print(f"[{name}] Response saved to log")
            except Exception as e:
                log.write(f"API ERROR: {e}\n\n")
                print(f"[{name}] ERROR: {e}")

        log.write("=" * 60 + "\n")
        log.write("END OF LOG\n")

    print(f"\nFull debug log saved to: {log_path}")


if __name__ == "__main__":
    main()
