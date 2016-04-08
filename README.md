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


## TODO
Saving mask file from pvg_standalone results in error

    sult in an elementwise object comparison in the future.
    if self.referencePoints == None:
    Traceback (most recent call last):
    File "/Users/chenn/Documents/GitHub/pySolo-Video/pvg_common.py", line 500, in onKeyPressed
    self.ACTIONS[key][0]()
    File "/Users/chenn/Documents/GitHub/pySolo-Video/pvg_common.py", line 574, in SaveMask
    self.mon.saveROIS()
    File "/Users/chenn/Documents/GitHub/pySolo-Video/pysolovideo.py", line 1624, in saveROIS
    self.mask.saveROIS( filename, self.cam.getSerialNumber() )
    File "/Users/chenn/Documents/GitHub/pySolo-Video/pysolovideo.py", line 860, in saveROIS
    json.dumps({self.ROIS, self.points_to_track, self.referencePoints, self.serial},cf)
    TypeError: unhashable type: 'numpy.ndarray'
