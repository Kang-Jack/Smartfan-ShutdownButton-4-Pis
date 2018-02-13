#!/bin/sh
# launcher.sh

sudo python3.6 /root/fan_shutdown/fan_shutdown.py &

sudo python3.6 /root/fan_shutdown/mqtt_power.py &
