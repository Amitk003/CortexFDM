import json
import os
from pathlib import Path

from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv

from config.settings import (
    CEREBRAS_MODEL,
    CEREBRAS_TEMPERATURE,
    CEREBRAS_MAX_TOKENS,
)


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
                        "text": f"Current telemetry:\n{telemetry_text}\n\nWhat defect do you see in this 3D print?",
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

        choice = response.choices[0]
        content = choice.message.content or ""

        print(f"\n[MODEL RAW RESPONSE]\n{content}\n")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            try:
                start = content.index("{")
                end = content.rindex("}") + 1
                parsed = json.loads(content[start:end])
            except (ValueError, json.JSONDecodeError):
                raise CerebrasClientError(f"Failed to parse response as JSON: {content[:300]}")

        result = {
            "defect_type": parsed.get("defect_type", "nominal"),
            "action_required": parsed.get("action_required", "none"),
            "raw_response": content,
        }

        if "target_temperature_celsius" in parsed:
            result["target_temperature_celsius"] = parsed["target_temperature_celsius"]
        if "speed_percentage" in parsed:
            result["speed_percentage"] = parsed["speed_percentage"]

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
