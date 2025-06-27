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


class NodeHelpWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help")
        self.setWindowIcon(QtGui.QIcon("icons:help.png"))
        f = QtCore.QFile(r"ui:stylesheet.qss")
        with open(f.fileName(), "r") as s:
            self.setStyleSheet(s.read())
        self.resize(800, 600)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.layout)

        self.text = QtWidgets.QTextEdit()
        self.text.setStyleSheet("border:none")
        self.text.setReadOnly(True)
        self.text.setWordWrapMode(QtGui.QTextOption.WrapMode.WordWrap)
        self.text.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.layout.addWidget(self.text)

        self.run_text = QtWidgets.QTextEdit()
        self.run_text.setReadOnly(True)
        self.run_text.setFont(QtGui.QFont("arial", 12))
        self.run_text.setStyleSheet(
            "background-color:black;border:none;border-radius:5px"
        )
        self.run_text.setWordWrapMode(QtGui.QTextOption.WrapMode.WordWrap)
        self.run_text.document().setDocumentMargin(15)
        self.run_text.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.layout.addWidget(self.run_text)

    def set_text(self, html_text):
        self.text.insertHtml(html_text)

    def set_run_text(self, run_html_text):
        self.run_text.insertHtml(run_html_text)
