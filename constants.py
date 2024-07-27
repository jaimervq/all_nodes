# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from enum import Enum
import logging
import os

from PySide2 import QtCore
from PySide2 import QtGui


# -------------------------------- GRAPHIC -------------------------------- #
# Overall style
GLOW_EFFECTS = True
SHOW_GRID = True
IN_SCREEN_ERRORS = True

# Line style
CONNECTOR_LINE_WIDTH = 3
TEST_LINE_PEN = QtGui.QPen(QtCore.Qt.white, CONNECTOR_LINE_WIDTH, QtCore.Qt.DashLine)
LINE_GLOW_PEN = QtGui.QPen(QtCore.Qt.magenta, CONNECTOR_LINE_WIDTH * 2)
VALID_LINE_PEN = QtGui.QPen(QtCore.Qt.white, CONNECTOR_LINE_WIDTH)
STRAIGHT_LINES = 0
STEPPED_LINES = 1
SPLINE_LINES = 2
CONNECTOR_LINE_GEO = SPLINE_LINES

# Node style
STRIPE_HEIGHT = 20
CHAMFER_RADIUS = STRIPE_HEIGHT / 2
HEADER_HEIGHT = int(STRIPE_HEIGHT * 1.5)
NODE_CONTOUR_THICKNESS = 1.0
NODE_SELECTED_PEN = QtGui.QPen(QtCore.Qt.white, 2.5)
NODE_SELECTED_GLOW_THICKNESS = NODE_SELECTED_PEN.width() * 2.5
NODE_ERROR_PEN = QtGui.QPen(QtCore.Qt.red, 2, QtCore.Qt.DashDotDotLine)
NODE_DEACTIVATED_PEN = QtGui.QPen(QtGui.QColor(15, 15, 10, 235), 10)
NODE_ERROR_BRUSH = QtGui.QBrush(QtCore.Qt.red, QtCore.Qt.BDiagPattern)
NODE_FAILED_PEN = QtGui.QPen(QtGui.QColor("orange"), 2, QtCore.Qt.DashDotDotLine)
NODE_FAILED_BRUSH = QtGui.QBrush(QtGui.QColor("orange"), QtCore.Qt.BDiagPattern)
NODE_FONT = "arial"
DEFAULT_NODE_COLOR = "#4D004C"  # magenta

# Plug style
PLUG_RADIUS = int(0.3 * STRIPE_HEIGHT)
CONNECTOR_USED_PEN = QtGui.QPen(QtCore.Qt.white, 3)

# Naming
GRAPHIC_NODE = "GRAPHIC_NODE"
GRAPHIC_ATTRIBUTE = "GRAPHIC_ATTRIBUTE"

PLUG = "PLUG"
CONNECTOR_LINE = "CONNECTOR_LINE"

GRAPHIC_ANNOTATION = "GRAPHIC_ANNOTATION"


# -------------------------------- LOGIC -------------------------------- #
# Naming
INPUT = "INPUT"
OUTPUT = "OUTPUT"

INTERNAL = "INTERNAL"

START = "START"
COMPLETED = "COMPLETED"

# Node statuses
NOT_RUN = "NOT_RUN"
EXECUTING = "EXECUTING"
IN_LOOP = "IN_LOOP"
SKIPPED = "SKIPPED"
SUCCESSFUL = "SUCCESSFUL"
FAILED = "FAILED"
ERROR = "ERROR"


# -------------------------------- GUI INPUT / PREVIEW TYPES -------------------------------- #
class InputsGUI(Enum):
    STR_INPUT = "String input"
    MULTILINE_STR_INPUT = "Multiline string input"
    INT_INPUT = "Integer input"
    FLOAT_INPUT = "Float input"
    BOOL_INPUT = "Boolean input"
    OPTION_INPUT = "Option input"
    TUPLE_INPUT = "Tuple input"
    DICT_INPUT = "Dictionary input"
    LIST_INPUT = "List input"


class PreviewsGUI(Enum):
    STR_PREVIEW = "String preview"
    MULTILINE_STR_PREVIEW = "Multiline string preview"
    DICT_PREVIEW = "Dictionary preview"
    IMAGE_PREVIEW = "Image preview"


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

# -------------------------------- ANALYTICS -------------------------------- #
DB_ENV = os.getenv("DB_ENV", "PROD")
if IN_DEV:
    DB_ENV = "DEV"
