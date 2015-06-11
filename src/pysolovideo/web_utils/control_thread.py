import tempfile
import os
import cv2
from threading import Thread
from pysolovideo.tracking.monitor import Monitor

# Interface to V4l
from pysolovideo.tracking.cameras import OurPiCameraAsync
from pysolovideo.tracking.cameras import MovieVirtualCamera

# Build ROIs from greyscale image
from pysolovideo.tracking.roi_builders import SleepMonitorWithTargetROIBuilder,TubeMonitorWithTargetROIBuilder

# the robust self learning tracker
from pysolovideo.tracking.trackers import AdaptiveBGModel
from pysolovideo.utils.debug import PSVException
import shutil
import logging
import time

import traceback
from pysolovideo.utils.io import ResultWriter


# http://localhost:9001/controls/3a92bcf229a34c4db2be733f6802094d/start
# {"time": "372894738."}


class ControlThread(Thread):
    _tmp_last_img_file = "last_img.jpg"
    _dbg_img_file = "dbg_img.png"
    _log_file = "psv.log"
    _mysql_db_name = "psv_db"
    _default_monitor_info =  {
                            "last_positions":None,
                            "last_time_stamp":0,
                            "fps":0
                            }
    _ROIBuilderClass = SleepMonitorWithTargetROIBuilder

    def __init__(self, machine_id, name, version, psv_dir, video_file=None, *args, **kwargs):
        self._monit_args = args
        self._monit_kwargs = kwargs
        self._metadata = None

        # for FPS computation
        self._last_info_t_stamp = 0
        self._last_info_frame_idx = 0

        # We wipe off previous data
        shutil.rmtree(psv_dir, ignore_errors=True)
        try:
            os.makedirs(psv_dir)
        except OSError:
            pass

        #self._result_file = os.path.join(result_dir, self._result_db_name)
        self._video_file = video_file

        if name.find('SM')==0:
            type_of_device = 'sm'
        elif name.find('SD')==0:
            type_of_device = 'sd'
        else:
            type_of_device = 'sm'

        self._tmp_dir = tempfile.mkdtemp(prefix="psv_")
        self._info = {  "status": "stopped",
                        "time": time.time(),
                        "error": None,
                        "log_file": os.path.join(psv_dir, self._log_file),
                        "dbg_img": os.path.join(psv_dir, self._dbg_img_file),
                        "last_drawn_img": os.path.join(self._tmp_dir, self._tmp_last_img_file),
                        "id": machine_id,
                        "name": name,
                        "version": version,
                        "type": type_of_device,
                        "db_name":self._mysql_db_name,
                        "monitor_info": self._default_monitor_info
                        }

        self._monit = None
        super(ControlThread, self).__init__()


    @property
    def info(self):
        self._update_info()
        return self._info

    def _update_info(self):
        if self._monit is None:
            return
        t = self._monit.last_time_stamp

        frame_idx = self._monit.last_frame_idx
        wall_time = time.time()
        dt = wall_time - self._last_info_t_stamp
        df = float(frame_idx - self._last_info_frame_idx)

        if self._last_info_t_stamp == 0 or dt > 0:
            f = round(df/dt, 2)
        else:
            f="NaN"
        p = self._monit.last_positions

        pos = {}
        for k,v in p.items():
            if v is None:
                continue
            pos[k] = dict(v)
            pos[k]["roi_idx"] = k

        if t is not None and p is not None:
            self._info["monitor_info"] = {
                            "last_positions":pos,
                            "last_time_stamp":t,
                            "fps": f
                            }

        f = self._monit.last_drawn_frame
        if not f is None:
            cv2.imwrite(self._info["last_drawn_img"], f)

        self._last_info_t_stamp = wall_time
        self._last_info_frame_idx = frame_idx

    def run(self):

        try:
            self._info["status"] = "initialising"
            logging.info("Starting Monitor thread")

            self._info["error"] = None


            self._last_info_t_stamp = 0
            self._last_info_frame_idx = 0
            try:
                if self._video_file is None:
                    cam = OurPiCameraAsync( target_fps=20, target_resolution=(1280, 960))
                else:
                    cam = MovieVirtualCamera(self._video_file, use_wall_clock=True)

                logging.info("Building ROIs")
                roi_builder = self._ROIBuilderClass()
                rois = roi_builder(cam)

                logging.info("Initialising monitor")
                cam.restart()

                self._metadata = {
                             "machine_id": self._info["id"],
                             "machine_name": self._info["name"],
                             "date_time": cam.start_time, #the camera start time is the reference 0
                             "frame_width":cam.width,
                             "frame_height":cam.height,
                             "version": self._info["version"]
                              }
                #the camera start time is the reference 0
                self._info["time"] = cam.start_time
                self._monit = Monitor(cam, AdaptiveBGModel, rois,
                            *self._monit_args, **self._monit_kwargs)

                logging.info("Starting monitor")

                with ResultWriter(self._mysql_db_name ,rois, self._metadata) as rw:
                    self._info["status"] = "running"
                    logging.info("Setting monitor status as running: '%s'" % self._info["status"] )
                    self._monit.run(rw)
                logging.info("Stopping Monitor thread")
                self.stop()
            finally:
                try:
                    cam._close()
                except:
                    pass

        except PSVException as e:
            if e.img is not  None:
                cv2.imwrite(self._info["dbg_img"], e.img)
            self.stop(traceback.format_exc(e))
        except Exception as e:
            self.stop(traceback.format_exc(e))


    def stop(self, error=None):
        self._info["status"] = "stopping"
        self._info["time"] = time.time()

        logging.info("Stopping monitor")
        if not self._monit is None:
            self._monit.stop()
            self._monit = None

        self._info["status"] = "stopped"
        self._info["time"] = time.time()
        self._info["error"] = error
        self._info["monitor_info"] = self._default_monitor_info

        if error is not None:
            logging.error("Monitor closed with an error:")
            logging.error(error)
        else:
            logging.info("Monitor closed all right")

    def __del__(self):
        self.stop()
        shutil.rmtree(self._tmp_dir, ignore_errors=True)
