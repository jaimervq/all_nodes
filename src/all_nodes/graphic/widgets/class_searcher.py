# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

from all_nodes import utils
from all_nodes.logic.global_signaler import GLOBAL_SIGNALER as GS
from all_nodes.logic.class_registry import CLASS_REGISTRY as CR


LOGGER = utils.get_logger(__name__)


class ClassSearcher(QtWidgets.QWidget):
    """TODO this description"""

    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText(" Search for a class...")
        self.search_bar.setFixedHeight(40)
        self.search_bar.setStyleSheet("QLineEdit {font-size:16px}")
        self.layout.addWidget(self.search_bar)

        self.class_list = QtWidgets.QListWidget()
        self.class_list.setStyleSheet(
            "QListWidget {"
            "background-color:qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            "stop:0 rgba(255, 255, 255, 5), stop:1 rgba(255, 255, 255, 10));"
            "border:none;"
            "}"
        )
        self.class_list.setMaximumHeight(200)
        self.layout.addWidget(self.class_list)

        self.setMaximumWidth(300)
        self.setMaximumHeight(260)

        self.make_connections()

    def make_connections(self):
        self.search_bar.textChanged.connect(self.filter_classes)
        self.class_list.itemClicked.connect(self.send_node_creation_signal)

    def reset(self):
        """
        Reset the state of the widget.
        """
        self.show()  # TODO should this be separate?
        self.search_bar.clear()
        self.class_list.clear()
        QtCore.QTimer.singleShot(50, self.search_bar.setFocus)

    def filter_classes(self):
        """
        Filter the list of classes based on the text entered in the search bar.
        """
        self.class_list.clear()
        current_text = self.search_bar.text()
        if not current_text:
            return
        for class_name, icon_path in CR.get_all_classes_simplified():
            if current_text.lower() in class_name.lower():
                i = QtWidgets.QListWidgetItem(class_name)
                i.setIcon(QtGui.QIcon(icon_path))
                self.class_list.addItem(i)

        if self.class_list.item(0):
            self.class_list.item(0).setSelected(True)

    def send_node_creation_signal(self):
        """
        Send a signal to request the creation of a node based on selection
        """
        if self.class_list.selectedItems():
            GS.signals.node_creation_requested.emit(
                self.mapToGlobal(QtCore.QPoint(0, 0)) - QtCore.QPoint(100, 50),
                self.class_list.selectedItems()[0].text(),
            )
        self.hide()

    def keyPressEvent(self, event: QtWidgets.QWidget.event):
        QtWidgets.QWidget.keyPressEvent(self, event)

        modifiers = QtWidgets.QApplication.keyboardModifiers()

        if event.key() == QtCore.Qt.Key_Return and not modifiers:
            self.send_node_creation_signal()

        elif event.key() == QtCore.Qt.Key_Down and not modifiers:
            index = self.class_list.indexFromItem(self.class_list.selectedItems()[0])
            row = index.row()
            new_selected = self.class_list.item(row + 1)
            if new_selected:
                self.class_list.selectedItems()[0].setSelected(False)
                new_selected.setSelected(True)

        elif event.key() == QtCore.Qt.Key_Up and not modifiers:
            index = self.class_list.indexFromItem(self.class_list.selectedItems()[0])
            row = index.row()
            new_selected = self.class_list.item(row - 1)
            if new_selected:
                self.class_list.selectedItems()[0].setSelected(False)
                new_selected.setSelected(True)

        event.setAccepted(True)
