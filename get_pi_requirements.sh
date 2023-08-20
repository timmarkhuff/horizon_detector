#!/bin/bash

# Get packages required for OpenCV
sudo apt-get -y install libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev
sudo apt-get -y install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt-get -y install libxvidcore-dev libx264-dev
sudo apt-get -y install qt4-dev-tools 
sudo apt-get -y install libatlas-base-dev

# Some additional dependencies according to https://www.youtube.com/watch?v=QzVYnG-WaM4
sudo apt install -y build-essential cmake pkg-config libjpeg-dev libtiff5-dev libpng-dev libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev libfontconfig1-dev libcairo2-dev libgdk-pixbuf2.0-dev libpango1.0-dev libgtk2.0-dev libgtk-3-dev libatlas-base-dev gfortran libhdf5-dev libhdf5-serial-dev libhdf5-103 libqt5gui5 libqt5webkit5 libqt5test5 python3-pyqt5 python3-dev

# Now using this version. It's the latest version that contains a pre-built wheel for the Pi
pip3 install opencv-python-headless==4.4.0.46

# may need to install this according to https://raspberrypi-guide.github.io/programming/install-opencv
pip3 install -U numpy

# For the PID controller
pip3 install simple-pid==2.0.0

# For displaying images in the terminal
# pip3 install imgcat

# for SBUS
pip install bitarray