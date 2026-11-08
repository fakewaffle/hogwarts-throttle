# hogwarts-throttle

A full-screen touch throttle for the Lionel Hogwarts Express battery set, which has a LionChief Bluetooth LE engine. It runs on a Raspberry Pi 4 with the official 7" touch screen, starts at power-on, and finds the engine by itself.

It has speed (shown as 0–100%), direction, STOP, a whistle you hold down, bell, lights, smoke, "All aboard!" crew talk and master volume.

## Layout

- `throttle/`: the Python service. It holds the engine's state, talks Bluetooth LE to it through `bleak`, and serves the UI and a small JSON API on `127.0.0.1:8080`.
  - `protocol.py`: command bytes
  - `train.py`: state and safety rules. Connecting resets to stopped, and changing direction stops the train first.
  - `links.py`: the Bluetooth LE link, plus a fake link for development
  - `server.py`: HTTP
  - `logs.py`: rotating log file
- `web/`: the touch UI. Plain HTML, CSS and JS with an inline SVG sprite and a vendored Bebas Neue font (OFL licence).
- `deploy/`: the systemd unit, journald cap, labwc autostart, Chromium kiosk launcher and `install.sh`.
- `tests/`: `python3 -m unittest`

## Develop

    python3 -m unittest
    python3 -m throttle run --fake        # no Bluetooth; open http://127.0.0.1:8080

## Operate the Pi

Run `./pi` from the Mac. It reaches the Pi over ssh through the `raspberrypi` host alias.

    ./pi deploy        # run the tests, copy the code, reinstall the service and kiosk, reload the screen
    ./pi ui            # copy the code and reload the screen only (for web/ changes)
    ./pi status        # service state, engine connection and kiosk
    ./pi logs [N|-f]   # app log: the last N lines, or follow it
    ./pi journal       # systemd journal for this boot
    ./pi restart       # restart the throttle service
    ./pi screenshot    # capture the touch screen to a PNG
    ./pi reboot | ssh

On a fresh Pi, run `./pi deploy` once and then `./pi reboot`.

The engine address `E3:5C:B5:BE:24:42` (it advertises as `LC075630`) is set in `deploy/hogwarts-throttle.service`. To find another engine, run `python3 -m throttle scan`.

The engine takes only one connection, so a phone running Cab3 or LionChief blocks the Pi until it disconnects.

Logs go to `~/hogwarts-throttle-logs/throttle.log` (1 MB × 5 files, rotating) and to `journalctl -u hogwarts-throttle`.

## API

`GET /api/state` returns `{connected, speed, forward, horn, bell, lights, smoke, volume}`.

`POST /api/<action>` takes the body `{"value": …}`. The actions are:

- `speed` 0–31
- `stop`
- `direction` (true = forward)
- `horn`, `bell`, `lights`, `smoke` (bool)
- `dialog`
- `volume` 0–7

## Protocol

Commands are written to the characteristic `08590f7e-db05-467e-8757-72f6faeb13d4`, in the form `00 <opcode> <args…> <checksum>`. The checksum is the negated sum of the bytes. The opcodes come from Lionel's Cab3 Android app (`EngineCommand`):

| Command | Bytes |
| --- | --- |
| Speed 0–31 | `45 nn` |
| Direction fwd/rev | `46 01` / `46 02` |
| Bell, horn | `47 0/1`, `48 0/1` |
| Couplers front/rear | `49`, `4a` |
| Disconnect | `4b` |
| Master volume 0–7 | `4c nn` |
| Dialog (crew talk) | `4d 00 01` |
| Smoke | `50 0/1` |
| Per-sound volume/pitch | `44 type vol pitch` (1 horn, 2 bell, 3 speech, 4 engine) |
| Status / volumes | `01`, `04 00`, `0c` (replies on `…14d3`) |

Lights (`51 0/1`) isn't in Cab3. It comes from captures of the older LionChief app.
