import json
import os
from pathlib import Path

from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv

from config.settings import CEREBRAS_MODEL, CEREBRAS_TEMPERATURE, CEREBRAS_MAX_TOKENS


load_dotenv()

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent.parent / "config" / "system_prompt.txt"


class CerebrasClientError(Exception):
    pass


class CerebrasClient:
    def __init__(self, api_key=None):
        api_key = api_key or os.getenv("CEREBRAS_API_KEY")
        if not api_key:
            raise CerebrasClientError(
                "CEREBRAS_API_KEY not found. Set it in .env file or pass api_key parameter."
            )
        self.client = Cerebras(api_key=api_key)
        self.system_prompt = self._load_system_prompt()

    @staticmethod
    def _load_system_prompt():
        try:
            return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            raise CerebrasClientError(f"System prompt file not found: {SYSTEM_PROMPT_PATH}")

    def diagnose(self, image_base64, telemetry=None):
        telemetry_text = self._format_telemetry(telemetry)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Telemetry: extruder {telemetry.get('extruder_actual', '?')}C, bed {telemetry.get('bed_actual', '?')}C. Describe the print quality.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_base64},
                    },
                ],
            },
        ]

        kwargs = {
            "model": CEREBRAS_MODEL,
            "messages": messages,
            "temperature": CEREBRAS_TEMPERATURE,
            "max_tokens": CEREBRAS_MAX_TOKENS,
        }

        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            raise CerebrasClientError(f"API call failed: {e}")

        content = response.choices[0].message.content or ""
        text_lower = content.lower()

        result = {
            "defect_type": "nominal",
            "action_required": "none",
            "raw_response": content,
        }

        has_catastrophic = "catastrophic" in text_lower
        has_spaghetti = "spaghetti" in text_lower
        has_tangled = "tangled" in text_lower
        has_failure = "failure" in text_lower or "failed" in text_lower
        has_layer_shift = "layer shift" in text_lower or "layer_shift" in text_lower
        has_z_wobble = "z-wobble" in text_lower or "z wobble" in text_lower
        has_stair_step = "stair-step" in text_lower or "stair step" in text_lower
        has_under_extrusion = "under-extrusion" in text_lower or "under_extrusion" in text_lower or "under extrusion" in text_lower
        has_gaps = "gap" in text_lower
        has_over_extrusion = "over-extrusion" in text_lower or "over_extrusion" in text_lower
        has_blobbing = "blobbing" in text_lower or "blob" in text_lower

        has_critical_term = has_catastrophic or "severe" in text_lower or "total" in text_lower

        if has_spaghetti or has_tangled or (has_failure and not has_gaps and not has_under_extrusion):
            result["defect_type"] = "spaghetti"
            result["action_required"] = "emergency_stop"
        elif has_layer_shift or has_z_wobble or has_stair_step:
            result["defect_type"] = "layer_shift"
            result["action_required"] = "reduce_speed"
            result["speed_percentage"] = 70
        elif has_under_extrusion or has_gaps:
            result["defect_type"] = "under_extrusion"
            result["action_required"] = "adjust_temp"
            if telemetry and telemetry.get("extruder_actual"):
                result["target_temperature_celsius"] = min(telemetry["extruder_actual"] + 10, 250)
            else:
                result["target_temperature_celsius"] = 215

        return result

    @staticmethod
    def _format_telemetry(telemetry):
        if not telemetry:
            return "Not available"
        parts = []
        for key, value in telemetry.items():
            key_str = key.replace("_", " ").title()
            parts.append(f"{key_str}: {value}")
        return "\n".join(parts)
