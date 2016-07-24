#!/bin/bash
xinput set-prop "eGalax Inc. USB TouchController" "Evdev Axes Swap" "1"
xinput set-prop "eGalax Inc. USB TouchController" "Coordinate Transformation Matrix" 1.3 0 -0.15 0 1.3 -0.15 0 0 1
ENV=PI
cd /home/pi/drinks-scanner-display && python game.py
