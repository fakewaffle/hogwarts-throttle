"""LionChief BLE command encoding.

Every command is written to one characteristic as: 0x00, payload..., checksum,
where checksum makes the payload bytes sum to 0 mod 256.
"""

CHARACTERISTIC = "08590f7e-db05-467e-8757-72f6faeb13d4"
MAX_SPEED = 31
MAX_VOLUME = 7


def frame(*payload: int) -> bytes:
    checksum = -sum(payload) % 256
    return bytes([0x00, *payload, checksum])


def speed(value: int) -> bytes:
    _check_range("speed", value, MAX_SPEED)
    return frame(0x45, value)


def direction(forward: bool) -> bytes:
    return frame(0x46, 0x01 if forward else 0x02)


def horn(on: bool) -> bytes:
    return frame(0x48, int(on))


def bell(on: bool) -> bytes:
    return frame(0x47, int(on))


def lights(on: bool) -> bytes:
    return frame(0x51, int(on))


def dialog() -> bytes:
    return frame(0x4D, 0x00, 0x01)


def smoke(on: bool) -> bytes:
    return frame(0x50, int(on))


def master_volume(value: int) -> bytes:
    _check_range("volume", value, MAX_VOLUME)
    return frame(0x4C, value)


def _check_range(name: str, value: int, maximum: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= maximum:
        raise ValueError(f"{name} must be an integer 0-{maximum}, got {value!r}")
