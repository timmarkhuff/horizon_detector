#!/bin/bash
sudo pigpiod
cd horizon_detector
python3 autoupdater.py
python3 main.py


