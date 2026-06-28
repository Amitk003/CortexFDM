from config.settings import (
    MAX_TEMPERATURE_CELSIUS,
    MIN_TEMPERATURE_CELSIUS,
    MIN_SPEED_PERCENTAGE,
    MAX_SPEED_PERCENTAGE,
)


class SafetyError(Exception):
    pass


def clamp_temperature(temp_celsius):
    if temp_celsius is None:
        return None
    temp = int(temp_celsius)
    if temp < MIN_TEMPERATURE_CELSIUS:
        raise SafetyError(
            f"Temperature {temp}C is below minimum {MIN_TEMPERATURE_CELSIUS}C"
        )
    if temp > MAX_TEMPERATURE_CELSIUS:
        raise SafetyError(
            f"Temperature {temp}C exceeds maximum {MAX_TEMPERATURE_CELSIUS}C"
        )
    return temp


def clamp_speed(speed_percent):
    if speed_percent is None:
        return None
    speed = int(speed_percent)
    if speed < MIN_SPEED_PERCENTAGE:
        raise SafetyError(
            f"Speed {speed}% is below minimum {MIN_SPEED_PERCENTAGE}%"
        )
    if speed > MAX_SPEED_PERCENTAGE:
        raise SafetyError(
            f"Speed {speed}% exceeds maximum {MAX_SPEED_PERCENTAGE}%"
        )
    return speed
