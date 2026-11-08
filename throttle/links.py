import asyncio
import logging

from . import protocol

log = logging.getLogger(__name__)


class BleLink:
    def __init__(self, address: str):
        self._address = address
        self._client = None
        self._closed = asyncio.Event()

    async def connect(self) -> None:
        from bleak import BleakClient, BleakScanner

        await self.close()
        device = await BleakScanner.find_device_by_address(self._address, timeout=10)
        if device is None:
            # An engine still held by a dead process stays connected in BlueZ and stops advertising.
            await _release_in_bluez(self._address)
            raise ConnectionError(f"engine {self._address} not found; is it on and in range?")
        # Each client gets its own event so a stale client's late callback can't close a newer link.
        closed = asyncio.Event()
        client = BleakClient(device, disconnected_callback=lambda _c: closed.set())
        try:
            await client.connect()
        except BaseException:
            await _quietly_disconnect(client)
            raise
        self._client = client
        self._closed = closed

    async def write(self, packet: bytes) -> None:
        if self._client is None:
            raise ConnectionError("not connected")
        await self._client.write_gatt_char(protocol.CHARACTERISTIC, packet, response=True)

    async def wait_closed(self) -> None:
        await self._closed.wait()

    async def close(self) -> None:
        client, self._client = self._client, None
        if client is not None:
            await _quietly_disconnect(client)
        self._closed.set()


async def _release_in_bluez(address: str) -> None:
    try:
        process = await asyncio.create_subprocess_exec(
            "bluetoothctl", "disconnect", address,
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(process.wait(), timeout=10)
    except (OSError, TimeoutError) as error:
        log.debug("bluetoothctl disconnect failed: %r", error)


async def _quietly_disconnect(client) -> None:
    try:
        await client.disconnect()
    except Exception as error:
        log.debug("disconnect failed: %r", error)


class FakeLink:
    """Stands in for the engine so the UI can be developed without Bluetooth."""

    def __init__(self):
        self.packets: list[bytes] = []
        self._closed = asyncio.Event()

    async def connect(self) -> None:
        self._closed = asyncio.Event()

    async def write(self, packet: bytes) -> None:
        log.info("fake engine <- %s", packet.hex(" "))
        self.packets.append(packet)

    async def wait_closed(self) -> None:
        await self._closed.wait()

    async def close(self) -> None:
        self._closed.set()


async def scan(seconds: float = 8.0) -> list[tuple[str, str, int]]:
    from bleak import BleakScanner

    found = await BleakScanner.discover(timeout=seconds, return_adv=True)
    rows = [(device.address, adv.local_name or device.name or "?", adv.rssi) for device, adv in found.values()]
    return sorted(rows, key=lambda row: -row[2])
