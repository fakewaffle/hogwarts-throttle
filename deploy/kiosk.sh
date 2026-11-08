#!/bin/sh
# Launched by labwc at login: wait for the throttle server, then show it full screen.
URL=http://127.0.0.1:8080/

until curl -sf -o /dev/null "$URL"; do sleep 1; done

exec chromium "$URL" \
  --kiosk \
  --ozone-platform=wayland \
  --noerrdialogs \
  --disable-infobars \
  --disable-pinch \
  --overscroll-history-navigation=0 \
  --no-first-run \
  --password-store=basic \
  --disable-features=Translate
