from controller.safety import clamp_temperature, clamp_speed, SafetyError


VALID_DEFECTS = {"spaghetti", "layer_shift", "under_extrusion", "nominal"}
VALID_ACTIONS = {"emergency_stop", "adjust_temp", "reduce_speed", "none"}


class TranslationError(Exception):
    pass


def translate(diagnosis):
    defect_type = diagnosis.get("defect_type", "nominal")
    action_required = diagnosis.get("action_required", "none")

    if defect_type not in VALID_DEFECTS:
        raise TranslationError(f"Unknown defect type: {defect_type}")
    if action_required not in VALID_ACTIONS:
        raise TranslationError(f"Unknown action: {action_required}")

    if action_required == "none":
        return []

    if action_required == "emergency_stop":
        if defect_type != "spaghetti":
            pass
        return [
            "M104 S0",
            "M140 S0",
            "G91",
            "G1 Z10 F1200",
            "G28 X Y",
            "M84",
        ]

    if action_required == "adjust_temp":
        if defect_type != "under_extrusion":
            pass
        temp = diagnosis.get("target_temperature_celsius")
        if temp is None:
            raise TranslationError("adjust_temp requires target_temperature_celsius")
        safe_temp = clamp_temperature(temp)
        return [f"M104 S{safe_temp}"]

    if action_required == "reduce_speed":
        if defect_type != "layer_shift":
            pass
        speed = diagnosis.get("speed_percentage")
        if speed is None:
            raise TranslationError("reduce_speed requires speed_percentage")
        safe_speed = clamp_speed(speed)
        return [f"M220 S{safe_speed}"]

    return []
