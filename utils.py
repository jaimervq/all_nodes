# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import logging
import sys

from colorama import Fore, Style
from PySide2 import QtGui

from all_nodes import constants


# -------------------------------- LOGGING -------------------------------- #
def get_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(constants.LOGGING_LEVEL)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(constants.LOGGING_LEVEL)
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
    print("\n", end="")
    print(message.upper())
    print("-" * len(message))


def print_test_header(message):
    """Print a test header separator to screen

    Args:
        message (str): Message to display in the separator
    """
    message = "TEST STARTED - " + message
    print("\n", end="")
    print(f"{Fore.GREEN}+-{'-' * len(message)}-+")
    print(f"{Fore.GREEN}| {message} | ")
    print(f"{Fore.GREEN}+-{'-' * len(message)}-+ {Style.RESET_ALL}")


# -------------------------------- UTILITY -------------------------------- #
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
