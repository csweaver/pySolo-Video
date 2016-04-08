README
======

pySolo-Video is a standalone program that provides video tracking
capabilities meant for studying sleep in Drosophila

Input can be:

* usb camera handled through opencv
* single movie files (mov, avi, etc)
* folders containing sequences of snapshots
    
Tracking is done using findContours algorithm of opencv.

It works through a GUI interface

REQUIRES:
------

* `python 2.x`
* `wxpython 2.8`
* `opencv`
* `numpy`
* `pyserial`
