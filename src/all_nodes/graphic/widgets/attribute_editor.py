# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

from all_nodes import constants
from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes.logic.class_registry import CLASS_REGISTRY as CR


from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class NodePanel(QtWidgets.QWidget):
    """Widget representation of a logic node and its attributes"""

    def __init__(self, logic_node: GeneralLogicNode):
        QtWidgets.QWidget.__init__(self)

        self.grid_layout = QtWidgets.QGridLayout()
        self.setLayout(self.grid_layout)

        self.logic_node = logic_node

        self.color = self.get_node_color()
        self.get_node_color()

        self.row_count = 0
        self.represent_node()

    def get_node_color(self):
        """
        Examine the configs and find the color associated to the represented node

        Returns:
            QtGui.QColor: color that corresponds to the logic node

        """
        all_classes = CR.get_all_classes()
        node_color = QtGui.QColor(constants.DEFAULT_NODE_COLOR)
        for lib in all_classes:
            for module in all_classes[lib]:
                classes = all_classes[lib][module]["classes"]
                for c in classes:
                    c_name, _ = c
                    if c_name == self.logic_node.class_name:
                        node_color = QtGui.QColor(all_classes[lib][module]["color"])
                        node_color.setAlphaF(0.8)
                        return node_color

        return node_color

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        qp = QtGui.QPainter()
        qp.begin(self)

        # Fill
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRect(0, 0, self.width(), self.height() - 2), 12, 12)
        linearGrad = QtGui.QLinearGradient(0, 0, 0, self.height())
        linearGrad.setColorAt(0.0, QtGui.QColor(255, 255, 255, 50))
        linearGrad.setColorAt(0.1, QtGui.QColor(255, 255, 255, 0))
        linearGrad.setColorAt(0.7, QtGui.QColor(255, 255, 255, 0))
        linearGrad.setColorAt(1.0, QtGui.QColor(0, 0, 0, 50))
        qp.fillPath(path, self.color)
        qp.fillPath(path, linearGrad)
        qp.fillPath(
            path, QtGui.QBrush(QtGui.QColor(0, 0, 0, 50), QtCore.Qt.BDiagPattern)
        )

        # Shadow
        qp.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 130), 5))
        qp.drawLine(QtCore.QLine(12, self.height(), self.width() - 12, self.height()))

        # End
        qp.end()
        QtWidgets.QWidget.paintEvent(self, event)

    def clear(self):
        """
        Clear all contents of this widget.
        """
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

    def represent_node(self):
        """
        Add the needed child widgets to properly represent all the
        internal information in the node.
        """
        self.row_count = 0

        name_label = QtWidgets.QLabel(self.logic_node.full_name)
        name_label.setFont(QtGui.QFont("arial", 14))
        self.grid_layout.addWidget(name_label, self.row_count, 0, 1, 3)
        close_btn = QtWidgets.QToolButton()
        close_btn.setIcon(QtGui.QIcon("icons:close.svg"))
        close_btn.setToolTip("Close this node panel")
        close_btn.clicked.connect(self.deleteLater)
        self.grid_layout.addWidget(close_btn, self.row_count, 2, 1, 1)
        self.row_count += 1

        # IN attributes
        in_attrs = self.logic_node.get_input_attrs()
        if in_attrs:
            in_l = QtWidgets.QLabel("Inputs")
            in_l.setAlignment(QtCore.Qt.AlignVCenter)
            self.grid_layout.addWidget(in_l, self.row_count, 0, 1, 3)
            self.row_count += 1

        for attr in in_attrs:
            self.represent_attribute(attr)

        # OUT attributes
        out_attrs = self.logic_node.get_output_attrs()
        if out_attrs:
            line = QtWidgets.QFrame()
            line.setFrameShape(QtWidgets.QFrame.HLine)
            self.grid_layout.addWidget(line, self.row_count, 0, 1, 3)
            self.row_count += 1

            out_l = QtWidgets.QLabel("Ouputs")
            out_l.setAlignment(QtCore.Qt.AlignVCenter)
            self.grid_layout.addWidget(out_l, self.row_count, 0, 1, 3)
            self.row_count += 1

        for attr in out_attrs:
            self.represent_attribute(attr)

        # LOGS
        fail_log = self.logic_node.fail_log
        error_log = self.logic_node.error_log

        if error_log or fail_log:
            line = QtWidgets.QFrame()
            line.setFrameShape(QtWidgets.QFrame.HLine)
            self.grid_layout.addWidget(line, self.row_count, 0, 1, 3)
            self.row_count += 1

        if fail_log:
            fail_label = QtWidgets.QTextEdit()
            fail_label.setReadOnly(True)
            fail_label.setText("<b>Fail log:</b><br>" + "<br>".join(fail_log))
            fail_label.setStyleSheet(
                "color:orange; background-color:rgba(0,0,0,50); border: 1px solid rgba(200,200,200,50); border-radius:5px;"
            )
            self.grid_layout.addWidget(fail_label, self.row_count, 0, 1, 3)
            self.row_count += 1

        if error_log:
            error_label = QtWidgets.QTextEdit()
            error_label.setReadOnly(True)
            error_label.setText("<b>Error log:</b><br>" + "<br>".join(error_log))
            error_label.setStyleSheet(
                "color:red; background-color:rgba(0,0,0,50); border: 1px solid rgba(200,200,200,50); border-radius:5px;"
            )
            self.grid_layout.addWidget(error_label, self.row_count, 0, 1, 3)
            self.row_count += 1

        # Execution time
        exec_time = QtWidgets.QLabel(
            f"Execution time: {self.logic_node.execution_time:.4f} s."
        )
        self.grid_layout.addWidget(exec_time, self.row_count, 0, 1, 3)
        self.row_count += 1

        # Spacer
        verticalSpacer = QtWidgets.QSpacerItem(
            20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.grid_layout.addItem(verticalSpacer, self.row_count, 0, 1, 3)

    def represent_attribute(self, attr):
        """
        Add one of the node's attributes to the widget.

        It will consist of different parts: a name label, an input text line...

        Args:
            attr (GeneralLogicAttribute): attr to be represented

        """
        attr_name = attr.attribute_name
        data_type = attr.data_type
        name_l = QtWidgets.QLabel("{} ({})".format(attr_name, attr.get_datatype_str()))
        name_l.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.grid_layout.addWidget(name_l, self.row_count, 0, 1, 1)

        value = attr.value
        attrib_value_le = QtWidgets.QLineEdit()
        attrib_value_le.setPlaceholderText("None")

        if value is not None:
            attrib_value_le.setText(str(value))

        regex = QtCore.QRegExp(".*")
        if data_type is str and value == "":
            attrib_value_le.setText("''")
        elif data_type is float:
            regex = QtCore.QRegExp("\d+\.\d+")
        elif data_type is int:
            regex = QtCore.QRegExp("\d+")
        elif data_type is dict:
            regex = QtCore.QRegExp("\{.+")
        elif data_type is bool:
            regex = QtCore.QRegExp("[01]")
            if value is not None:
                attrib_value_le.setText(str(int(value)))

        validator = QtGui.QRegExpValidator(regex)
        attrib_value_le.setValidator(validator)
        attrib_value_le.setToolTip("Valid input: {}".format(regex.pattern()))

        connector_type = attr.connector_type
        conns = attr.get_connections_list()
        if (
            connector_type == constants.OUTPUT
            or attr_name
            in [
                constants.START,
                constants.COMPLETED,
            ]
            or conns
        ):
            attrib_value_le.setToolTip("Does not accept manual input")
            attrib_value_le.setReadOnly(True)
            if conns:
                attrib_value_le.setToolTip("Is connected, does not accept manual input")
            attrib_value_le.setStyleSheet("border: 1px solid white")
        else:
            attrib_value_le.setStyleSheet(
                "QLineEdit{color:cyan;} QLineEdit:!focus{border: 1px solid white}\
                                            QLineEdit:focus{border: 1px dashed white}"
            )
            attrib_value_le.editingFinished.connect(
                lambda: self.logic_node.set_attribute_from_str(
                    attr_name, attrib_value_le.text()
                )
            )

        self.grid_layout.addWidget(attrib_value_le, self.row_count, 1, 1, 1)

        if attr.get_datatype_str() not in [
            "Run",
            "RunLoop",
        ]:
            copy_btn = QtWidgets.QToolButton()
            copy_btn.setIcon(QtGui.QIcon("icons:clipboard.svg"))
            copy_btn.setToolTip("Copy this value to clipboard")
            copy_btn.clicked.connect(
                lambda: QtWidgets.QApplication.clipboard().setText(
                    attrib_value_le.text()
                )
            )
            self.grid_layout.addWidget(copy_btn, self.row_count, 2, 1, 1)

        self.row_count += 1

        if conns:
            for conn in conns:
                conn_l = QtWidgets.QLabel("└─")
                conn_l.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                self.grid_layout.addWidget(conn_l, self.row_count, 0, 1, 1)
                attrib_conns = QtWidgets.QLabel()
                if connector_type == constants.OUTPUT:
                    attrib_conns.setText(conn[1])
                else:
                    attrib_conns.setText(conn[0])
                self.grid_layout.addWidget(attrib_conns, self.row_count, 1, 1, 1)
                self.row_count += 1


class AttributeEditor(QtWidgets.QScrollArea):
    def __init__(self):
        QtWidgets.QScrollArea.__init__(self)
        self.layout = QtWidgets.QVBoxLayout()
        self.widget = QtWidgets.QWidget()
        self.widget.setLayout(self.layout)
        self.setWidgetResizable(True)
        self.setWidget(self.widget)
        self.layout.addItem(
            QtWidgets.QSpacerItem(
                20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
            ),
        )

        self.setMinimumWidth(360)

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def add_node_panel(self, logic_node: GeneralLogicNode):
        """
        Add a logic node to the attribute editor.

        Args:
            logic_node (GeneralLogicNode): logic node to be represented
        """
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if w:
                if w.logic_node == logic_node:
                    self.layout.takeAt(i)
                    self.layout.insertWidget(0, w)
                    self.verticalScrollBar().setValue(0)
                    return

        self.layout.insertWidget(0, NodePanel(logic_node))

    def refresh_node_panel(self, logic_node: GeneralLogicNode):
        """
        Refresh the representation/widget of a logic node in attribute editor.

        Args:
            logic_node (GeneralLogicNode): logic node to be refreshed
        """
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if w:
                if w.logic_node == logic_node:
                    w.clear()
                    w.represent_node()
                    return

    def remove_node_panel(self, logic_node: GeneralLogicNode):
        """
        Remove the representation/widget of a logic node in attribute editor.

        Args:
            logic_node (GeneralLogicNode): logic node to be removed
        """
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if w:
                if w.logic_node == logic_node:
                    w.deleteLater()
                    return

    def refresh(self):
        """
        Perform an overall refresh of all representations of nodes.
        """
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if w:
                w.clear()
                w.represent_node()

    def clear_all(self):
        """
        Remove all representations of nodes.
        """
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if w:
                w.deleteLater()
