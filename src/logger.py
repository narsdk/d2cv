import logging as log
import logging.handlers
import os
from vlogging import VisualRecord

LOG_LEVEL = log.DEBUG

class GameError(Exception):
    def __init__(self, *args):
        Exception.__init__(self, *args)


# Improve RotateExtensionLogs class - add possibility to include file extension to log file name
class RotateExtensionLogs(log.handlers.RotatingFileHandler):
    def __init__(self, filename, mode='a', maxbytes=0, backupcount=0, encoding=None, delay=False, file_extension=""):
        super().__init__(filename, mode, maxbytes, backupcount, encoding, delay)
        self.file_extension = file_extension

    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename("%s.%d.%s" % (self.baseFilename, i, self.file_extension))
                dfn = self.rotation_filename("%s.%d.%s" % (self.baseFilename, i + 1, self.file_extension))
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = self.rotation_filename(self.baseFilename + ".1." + self.file_extension)
            if os.path.exists(dfn):
                os.remove(dfn)
            self.rotate(self.baseFilename, dfn)
        if not self.delay:
            self.stream = self._open()


# Add new logging level - visual
visual_level = log.INFO - 1
visual_name = "VISUAL"
visual_method_name = "visual"


def log_for_level(self, message, *args, **kwargs):
    if self.isEnabledFor(visual_level):
        self._log(visual_level, message, args, **kwargs)


def log_to_root(message, *args, **kwargs):
    log.log(visual_level, message, *args, **kwargs)


log.addLevelName(visual_level, visual_name)
setattr(log, visual_name, visual_level)
setattr(log.getLoggerClass(), visual_method_name, log_for_level)
setattr(log, visual_method_name, log_to_root)


# Set file logger
log_name = 'log/d2cv-log.html'

# Set console logger
should_roll_over = os.path.isfile(log_name)
html_handler = RotateExtensionLogs(log_name, mode='w', backupcount=10, maxbytes=100000, file_extension="html")
if should_roll_over:  # log already exists, roll over!
    html_handler.doRollover()

html_log_format = '[%(asctime)s.%(msecs)03d] [%(levelname)s] %(module)s - %(funcName)s: %(message)s<br>'

log.basicConfig(
    filename=log_name,
    level=LOG_LEVEL,
    format=html_log_format,
    datefmt='%H:%M:%S',
)

log_format = '[%(asctime)s.%(msecs)03d] [%(levelname)s] %(module)s - %(funcName)s: %(message)s'
console_logging = log.StreamHandler()
console_logging.setLevel(LOG_LEVEL)
console_logging.setFormatter(log.Formatter(log_format))
log.getLogger().addHandler(console_logging)