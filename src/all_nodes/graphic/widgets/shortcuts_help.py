__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from PySide2 import QtWidgets
from PySide2 import QtCore

from all_nodes import utils
from all_nodes.graphic.widgets.global_signaler import GlobalSignaler


GS = GlobalSignaler()

LOGGER = utils.get_logger(__name__)


SHORTCUTS_DICT = {
    "Examine selected nodes code": "E",
    "Run selected nodes": "Return",
    "Reset selected nodes": "R",
    "Toggle selected nodes activation": "D",
    "Expand selected contexts": "Ctrl + Return",
    "Export selected nodes code": "Ctrl + E",
    "Soft-reset selected nodes": "S",
    "Delete selected nodes": "Del",
    "Fit to view": "F",
    "Search node class": "Tab",
}


class ShortcutsHelp(QtWidgets.QWidget):
    """Small helper widget to show the keyboard shortcuts."""

    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(QtWidgets.QLabel("KEYBOARD SHORTCUTS"))

        for action, key_shortcut in SHORTCUTS_DICT.items():
            h_layout = QtWidgets.QHBoxLayout()
            h_layout.addWidget(QtWidgets.QLabel(" " + action))
            shortcut_label = QtWidgets.QLabel(key_shortcut)
            shortcut_label.setFixedWidth(120)
            shortcut_label.setAlignment(QtCore.Qt.AlignCenter)
            shortcut_label.setStyleSheet(
                "background-color:rgba(0,0,0,150); border-radius:5px;"
            )
            h_layout.addWidget(shortcut_label)
            self.layout.addLayout(h_layout)
