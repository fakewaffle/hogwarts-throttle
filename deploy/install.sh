#!/bin/sh
# Run on the Pi from ~/hogwarts-throttle. Re-runnable.
set -e
cd "$(dirname "$0")/.."

sudo apt-get install -y -qq python3-bleak chromium curl
chmod +x deploy/kiosk.sh
sudo cp deploy/hogwarts-throttle.service /etc/systemd/system/
sudo mkdir -p /etc/systemd/journald.conf.d
sudo cp deploy/journald-throttle.conf /etc/systemd/journald.conf.d/throttle.conf
sudo systemctl restart systemd-journald
sudo systemctl daemon-reload
sudo systemctl enable --now hogwarts-throttle
sudo systemctl restart hogwarts-throttle

mkdir -p ~/.config/labwc
cp deploy/labwc-autostart ~/.config/labwc/autostart
echo "Installed. Reboot to start the kiosk."
