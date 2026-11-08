import asyncio
import json
import threading
import unittest
import urllib.error
import urllib.request

from throttle import protocol
from throttle.links import FakeLink
from throttle.server import make_server
from throttle.train import Train


class FailingLink(FakeLink):
    async def write(self, packet):
        raise OSError("gone")


async def connected_train(link):
    train = Train(link)
    await link.connect()
    await train._on_connected()
    link.packets.clear()
    return train


class TrainTests(unittest.IsolatedAsyncioTestCase):
    async def test_connect_resets_engine_to_safe_state(self):
        link = FakeLink()
        train = Train(link)
        train.state.speed = 20
        await train._on_connected()
        self.assertEqual(train.state.speed, 0)
        self.assertEqual(link.packets[0], protocol.speed(0))

    async def test_speed_updates_state_and_sends(self):
        link = FakeLink()
        train = await connected_train(link)
        snapshot = await train.apply("speed", 10)
        self.assertEqual(snapshot["speed"], 10)
        self.assertEqual(link.packets, [protocol.speed(10)])

    async def test_reversing_while_moving_stops_first(self):
        link = FakeLink()
        train = await connected_train(link)
        await train.apply("speed", 8)
        link.packets.clear()
        snapshot = await train.apply("direction", False)
        self.assertEqual(link.packets, [protocol.speed(0), protocol.direction(False)])
        self.assertEqual((snapshot["speed"], snapshot["forward"]), (0, False))

    async def test_smoke_and_volume(self):
        link = FakeLink()
        train = await connected_train(link)
        await train.apply("smoke", True)
        snapshot = await train.apply("volume", 2)
        self.assertEqual((snapshot["smoke"], snapshot["volume"]), (True, 2))
        self.assertEqual(link.packets, [protocol.smoke(True), protocol.master_volume(2)])

    async def test_reconnect_turns_smoke_off(self):
        link = FakeLink()
        train = await connected_train(link)
        await train.apply("smoke", True)
        await train._on_connected()
        self.assertFalse(train.state.smoke)
        self.assertIn(protocol.smoke(False), link.packets)

    async def test_invalid_input_changes_nothing(self):
        link = FakeLink()
        train = await connected_train(link)
        for action, value in (("speed", 99), ("bell", "yes"), ("teleport", 1)):
            with self.assertRaises(ValueError):
                await train.apply(action, value)
        self.assertEqual(train.state.speed, 0)
        self.assertEqual(link.packets, [])

    async def test_cancelling_run_stops_the_engine(self):
        link = FakeLink()
        train = Train(link)
        task = asyncio.create_task(train.run())
        while not train.state.connected:
            await asyncio.sleep(0)
        await train.apply("speed", 25)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(link.packets[-1], protocol.speed(0))
        self.assertFalse(train.state.connected)

    async def test_nothing_sent_while_disconnected(self):
        link = FakeLink()
        train = Train(link)
        await train.apply("horn", True)
        self.assertEqual(link.packets, [])

    async def test_write_failure_marks_disconnected(self):
        link = FailingLink()
        train = Train(link)
        train.state.connected = True
        await train.apply("horn", True)
        self.assertFalse(train.state.connected)


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        self.link = FakeLink()
        self.train = asyncio.run_coroutine_threadsafe(connected_train(self.link), self.loop).result()
        self.server = make_server(self.train, self.loop, "127.0.0.1", 0)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.loop.call_soon_threadsafe(self.loop.stop)

    def post(self, action, value):
        request = urllib.request.Request(
            f"{self.base}/api/{action}",
            data=json.dumps({"value": value}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request) as response:
            return json.load(response)

    def test_post_command_returns_state(self):
        self.assertEqual(self.post("speed", 5)["speed"], 5)
        self.assertEqual(self.link.packets, [protocol.speed(5)])

    def test_bad_command_is_400(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.post("speed", 500)
        self.assertEqual(caught.exception.code, 400)

    def test_serves_page_and_blocks_traversal(self):
        with urllib.request.urlopen(f"{self.base}/") as response:
            self.assertIn(b"Hogwarts Express", response.read())
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(f"{self.base}/../throttle/train.py")
        self.assertEqual(caught.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
