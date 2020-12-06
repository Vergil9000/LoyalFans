import os
import sys
import logging
import platform

from blessed import Terminal


class Logger:
    status_error = "There was an error connecting to LoyalFans's servers. This could either be because their servers are down or because your 'authorization' cookie has expired."
    key_error = f"There was an error retrieving data from the LoyalFans API. This could be due to them changing their API. Please file an issue on Github at:\nhttps://github.com/Amenly/LoyalFans/issues/new\nAn error log was created and updated at {os.path.join(sys.path[0], 'error.log')}. Please copy and paste the content pertaining to this issue. The traceback may contain your name/username; if you need to, you can remove those parts."

    wait1 = "Please be patient, this user may have a lot of content..."
    wait2 = "Still scraping..."

    def __init__(self, debug):
        self.term = Terminal()
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)
            INFO_FORMAT = f"{self.term.cyan('%(levelname)s')}: %(message)s"
        else:
            self.logger.setLevel(logging.INFO)
            INFO_FORMAT = "%(message)s"
        DATE_FORMAT = "%b-%d-%Y %I:%M:%S %p"
        ERROR_FORMAT = f"%(asctime)s:{self.term.red('%(levelname)s')}:{platform.platform()}:{platform.python_version()}\nError: {self.term.red('%(message)s')}"
        info_formatter = logging.Formatter(fmt=INFO_FORMAT)
        error_formatter = logging.Formatter(
            fmt=ERROR_FORMAT, datefmt=DATE_FORMAT)
        stream_handler = logging.StreamHandler()
        file_handler = logging.FileHandler(
            os.path.join(sys.path[0], "error.log"))
        stream_handler.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.ERROR)
        stream_handler.setFormatter(info_formatter)
        file_handler.setFormatter(error_formatter)
        self.logger.addHandler(stream_handler)
        self.logger.addHandler(file_handler)

    def error(self, message):
        self.logger.error(message, exc_info=1)

    def info(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)
