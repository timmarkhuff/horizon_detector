#!/bin/bash

# Get packages required for OpenCV

sudo apt-get -y install libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev
sudo apt-get -y install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt-get -y install libxvidcore-dev libx264-dev
sudo apt-get -y install qt4-dev-tools 
sudo apt-get -y install libatlas-base-dev

# Need to get an older version of OpenCV because version 4 has errors
# pip3 install opencv-python==3.4.11.41 # previously used this version

# Now using this version. It's the latest version that contains a pre-built wheel for the Pi
pip3 install opencv-python==4.4.0.46

# For the PID controller
pip3 install simple-pid==2.0.0

# For displaying images in the terminal
pip3 install imgcat