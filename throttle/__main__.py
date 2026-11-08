import argparse
import asyncio
import logging
import threading
from pathlib import Path

from .logs import setup_logging
from .links import BleLink, FakeLink, scan
from .server import make_server
from .train import Train


async def serve(args) -> None:
    link = FakeLink() if args.fake else BleLink(args.address)
    train = Train(link)
    server = make_server(train, asyncio.get_running_loop(), args.host, args.port)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logging.info("throttle on http://%s:%d", args.host, args.port)
    await train.run()


async def print_scan() -> None:
    for address, name, rssi in await scan():
        print(f"{address}  {rssi:>4} dBm  {name}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="throttle", description="Touch throttle for a LionChief Bluetooth engine")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="connect to the engine and serve the throttle page")
    target = run.add_mutually_exclusive_group(required=True)
    target.add_argument("--address", help="engine Bluetooth address (find it with `scan`)")
    target.add_argument("--fake", action="store_true", help="no Bluetooth; log packets instead")
    run.add_argument("--host", default="127.0.0.1")
    run.add_argument("--port", type=int, default=8080)
    run.add_argument("--log-file", type=Path, help="also log here, rotated at 1 MB x 5")
    sub.add_parser("scan", help="list nearby Bluetooth LE devices")
    args = parser.parse_args()

    setup_logging(getattr(args, "log_file", None))
    asyncio.run(print_scan() if args.command == "scan" else serve(args))


main()
