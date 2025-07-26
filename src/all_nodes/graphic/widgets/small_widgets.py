# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2 import QtSvg

from all_nodes.logic.global_signaler import GLOBAL_SIGNALER as GS


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
            self.mapToGlobal(event.pos()) - QtCore.QPoint(100, 50)
        )

    def contextMenuEvent(self, event):
        event.ignore()
        self.parent().contextMenuEvent(event)


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


class FakeConsole(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        font = QtGui.QFont("Consolas")
        font.setStyleHint(QtGui.QFont.Monospace)
        self.setFont(font)
        self.setStyleSheet("""
            QTextEdit {     
                background-color: black;
                color: lime;
                border: none;
                padding: 5px;
            }
                    
            QScrollBar:vertical {
                background: transparent;
                width: 12px;
                margin: 0px;
                border: none;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background: limegreen;
                min-height: 20px;
                border-radius: 6px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
                height: 0px;
            }
        """)

        self.setWordWrapMode(QtGui.QTextOption.WrapMode.WordWrap)
        self.setPlaceholderText(">")


class StopButton(QtWidgets.QPushButton):
    def __init__(self, svg_path, parent=None):
        super().__init__(parent)
        self._scale = 1.0
        self.renderer = QtSvg.QSvgRenderer(svg_path)
        self.anim = QtCore.QPropertyAnimation(self, b"scale")
        self.anim.setDuration(1000)
        self.anim.setEasingCurve(QtCore.QEasingCurve.OutBack)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def enterEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self._scale)
        self.anim.setEndValue(1.1)
        self.anim.start()

    def leaveEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self._scale)
        self.anim.setEndValue(1.0)
        self.anim.start()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        if not painter.isActive():
            return
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._scale - 0.2, self._scale - 0.2)
        painter.translate(-self.width() / 2, -self.height() / 2)
        self.renderer.render(painter)

    def getScale(self):
        return self._scale

    def setScale(self, value):
        self._scale = value
        self.update()

    scale = QtCore.Property(float, getScale, setScale)
