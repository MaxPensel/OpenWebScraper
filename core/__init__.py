import os
import sys
from logging import Formatter, FileHandler, StreamHandler, Logger, INFO

MASTER_LOG = "master.log"


def simple_logger(modname="core", file_path=None, console_level=INFO, file_level=INFO) -> Logger:
    """
    Create a logging.Logger instance and configure it with console stream handler and optionally file handler.
    Format is kept simple and universal with '[modname] time - level - message'
    If no file_path is given (default: None), then log messages are only provided in console.
    If file_path is provided, it will also create the required directory structure if necessary.

    :param modname: name of the module producing log messages (default: core)
    :param file_path: path to log file, give relative path, starting from %workspace%/logs/  (default: None)
    :param console_level: level of log messages for the console stream handler (default: INFO)
    :param file_level: level of log messages for the file stream handler (default: INFO)
    :return: configured instance of logging.Logger
    """
    # setup logger format
    log_fmt = Formatter(fmt="[{0}] %(asctime)s - %(levelname)s - %(message)s".format(modname))

    logger = Logger(modname)

    log_ch = StreamHandler(sys.stdout)
    log_ch.setLevel(console_level)
    log_ch.setFormatter(log_fmt)

    logger.addHandler(log_ch)

    if file_path:
        parent_dir = os.path.abspath(os.path.join(file_path, os.pardir))
        if not file_path.endswith(".log"):
            logger.warning("Log files are recommended to end in '.log'.")
        if not os.path.exists(parent_dir):
            logger.info("Directory {0} is being created for logging.".format(parent_dir))
            os.makedirs(parent_dir, exist_ok=True)

        log_fh = FileHandler(file_path, mode="a")
        log_fh.setFormatter(log_fmt)
        log_fh.setLevel(file_level)

        logger.addHandler(log_fh)

    return logger
