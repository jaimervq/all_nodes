__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtSvg
from PySide2 import QtWidgets

from all_nodes import constants
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


ANNOTATION_TYPES_WITH_TEXT = [
    "note",
    "paper",
    "long_tag",
    "short_tag",
    "notepad",
    "post_it",
]


# -------------------------------- ANNOTATION CLASS -------------------------------- #
class GeneralGraphicAnnotation(QtWidgets.QGraphicsPathItem):
    def __init__(self, annotation_type: str):
        # INIT
        QtWidgets.QGraphicsPathItem.__init__(self)
        self.setData(0, constants.GRAPHIC_ANNOTATION)
        self.setAcceptHoverEvents(True)
        self.setFlags(
            QtWidgets.QGraphicsPathItem.ItemIsMovable
            | QtWidgets.QGraphicsPathItem.ItemIsSelectable
            | QtWidgets.QGraphicsPathItem.ItemSendsScenePositionChanges
        )

        self.setPen(QtCore.Qt.NoPen)

        # Setup graphics
        self.annotation_type = annotation_type
        self.width = 0
        self.height = 0
        self.setup_graphics()

    def setup_graphics(self):
        # Main graphics
        self.renderer = QtSvg.QSvgRenderer(f"graphics:{self.annotation_type}.svg")
        main_graphics = QtSvg.QGraphicsSvgItem(parentItem=self)
        main_graphics.setSharedRenderer(self.renderer)

        self.width = main_graphics.boundingRect().width()
        self.height = main_graphics.boundingRect().height()

        padding = 40

        # Text input
        self.proxy_edit = QtWidgets.QGraphicsProxyWidget(parent=self)
        self.note_text_edit = QtWidgets.QPlainTextEdit()
        self.note_text_edit.setFont(QtGui.QFont("arial", 8))
        self.note_text_edit.setStyleSheet(
            "color:black; background-color:transparent; border:1px dotted rgba(100,100,100,120);"
        )
        self.note_text_edit.setFixedSize(self.width - padding, self.height - padding)
        self.note_text_edit.setPlainText("Write here...")
        self.proxy_edit.setWidget(self.note_text_edit)
        self.proxy_edit.setPos(
            self.width,
            self.height,
        )

        if self.annotation_type not in ANNOTATION_TYPES_WITH_TEXT:
            self.proxy_edit.hide()

        # Main shape
        path = QtGui.QPainterPath()
        path.addRect(
            QtCore.QRect(
                0,
                0,
                self.width + padding,
                self.height + padding,
            ),
        )
        main_graphics.setPos(padding / 2, padding / 2)
        self.proxy_edit.setPos(padding, padding)
        self.setPath(path)

    def get_type(self):
        return self.annotation_type

    def get_text(self):
        if self.annotation_type in ANNOTATION_TYPES_WITH_TEXT:
            return self.note_text_edit.toPlainText()
        return None

    def set_text(self, text: str):
        self.note_text_edit.setPlainText(text)
