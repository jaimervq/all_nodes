# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import logging
import re
import sys

from colorama import Fore, Style
from PySide2 import QtGui

from all_nodes import constants


# -------------------------------- LOGGING -------------------------------- #
def get_logger(logger_name: str) -> logging.Logger:
    """Get a logger with a specific formatting

    Args:
        logger_name (str)

    Returns:
        logging.Logger
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(constants.LOGGING_LEVEL)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(constants.LOGGING_LEVEL)
    console_handler.setFormatter(constants.CONSOLE_LOG_FORMATTER)
    logger.addHandler(console_handler)
    return logger


LOGGER = get_logger(__name__)


def print_separator(message):
    """Print a separator to screen

    Args:
        message (str): Message to display in the separator
    """
    LOGGER.info(f"\n{message.upper()}\n{'-' * len(message)}")


def print_test_header(message):
    """Print a test header separator to screen

    Args:
        message (str): Message to display in the separator
    """
    header = f"TEST STARTED - {message}"
    print(
        f"{Fore.GREEN}+-{'-' * len(header)}-+\n"
        f"{Fore.GREEN}| {header} |\n"
        f"{Fore.GREEN}+-{'-' * len(header)}-+ {Style.RESET_ALL}"
    )


# -------------------------------- LOGIC UTILITY -------------------------------- #
def parse_datatype(datatype_str):
    if re.match("<class '.+\.(.+)'>", datatype_str):
        return re.match("<class '.+\.(.+)'>", datatype_str).group(1)
    elif re.match("<module '.+\.(.+)' from", datatype_str):
        return re.match("<module '.+\.(.+)' from", datatype_str).group(1)
    return re.search("'(.+)'", datatype_str).group(1)


# -------------------------------- GUI UTILITY -------------------------------- #
def get_bright_color(color_name):
    """Given a color name, get a fully saturated and bright version of it

    Args:
        color_name (str): name of the color to saurate

    Returns:
        str: name of the saturated color
    """
    base_color = QtGui.QColor(color_name)
    h = base_color.hue()

    bright_color = QtGui.QColor.fromHsv(h, 255, 255)
    return bright_color.name()
