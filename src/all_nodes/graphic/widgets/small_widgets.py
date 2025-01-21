# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2 import QtCore

from all_nodes.graphic.widgets.global_signaler import GlobalSignaler


GS = GlobalSignaler()


class FeedbackLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setReadOnly(True)
        self.setFont(QtGui.QFont("arial", 13))
        self.hide()

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        event.ignore()
        GS.signals.dropped_node.emit(
            self.mapToParent(self.rect().topLeft())
            + event.pos()
            - QtCore.QPoint(20, 20)
        )

    def mousePressEvent(self, event):
        event.ignore()
        super().mousePressEvent(event)
