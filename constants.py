# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import logging
import os

from PySide2 import QtCore
from PySide2 import QtGui


# -------------------------------- GRAPHICAL -------------------------------- #
# Overall style
GLOW_EFFECTS = True
SHOW_GRID = True
IN_SCREEN_ERRORS = True

# Line style
CONNECTOR_LINE_WIDTH = 3
TEST_LINE_PEN = QtGui.QPen(QtCore.Qt.white, CONNECTOR_LINE_WIDTH, QtCore.Qt.DashLine)
LINE_GLOW_PEN = QtGui.QPen(QtCore.Qt.magenta, CONNECTOR_LINE_WIDTH * 2)
VALID_LINE_PEN = QtGui.QPen(QtCore.Qt.white, CONNECTOR_LINE_WIDTH)
STRAIGHT_LINES = False

# Node style
STRIPE_HEIGHT = 20
CHAMFER_RADIUS = STRIPE_HEIGHT / 2
HEADER_HEIGHT = int(STRIPE_HEIGHT * 1.5)
NODE_SELECTED_PEN = QtGui.QPen(QtCore.Qt.white, 4)
NODE_SELECTED_GLOW_THICKNESS = NODE_SELECTED_PEN.width() * 2.5
NODE_ERROR_PEN = QtGui.QPen(QtCore.Qt.red, 2, QtCore.Qt.DashDotDotLine)
NODE_ERROR_BRUSH = QtGui.QBrush(QtCore.Qt.red, QtCore.Qt.BDiagPattern)
NODE_FAILED_PEN = QtGui.QPen(QtGui.QColor("orange"), 2, QtCore.Qt.DashDotDotLine)
NODE_FAILED_BRUSH = QtGui.QBrush(QtGui.QColor("orange"), QtCore.Qt.BDiagPattern)
NODE_FONT = "arial"
DEFAULT_NODE_COLOR = "#4D004C"  # magenta

# Plug style
PLUG_RADIUS = int(0.35 * STRIPE_HEIGHT)
CONNECTOR_AVAILABLE_PEN = QtGui.QPen(QtCore.Qt.gray, 2)
CONNECTOR_USED_PEN = QtGui.QPen(QtCore.Qt.white, 3)


# -------------------------------- NAMING -------------------------------- #
# Graphic
GRAPHIC_NODE = "GRAPHIC_NODE"
GRAPHIC_ATTRIBUTE = "GRAPHIC_ATTRIBUTE"
PLUG = "PLUG"
CONNECTOR_LINE = "CONNECTOR_LINE"

# Logic
INPUT = "INPUT"
OUTPUT = "OUTPUT"

START = "START"
COMPLETED = "COMPLETED"

NOT_RUN = "NOT_RUN"
SUCCESSFUL = "SUCCESSFUL"
FAILED = "FAILED"
ERROR = "ERROR"


# -------------------------------- LOGGING PREFS -------------------------------- #
LOGGING_LEVEL = logging.INFO
CONSOLE_LOG_FORMATTER = logging.Formatter(
    "%(asctime)s.%(msecs)03d %(levelname)8s- %(message)s (%(funcName)s) %(filename)s:%(lineno)d",
    datefmt="%Y%m%d %H:%M:%S",
)


# -------------------------------- DEV -------------------------------- #
IN_DEV = os.getenv("IN_DEV", False)
if IN_DEV:
    LOGGING_LEVEL = logging.DEBUG
    CONSOLE_LOG_FORMATTER = logging.Formatter(
        "%(levelname)8s- %(message)s (%(funcName)s) %(filename)s:%(lineno)d"
    )
