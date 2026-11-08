import asyncio
import logging
from dataclasses import asdict, dataclass

from . import protocol

log = logging.getLogger(__name__)

RECONNECT_DELAY = 3.0


@dataclass
class State:
    connected: bool = False
    speed: int = 0
    forward: bool = True
    horn: bool = False
    bell: bool = False
    lights: bool = True
    smoke: bool = False
    volume: int = 5


class Train:
    """Owns the engine's state and pushes changes over a link.

    A link needs `async connect()`, `async write(bytes)`, `async wait_closed()`
    and `async close()`.
    """

    def __init__(self, link):
        self.state = State()
        self._link = link
        self._lock = asyncio.Lock()

    def snapshot(self) -> dict:
        return asdict(self.state)

    async def run(self) -> None:
        while True:
            try:
                await self._link.connect()
                await self._on_connected()
                await self._link.wait_closed()
                log.info("engine disconnected")
            except Exception as error:
                log.warning("engine link failed: %r", error)
            self.state.connected = False
            await self._link.close()
            await asyncio.sleep(RECONNECT_DELAY)

    async def apply(self, action: str, value=None) -> dict:
        handler = ACTIONS.get(action)
        if handler is None:
            raise ValueError(f"unknown action {action!r}")
        log.info("command %s=%r connected=%s", action, value, self.state.connected)
        async with self._lock:
            for packet in handler(self.state, value):
                await self._write(packet)
        return self.snapshot()

    async def _on_connected(self) -> None:
        log.info("engine connected")
        self.state.connected = True
        self.state.speed = 0
        self.state.horn = False
        self.state.bell = False
        self.state.smoke = False
        async with self._lock:
            for packet in (
                protocol.speed(0),
                protocol.direction(self.state.forward),
                protocol.lights(self.state.lights),
                protocol.smoke(False),
                protocol.master_volume(self.state.volume),
            ):
                await self._write(packet)

    async def _write(self, packet: bytes) -> None:
        if not self.state.connected:
            return
        try:
            log.debug("write %s", packet.hex(" "))
            await self._link.write(packet)
        except Exception as error:
            log.warning("write failed: %s", error)
            self.state.connected = False
            await self._link.close()


def _speed(state: State, value):
    packet = protocol.speed(value)
    state.speed = value
    return [packet]


def _stop(state: State, _value):
    state.speed = 0
    return [protocol.speed(0)]


def _direction(state: State, value):
    forward = _as_bool(value)
    packets = []
    if state.speed:
        state.speed = 0
        packets.append(protocol.speed(0))
    state.forward = forward
    packets.append(protocol.direction(forward))
    return packets


def _horn(state: State, value):
    state.horn = _as_bool(value)
    return [protocol.horn(state.horn)]


def _bell(state: State, value):
    state.bell = _as_bool(value)
    return [protocol.bell(state.bell)]


def _lights(state: State, value):
    state.lights = _as_bool(value)
    return [protocol.lights(state.lights)]


def _smoke(state: State, value):
    state.smoke = _as_bool(value)
    return [protocol.smoke(state.smoke)]


def _dialog(_state: State, _value):
    return [protocol.dialog()]


def _volume(state: State, value):
    packet = protocol.master_volume(value)
    state.volume = value
    return [packet]


def _as_bool(value) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"expected true or false, got {value!r}")
    return value


ACTIONS = {
    "speed": _speed,
    "stop": _stop,
    "direction": _direction,
    "horn": _horn,
    "bell": _bell,
    "lights": _lights,
    "smoke": _smoke,
    "dialog": _dialog,
    "volume": _volume,
}
