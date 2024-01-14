# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from PySide2 import QtGui
from PySide2 import QtWidgets, QtCore

from all_nodes import utils
from all_nodes.graphic.widgets.global_signaler import GLOBAL_SIGNALER as GS
from all_nodes.logic.class_registry import CLASS_REGISTRY as CR


LOGGER = utils.get_logger(__name__)


class ClassSearcher(QtWidgets.QWidget):
    """TODO"""

    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search for a class...")
        self.layout.addWidget(self.search_bar)

        self.class_list = QtWidgets.QListWidget()
        self.layout.addWidget(self.class_list)

        self.make_connections()

    def make_connections(self):
        self.search_bar.textChanged.connect(self.filter_classes)
        self.class_list.itemDoubleClicked.connect(self.send_signal)

    def reset(self):
        self.search_bar.clear()
        self.class_list.clear()
        self.show()
        self.search_bar.setFocus()

    def filter_classes(self):
        self.class_list.clear()
        current_text = self.search_bar.text()
        if not current_text:
            return
        for class_name, icon_path in CR.get_all_classes_simplified():
            if current_text.lower() in class_name.lower():
                i = QtWidgets.QListWidgetItem(class_name)
                i.setIcon(QtGui.QIcon(icon_path))
                self.class_list.addItem(i)

    def keyPressEvent(self, event: QtWidgets.QWidget.event):
        QtWidgets.QWidget.keyPressEvent(self, event)

        modifiers = QtWidgets.QApplication.keyboardModifiers()

        if event.key() == QtCore.Qt.Key_Return and not modifiers:
            self.send_signal()

    def send_signal(self):
        # TODO rename this one
        if self.class_list.selectedItems():
            GS.node_creation_requested.emit(
                self.pos(),
                self.class_list.selectedItems()[0].text(),
            )
        self.hide()
