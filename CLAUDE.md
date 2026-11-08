# hogwarts-throttle

A Raspberry Pi touch-screen throttle for the Lionel Hogwarts Express battery set, which has a LionChief Bluetooth LE engine. See `README.md` for the layout, setup and the command table.

## Rules

- **Don't move the real train without asking.** The engine on the Pi is live: a `POST /api/speed` makes a kid's toy drive off. Test with `python3 -m throttle run --fake` on the Mac. On the Pi, only read state (`GET /api/state`) and the logs unless the owner says go.
- **The UI is touch-screen only.** The owner decided on no phone or LAN access, so the server binds `127.0.0.1`. Don't open it up without asking.
- **Command bytes come from Lionel's Cab3 Android app** (`EngineCommand` in the decompiled Xamarin assemblies). Prefer that source over the older hobbyist README tables, which mislabel `0x4B` (it's Disconnect, not volume). Lights (`0x51`) is the one command that isn't in Cab3.
- `web/` is plain HTML, CSS and JS: no build step, no CDN, and everything served locally. The Pi may be offline.
- The only dependency is `bleak`, installed from apt (`python3-bleak`) and never from pip.

## Pi

- `ssh raspberrypi` connects as `pi@raspberrypi.local` with key `~/.ssh/raspberrypi_ed25519`. It's a Pi 4 running Debian trixie and labwc (Wayland), with the official 800×480 DSI screen.
- Deploy: `rsync -a --delete --exclude __pycache__ ./ raspberrypi:hogwarts-throttle/`, then `ssh raspberrypi sh hogwarts-throttle/deploy/install.sh`. After a UI-only change, `ssh raspberrypi pkill -x chromium` is enough, since `lwrespawn` relaunches the kiosk.
- Never run `pkill -f 'chromium.*kiosk'` over ssh: the pattern matches the ssh command itself and kills the session.
- Screenshot the screen: `ssh raspberrypi 'XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 grim /tmp/shot.png'`.
- Logs are in `~/hogwarts-throttle-logs/throttle.log` (1 MB × 5, rotating) and in `journalctl -u hogwarts-throttle`. The journal is capped at 50 MB.

## Bluetooth traps

- The engine accepts one connection. A phone running Cab3 or LionChief locks the Pi out.
- If the process dies, BlueZ keeps the link up and the engine stops advertising. `BleLink` runs `bluetoothctl disconnect` whenever a scan misses, so the next attempt can see it.
- Each `BleakClient` gets its own close event, so a stale client's late disconnect callback can't drop a newer link.

## Tests

`python3 -m unittest`. Use the standard library only.
