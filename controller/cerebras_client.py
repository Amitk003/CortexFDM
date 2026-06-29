import json
import os
from pathlib import Path

from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv

from config.settings import (
    CEREBRAS_MODEL,
    CEREBRAS_TEMPERATURE,
    CEREBRAS_REASONING_EFFORT,
    CEREBRAS_MAX_TOKENS,
)


load_dotenv()


SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent.parent / "config" / "system_prompt.txt"
TOOL_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "config" / "tool_schema.json"


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
        self.tools = self._load_tools()

    @staticmethod
    def _load_system_prompt():
        try:
            return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            raise CerebrasClientError(f"System prompt file not found: {SYSTEM_PROMPT_PATH}")

    @staticmethod
    def _load_tools():
        try:
            schema = json.loads(TOOL_SCHEMA_PATH.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise CerebrasClientError(f"Tool schema file not found: {TOOL_SCHEMA_PATH}")
        except json.JSONDecodeError as e:
            raise CerebrasClientError(f"Invalid tool schema JSON: {e}")
        return [schema]

    def diagnose(self, image_base64, telemetry=None):
        telemetry_text = self._format_telemetry(telemetry)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Current printer telemetry:\n{telemetry_text}",
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
            "tools": self.tools,
            "max_tokens": CEREBRAS_MAX_TOKENS,
        }

        reasoning = CEREBRAS_REASONING_EFFORT
        if reasoning:
            kwargs["reasoning_effort"] = reasoning

        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            raise CerebrasClientError(f"API call failed: {e}")

        choice = response.choices[0]
        message = choice.message

        if not message.tool_calls:
            return {
                "defect_type": "nominal",
                "action_required": "none",
                "raw_response": message.content or "",
            }

        tool_call = message.tool_calls[0]
        try:
            arguments = json.loads(tool_call.function.arguments)
        except (json.JSONDecodeError, IndexError, AttributeError) as e:
            raise CerebrasClientError(f"Failed to parse tool call response: {e}")

        result = {
            "defect_type": arguments.get("defect_type", "nominal"),
            "action_required": arguments.get("action_required", "none"),
        }

        if "target_temperature_celsius" in arguments:
            result["target_temperature_celsius"] = arguments["target_temperature_celsius"]
        if "speed_percentage" in arguments:
            result["speed_percentage"] = arguments["speed_percentage"]

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
