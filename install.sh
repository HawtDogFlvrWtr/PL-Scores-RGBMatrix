#!/bin/bash

# Just in case you used the zip
apt install git

# Create service
cp pl_display.service /lib/systemd/system/
systemctl enable pl_display.service
cd /opt
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd /opt/rpi-rgb-led-matrix
make -C examples-api-use

# Setup python bindings
cd /opt/rpi-rgb-led-matrix/bindings/python/
sudo apt-get update && sudo apt-get install python3-dev python3-pillow libcairo2-devel python3-cairo -y
make build-python PYTHON=$(command -v python3)
sudo make install-python PYTHON=$(command -v python3)

# Blacklist Soundcard
cat <<EOF | sudo tee /etc/modprobe.d/blacklist-rgb-matrix.conf
blacklist snd_bcm2835
EOF
