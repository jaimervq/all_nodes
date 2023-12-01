# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import ast
import math

from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtSvg

from all_nodes import constants
from all_nodes import utils
from all_nodes.graphic.widgets.global_signaler import GLOBAL_SIGNALER as GS


LOGGER = utils.get_logger(__name__)


# -------------------------------- NODE CLASS -------------------------------- #
class GeneralGraphicNode(QtWidgets.QGraphicsPathItem):
    def __init__(self, logic_node, color_name):
        # LOGIC NODE
        self.logic_node = logic_node

        # SHAPE
        self.extra_header = 0
        self.node_width = 450

        # INIT
        QtWidgets.QGraphicsPathItem.__init__(self)
        self.setData(0, constants.GRAPHIC_NODE)
        self.setAcceptHoverEvents(True)
        self.setFlags(
            QtWidgets.QGraphicsPathItem.ItemIsMovable
            | QtWidgets.QGraphicsPathItem.ItemIsSelectable
            | QtWidgets.QGraphicsPathItem.ItemSendsScenePositionChanges
        )

        # COLOR
        self.base_color = QtGui.QColor(color_name)
        self.bright_color_name = utils.get_bright_color(color_name)

        # SUB-ITEMS
        class_pixmap = QtGui.QPixmap(self.logic_node.ICON_PATH)
        print(self.logic_node.ICON_PATH)
        class_pixmap = class_pixmap.scaledToHeight(
            constants.STRIPE_HEIGHT, QtCore.Qt.TransformationMode.SmoothTransformation
        )
        self.class_icon = QtWidgets.QGraphicsPixmapItem(class_pixmap, parent=self)
        self.class_text = QtWidgets.QGraphicsTextItem(parent=self)

        self.proxy_help_btn = QtWidgets.QGraphicsProxyWidget(parent=self)

        self.selection_marquee = QtWidgets.QGraphicsPathItem(parent=self)
        self.selection_marquee.hide()
        self.error_marquee = QtWidgets.QGraphicsPathItem(parent=self)
        self.error_marquee.setFlag(QtWidgets.QGraphicsItem.ItemStacksBehindParent)
        self.error_marquee.hide()
        self.glow = QtWidgets.QGraphicsPathItem(parent=self)
        self.glow.hide()

        self.additional_info_text = QtWidgets.QGraphicsTextItem(parent=self)

        self.svg_renderer = QtSvg.QSvgRenderer("icons:badges.svg")
        self.badge_icon = QtSvg.QGraphicsSvgItem(parentItem=self)
        self.badge_icon.setSharedRenderer(self.svg_renderer)
        self.badge_icon.setElementId("neutral")
        self.badge_icon.hide()

        self.extras_renderer = QtSvg.QSvgRenderer("icons:ctx.svg")

        self.proxy_input_widget = QtWidgets.QGraphicsProxyWidget(parent=self)

        # ATTRIBUTES
        self.graphic_attributes = []

        # SPECIAL / INPUT
        self.input_datatype = None
        if hasattr(self.logic_node, "INPUT_TYPE"):
            self.input_datatype = self.logic_node.INPUT_TYPE
            self.extra_header = constants.HEADER_HEIGHT
            self.setScale(0.7)

        # SETUP
        self.setup_node()
        self.add_graphic_attributes()
        self.make_shape()
        self.place_graphic_attributes()
        self.setup_widget()
        self.update_attribute_from_widget()
        self.setup_extras()

        # Connect
        self.logic_node.signaler.status_changed.connect(self.show_result)
        self.logic_node.signaler.finished.connect(self.show_result)

    # PROPERTIES ----------------------
    @property
    def node_height(self):
        total_h = (
            constants.HEADER_HEIGHT
            + self.extra_header
            + (self.logic_node.get_max_in_or_out_count()) * constants.STRIPE_HEIGHT
        )
        total_h += constants.STRIPE_HEIGHT

        return total_h

    # GRAPHICS SETUP ----------------------
    def guess_width_to_use(self):
        """
        Calculate width to draw the node with, based on the size of its graphical attributes.
        """

        # Biggest attr names
        longest_in_name = max(
            [
                attribute.attr_text.boundingRect().width()
                for attribute in self.graphic_attributes
                if attribute.connector_type == constants.INPUT
            ]
        )
        longest_out_name = max(
            [
                attribute.attr_text.boundingRect().width()
                for attribute in self.graphic_attributes
                if attribute.connector_type == constants.OUTPUT
            ]
        )

        # Size of the options in case it is a multi-choice input node
        size_options = 0
        if self.input_datatype == "option":
            size_options = 15 * (
                max([len(elem) for elem in self.logic_node.INPUT_OPTIONS])
            )

        # Calculate max
        self.node_width = max(
            2.5 * constants.CHAMFER_RADIUS
            + self.class_text.boundingRect().width()
            + self.proxy_help_btn.boundingRect().width()
            + 20,
            longest_in_name + longest_out_name,
            2 * constants.CHAMFER_RADIUS + size_options,
        )
        return False

    def setup_node(self):
        """
        Setup some of the subcomponents of the node.
        """
        # NODE ICON
        self.class_icon.moveBy(
            constants.CHAMFER_RADIUS / 2.0, constants.CHAMFER_RADIUS / 2.0
        )

        # NODE NAME
        self.class_text.setHtml(
            '<p align="left"><font color=white>{0}'.format(self.logic_node.node_name)
        )
        node_class_font = QtGui.QFont(
            constants.NODE_FONT, int(0.4 * constants.HEADER_HEIGHT)
        )
        self.class_text.setFont(node_class_font)
        self.class_text.moveBy(2.5 * constants.CHAMFER_RADIUS, 0)

        # HELP
        help_btn = QtWidgets.QPushButton(parent=None)
        help_btn.setStyleSheet(
            "QPushButton:hover{color:yellow; background-color:rgba(255,255,0,50)}"
            "QPushButton{color:white; border-radius:3px; border:1px solid white; background:transparent;}"
        )
        help_btn.setFixedSize(
            int(0.4 * constants.HEADER_HEIGHT), int(0.4 * constants.HEADER_HEIGHT)
        )
        help_btn.setText("?")
        help_btn.setFont(
            QtGui.QFont(constants.NODE_FONT, int(0.45 * help_btn.height()))
        )
        help_btn.clicked.connect(self.show_help)
        self.proxy_help_btn = QtWidgets.QGraphicsProxyWidget(parent=self)
        self.proxy_help_btn.setWidget(help_btn)

        # ADDITIONAL INFO
        node_id_font = QtGui.QFont(
            constants.NODE_FONT, int(0.5 * constants.STRIPE_HEIGHT)
        )
        self.additional_info_text.setFont(node_id_font)
        self.additional_info_text.hide()

    def add_graphic_attributes(self):
        """
        Create graphic attributes of this node
        """
        i = 0
        for attr in self.logic_node.get_input_attrs():
            attr = GeneralGraphicAttribute(attr, self, i)
            attr.setZValue(100)
            self.graphic_attributes.append(attr)
            i += 1

        i = 0
        for attr in self.logic_node.get_output_attrs():
            attr = GeneralGraphicAttribute(attr, self, i)
            attr.setZValue(100)
            self.graphic_attributes.append(attr)
            i += 1

    def make_shape(self):
        """
        Setup the shape and size of the node and its subcomponents.
        """
        # BASIC SHAPE
        self.setZValue(20)
        self.setPen(
            QtGui.QPen(
                QtGui.QColor(self.bright_color_name), constants.NODE_CONTOUR_THICKNESS
            )
        )
        self.guess_width_to_use()
        new_path = QtGui.QPainterPath()
        new_path.addRoundedRect(
            QtCore.QRect(0, 0, self.node_width, self.node_height),
            constants.CHAMFER_RADIUS,
            constants.CHAMFER_RADIUS,
        )
        self.setPath(new_path)

        # FILLING
        grad = QtGui.QLinearGradient(0, 0, 0, self.node_height)
        grad.setColorAt(0.5, self.base_color)
        lighter_color = QtGui.QColor(
            self.base_color.red() + 50,
            self.base_color.green() + 50,
            self.base_color.blue() + 50,
        )
        grad.setColorAt(1.0, lighter_color)
        self.setBrush(grad)

        # STRIPES
        stripe_path = QtGui.QPainterPath()
        stripe_path.addRect(
            QtCore.QRect(0, 0, self.node_width, constants.STRIPE_HEIGHT)
        )
        for row_count in range(self.logic_node.get_max_in_or_out_count()):
            stripe = QtWidgets.QGraphicsPathItem(parent=self)
            stripe.setPath(stripe_path)
            stripe.setPen(QtGui.QPen(QtCore.Qt.NoPen))
            stripe.moveBy(
                0,
                constants.HEADER_HEIGHT
                + self.extra_header
                + row_count * constants.STRIPE_HEIGHT,
            )
            if row_count % 2 == 0:
                stripe.setBrush(QtGui.QColor(255, 255, 255, 20))
            stripe.setZValue(10)

        # BUTTON MOVEMENT
        self.proxy_help_btn.setPos(
            self.node_width
            - self.proxy_help_btn.widget().width()
            - constants.CHAMFER_RADIUS / 2,
            constants.CHAMFER_RADIUS / 2,
        )

        # GLOW
        glow_pen = QtGui.QPen(
            QtGui.QColor(self.bright_color_name), constants.NODE_SELECTED_GLOW_THICKNESS
        )
        self.glow.setPen(glow_pen)
        self.glow.setPath(new_path)
        blur = QtWidgets.QGraphicsBlurEffect()
        blur.setBlurRadius(glow_pen.width() * 2)
        self.glow.setGraphicsEffect(blur)
        self.glow.setZValue(40)

        # SELECTION MARQUEE
        self.selection_marquee.setPath(new_path)
        self.selection_marquee.setPen(constants.NODE_SELECTED_PEN)
        self.selection_marquee.setZValue(50)

        # ERROR MARQUEE
        error_path = QtGui.QPainterPath()
        error_path.addRoundedRect(
            QtCore.QRect(
                0,
                0,
                self.node_width + constants.PLUG_RADIUS * 6,
                self.node_height + constants.PLUG_RADIUS * 6,
            ),
            constants.CHAMFER_RADIUS * 2,
            constants.CHAMFER_RADIUS * 2,
        )
        self.error_marquee.setPath(error_path)
        self.error_marquee.moveBy(
            -constants.PLUG_RADIUS * 3, -constants.PLUG_RADIUS * 3
        )

        # BADGES
        self.badge_icon.setZValue(80)
        self.badge_icon.setPos(
            self.node_width
            - self.badge_icon.boundingRect().width()
            - constants.CHAMFER_RADIUS,
            self.node_height - constants.STRIPE_HEIGHT / 2,
        )

        # EXTRA TEXT
        self.additional_info_text.setTextWidth(self.node_width * 1.4)
        self.additional_info_text.moveBy(
            -constants.CHAMFER_RADIUS,
            self.node_height + constants.PLUG_RADIUS * 3,
        )

    def place_graphic_attributes(self):
        """
        Place the graphic attributes in their correct position.
        """
        for attr in self.graphic_attributes:
            attr.setup_graphics()

    def setup_widget(self):
        """
        For special nodes that take input, setup a widget to receive the input
        """
        if not self.input_datatype:
            return

        # Default widget
        input_widget = QtWidgets.QLineEdit(parent=None)

        # Set type of widget depending on the type of input needed
        if self.input_datatype == "str":
            input_widget.setStyleSheet(
                "background:transparent; color:white; border:1px solid white;"
            )
            input_widget.setPlaceholderText("str here")

            if self.logic_node.get_attribute_value("out_str"):
                input_widget.setText(self.logic_node.get_attribute_value("out_str"))

            input_widget.textChanged.connect(self.update_attribute_from_widget)

        elif self.input_datatype == "dict":
            input_widget.setStyleSheet(
                "background:transparent; color:white; border:1px solid white;"
            )
            input_widget.setPlaceholderText("Paste dict here")

            if self.logic_node.get_attribute_value("out_dict"):
                input_widget.setText(self.logic_node.get_attribute_value("out_dict"))

            input_widget.textChanged.connect(self.update_attribute_from_widget)

        elif self.input_datatype == "list":
            input_widget.setStyleSheet(
                "background:transparent; color:white; border:1px solid white;"
            )
            input_widget.setPlaceholderText("Paste list here")

            if self.logic_node.get_attribute_value("out_list"):
                input_widget.setText(self.logic_node.get_attribute_value("out_list"))

            input_widget.textChanged.connect(self.update_attribute_from_widget)

        elif self.input_datatype == "bool":
            input_widget = QtWidgets.QCheckBox("False", parent=None)
            input_widget.setStyleSheet(
                "QCheckBox::indicator{border : 1px solid white;}"
                "QCheckBox::indicator:checked{ background:rgba(255,255,200,150); }"
                "QCheckBox{ background:transparent; color:white}"
            )
            input_widget.stateChanged.connect(
                lambda: input_widget.setText(
                    ["False", "True"][input_widget.isChecked()]
                )
            )
            if self.logic_node.get_attribute_value("out_bool"):
                input_widget.setChecked(self.logic_node.get_attribute_value("out_bool"))

            input_widget.stateChanged.connect(self.update_attribute_from_widget)

        elif self.input_datatype == "int":
            input_widget = QtWidgets.QSpinBox(parent=None)
            input_widget.setMaximum(int(1e6))
            input_widget.setMinimum(int(-1e6))
            input_widget.setStyleSheet(
                "background:transparent; color:white; border:1px solid white;"
            )

            if self.logic_node.get_attribute_value("out_int"):
                input_widget.setValue(self.logic_node.get_attribute_value("out_int"))

            input_widget.valueChanged.connect(self.update_attribute_from_widget)

        elif self.input_datatype == "float":
            input_widget = QtWidgets.QDoubleSpinBox(parent=None)
            input_widget.setMaximum(1e6)
            input_widget.setMinimum(-1e6)
            input_widget.setStyleSheet(
                "background:transparent; color:white; border:1px solid white;"
            )

            if self.logic_node.get_attribute_value("out_float"):
                input_widget.setValue(self.logic_node.get_attribute_value("out_float"))

            input_widget.valueChanged.connect(self.update_attribute_from_widget)

        elif self.input_datatype == "option":
            input_widget = QtWidgets.QComboBox(parent=None)
            input_widget.setStyleSheet(
                "QComboBox { background:transparent; color:white; border:1px solid white; }"
                "QWidget:item { color: black; background:white; }"
            )
            input_widget.addItems(self.logic_node.INPUT_OPTIONS)

            if self.logic_node.get_attribute_value("out_str"):
                input_widget.setCurrentText(
                    self.logic_node.get_attribute_value("out_str")
                )

            input_widget.currentIndexChanged.connect(self.update_attribute_from_widget)

        # Set size of the widget
        input_widget.setFixedSize(
            int(self.node_width - 2 * constants.CHAMFER_RADIUS),
            int(0.8 * constants.HEADER_HEIGHT),
        )
        input_widget.setFont(
            QtGui.QFont(constants.NODE_FONT, int(0.5 * input_widget.height()))
        )

        # Then add it to the graphics proxy widget
        self.proxy_input_widget.setWidget(input_widget)
        self.proxy_input_widget.moveBy(
            constants.CHAMFER_RADIUS, constants.HEADER_HEIGHT
        )

    def setup_extras(self):
        """
        Setup the extra labels/icons on the node.

        Mainly oriented to context nodes or context-related nodes.
        """
        if self.logic_node.IS_CONTEXT:
            ctx_icon = QtSvg.QGraphicsSvgItem(parentItem=self)
            ctx_icon.setSharedRenderer(self.extras_renderer)
            ctx_icon.setPos(0, -25)
            ctx_icon.setElementId("context")
        elif "InputFromCtx" in self.logic_node.class_name:
            ctx_icon = QtSvg.QGraphicsSvgItem(parentItem=self)
            ctx_icon.setSharedRenderer(self.extras_renderer)
            ctx_icon.setPos(0, -25)
            ctx_icon.setElementId("in")
        elif "OutputToCtx" in self.logic_node.class_name:
            ctx_icon = QtSvg.QGraphicsSvgItem(parentItem=self)
            ctx_icon.setSharedRenderer(self.extras_renderer)
            ctx_icon.setPos(0, -25)
            ctx_icon.setElementId("out")

    # EXECUTION ----------------------
    def reset(self):
        """
        Reset the appearance of the node, so it shows no execution feedback (badges, marquees...).
        """
        LOGGER.info("Resetting graphic node {}".format(self.logic_node.node_name))
        self.badge_icon.hide()
        self.error_marquee.hide()
        self.additional_info_text.hide()
        self.update_attribute_from_widget()

    def show_result(self):
        """
        Display visual indications around the node to show the result of its execution.
        """
        self.badge_icon.show()

        if self.logic_node.success == constants.NOT_RUN:
            self.badge_icon.hide()
            self.error_marquee.hide()

        elif self.logic_node.success == constants.EXECUTING:
            self.badge_icon.setElementId("executing")
            self.badge_icon.setToolTip('<p style="color: gray">Executing...<br>')

            self.error_marquee.hide()

        elif self.logic_node.success == constants.SKIPPED:
            self.badge_icon.setElementId("neutral")
            self.badge_icon.setToolTip('<p style="color: gray">Skipped<br>')

            self.error_marquee.hide()

        elif self.logic_node.success == constants.SUCCESSFUL:
            self.badge_icon.setElementId("okay")
            self.badge_icon.setToolTip(
                '<p style="color: lime">SUCCESS!<br>Exec: {:.4f}s'.format(
                    self.logic_node.execution_time
                )
            )
            self.error_marquee.hide()

        elif self.logic_node.success in [constants.FAILED, constants.ERROR]:
            self.error_marquee.show()

            if self.logic_node.success == constants.FAILED:
                self.badge_icon.setElementId("failed")
                self.error_marquee.setPen(constants.NODE_FAILED_PEN)
                self.error_marquee.setBrush(constants.NODE_FAILED_BRUSH)

            elif self.logic_node.success == constants.ERROR:
                self.badge_icon.setElementId("error")
                self.error_marquee.setPen(constants.NODE_ERROR_PEN)
                self.error_marquee.setBrush(constants.NODE_ERROR_BRUSH)

            # Full feedback
            html_text = ""
            if self.logic_node.fail_log:
                html_text += '<p style="color: orange">FAILED:<br>' + "<br>".join(
                    self.logic_node.fail_log
                )
            if self.logic_node.error_log:
                html_text += '<p style="color: red">ERROR:<br>' + "<br>".join(
                    self.logic_node.error_log
                )

            self.badge_icon.setToolTip(html_text)
            if constants.IN_SCREEN_ERRORS:
                self.additional_info_text.setHtml(html_text)
                self.additional_info_text.show()

    # CHANGE ATTRIBUTES ----------------------
    def update_attribute_from_widget(self):
        if self.input_datatype == "str":
            text = self.proxy_input_widget.widget().text()
            if text:
                self.logic_node.set_special_attr_value("out_str", text)
        elif self.input_datatype == "dict":
            text = self.proxy_input_widget.widget().text()
            if text:
                try:
                    eval_dict = ast.literal_eval(text)
                    if eval_dict and isinstance(eval_dict, dict):
                        self.logic_node.set_special_attr_value("out_dict", eval_dict)
                except (ValueError, SyntaxError):
                    pass
        elif self.input_datatype == "list":
            text = self.proxy_input_widget.widget().text()
            if text:
                try:
                    eval_list = ast.literal_eval(text)
                    if eval_list and isinstance(eval_list, list):
                        self.logic_node.set_special_attr_value("out_list", eval_list)
                except (ValueError, SyntaxError):
                    pass
        elif self.input_datatype == "tuple":
            text = self.proxy_input_widget.widget().text()
            if text:
                try:
                    eval_tuple = ast.literal_eval(text)
                    if eval_tuple and isinstance(eval_tuple, tuple):
                        self.logic_node.set_special_attr_value("out_tuple", eval_list)
                except (ValueError, SyntaxError):
                    pass
        elif self.input_datatype == "bool":
            checked = self.proxy_input_widget.widget().isChecked()
            self.logic_node.set_special_attr_value("out_bool", checked)
        elif self.input_datatype == "int":
            val = self.proxy_input_widget.widget().value()
            self.logic_node.set_special_attr_value("out_int", val)
        elif self.input_datatype == "float":
            val = self.proxy_input_widget.widget().value()
            self.logic_node.set_special_attr_value("out_float", val)
            self.logic_node.set_special_attr_value("out_int", int(val))
        elif self.input_datatype == "option":
            val = self.proxy_input_widget.widget().currentText()
            self.logic_node.set_special_attr_value("out_str", val)

        if self.scene():
            GS.attribute_editor_refresh_node_requested.emit(self.logic_node.uuid)

    # ITEM CHANGE EVENT ----------------------
    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.set_selected_appearance()
        elif change in [
            QtWidgets.QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged
        ]:
            self.redraw_lines()

        return QtWidgets.QGraphicsItem.itemChange(self, change, value)

    # CONNECTIONS/LINES ----------------------
    def redraw_lines(self):
        self.scene().redraw_node_lines(self)

    def clear_all_connections(self):
        for g_a in self.graphic_attributes:
            g_a.clear_connections()

    # VISUAL FEEDBACK ----------------------
    def set_selected_appearance(self):
        self.setZValue(10)

        if self.isSelected():
            self.selection_marquee.show()
            if constants.GLOW_EFFECTS:
                self.glow.show()
        else:
            self.glow.hide()
            self.selection_marquee.hide()

    def show_help(self):
        """
        Show a window with the help/usage of this node class.
        """
        help_text = self.logic_node.get_node_html_help()
        info_window = QtWidgets.QMessageBox()
        info_window.setText(help_text)
        info_window.setWindowTitle("Help")
        info_window.setIcon(QtWidgets.QMessageBox.Information)

        f = QtCore.QFile(r"ui:stylesheet.qss")
        with open(f.fileName(), "r") as s:
            info_window.setStyleSheet(s.read())

        info_window.exec_()

    # UTILITY ----------------------
    def update_name(self):
        """
        Update the text shown in the node's name.
        """
        self.class_text.setHtml(
            '<p align="left"><font color=white>{0}'.format(self.logic_node.node_name)
        )

    # SPECIAL METHODS ----------------------
    def __str__(self):
        return "Grapic node " + self.logic_node.node_name

    def __getitem__(self, item: str):
        for g_attr in self.graphic_attributes:
            if g_attr.logic_attribute.attribute_name == item:
                return g_attr
        LOGGER.error("Error, no graphic attribute with that name {}".format(item))


# -------------------------------- Graphic Attribute -------------------------------- #
class GeneralGraphicAttribute(QtWidgets.QGraphicsPathItem):
    def __init__(self, logic_attribute, parent_node, row_index):
        # BASIC PROPERTIES
        self.logic_attribute = logic_attribute
        self.connector_type = self.logic_attribute.connector_type
        self.row_index = row_index

        self.connected_graphic_attrs = set()

        # GRAPHIC SETUP
        QtWidgets.QGraphicsPathItem.__init__(self, parent=parent_node)
        self.setData(0, constants.GRAPHIC_ATTRIBUTE)

        self.parent_node = parent_node

        self.plug_polygon = QtWidgets.QGraphicsPathItem(parent=self)

        self.attr_text = QtWidgets.QGraphicsTextItem(parent=self)
        attr_text_font = QtGui.QFont(
            constants.NODE_FONT, int(0.4 * constants.STRIPE_HEIGHT)
        )
        self.attr_text.setFont(attr_text_font)
        self.attr_text.setHtml(
            "<font color=white>↦ {0} <font color=cyan>({1})".format(
                logic_attribute.attribute_name,
                logic_attribute.get_datatype_str(),
            )
        )
        if logic_attribute.is_optional:
            self.attr_text.setHtml(
                "<font color=#60ffffff>∗ {0} <font color=#6000FFFF>({1})".format(
                    logic_attribute.attribute_name,
                    logic_attribute.get_datatype_str(),
                )
            )
        if self.logic_attribute.connector_type == constants.OUTPUT:
            self.attr_text.setHtml(
                "<font color=cyan>({0}) <font color=white> {1} ↦".format(
                    self.logic_attribute.get_datatype_str(),
                    self.logic_attribute.attribute_name,
                )
            )
            if logic_attribute.is_optional:
                self.attr_text.setHtml(
                    "<font color=#6000FFFF>({0}) <font color=#60ffffff> {1} ∗".format(
                        logic_attribute.get_datatype_str(),
                        logic_attribute.attribute_name,
                    )
                )

        self.glow = QtWidgets.QGraphicsPathItem(parent=self)
        self.glow.hide()

    # PROPERTIES ----------------------
    @property
    def x(self):
        return self.scenePos().x()

    @property
    def center_point(self):
        return self.scenePos()

    # GEOMETRY PROPERTIES ----------------------
    def plug_coords(self):
        return self.plug_polygon.scenePos()

    # GRAPHICS SETUP ----------------------
    def setup_graphics(self):
        self.setPen(QtGui.QPen(QtCore.Qt.NoPen))

        # Plug shape (will be different shape depending on data type)
        plug_path = QtGui.QPainterPath()

        if self.logic_attribute.get_datatype_str() == "bool":
            plug_polygon = QtGui.QPolygon(
                [
                    QtCore.QPoint(-constants.PLUG_RADIUS, -constants.PLUG_RADIUS),
                    QtCore.QPoint(0, -constants.PLUG_RADIUS * 0.5),
                    QtCore.QPoint(constants.PLUG_RADIUS, -constants.PLUG_RADIUS),
                    QtCore.QPoint(constants.PLUG_RADIUS, constants.PLUG_RADIUS),
                    QtCore.QPoint(0, constants.PLUG_RADIUS * 0.5),
                    QtCore.QPoint(-constants.PLUG_RADIUS, constants.PLUG_RADIUS),
                ]
            )
            plug_path.addPolygon(plug_polygon)

        elif self.logic_attribute.get_datatype_str() == "list":
            plug_polygon = QtGui.QPolygon(
                [
                    QtCore.QPoint(-constants.PLUG_RADIUS, -constants.PLUG_RADIUS * 0.7),
                    QtCore.QPoint(-constants.PLUG_RADIUS, constants.PLUG_RADIUS * 0.7),
                    QtCore.QPoint(constants.PLUG_RADIUS, constants.PLUG_RADIUS * 0.7),
                    QtCore.QPoint(+constants.PLUG_RADIUS, -constants.PLUG_RADIUS * 0.7),
                ]
            )
            plug_path.addPolygon(plug_polygon)

        elif self.logic_attribute.get_datatype_str() == "dict":
            plug_polygon = QtGui.QPolygon(
                [
                    QtCore.QPoint(-constants.PLUG_RADIUS, 0),
                    QtCore.QPoint(0, constants.PLUG_RADIUS),
                    QtCore.QPoint(constants.PLUG_RADIUS, 0),
                    QtCore.QPoint(0, -constants.PLUG_RADIUS),
                ]
            )
            plug_path.addPolygon(plug_polygon)

        elif self.logic_attribute.get_datatype_str() == "str":
            plug_path.addEllipse(
                QtCore.QPoint(0, 0), constants.PLUG_RADIUS, constants.PLUG_RADIUS
            )

        elif self.logic_attribute.get_datatype_str() == "tuple":
            plug_polygon = QtGui.QPolygon(
                [
                    QtCore.QPoint(
                        -constants.PLUG_RADIUS * 0.8, constants.PLUG_RADIUS * 0.8
                    ),
                    QtCore.QPoint(
                        -constants.PLUG_RADIUS * 0.8, -constants.PLUG_RADIUS * 0.8
                    ),
                    QtCore.QPoint(
                        constants.PLUG_RADIUS * 0.8, constants.PLUG_RADIUS * 0.8
                    ),
                    QtCore.QPoint(
                        +constants.PLUG_RADIUS * 0.8, -constants.PLUG_RADIUS * 0.8
                    ),
                ]
            )
            plug_path.addPolygon(plug_polygon)

        elif self.logic_attribute.get_datatype_str() in ("int", "float"):
            plug_polygon = QtGui.QPolygon(
                [
                    QtCore.QPoint(-constants.PLUG_RADIUS, -constants.PLUG_RADIUS),
                    QtCore.QPoint(constants.PLUG_RADIUS, -constants.PLUG_RADIUS),
                    QtCore.QPoint(constants.PLUG_RADIUS, constants.PLUG_RADIUS),
                    QtCore.QPoint(-constants.PLUG_RADIUS, constants.PLUG_RADIUS),
                ]
            )
            plug_path.addPolygon(plug_polygon)

        elif self.logic_attribute.get_datatype_str() == "Run":
            plug_polygon = QtGui.QPolygon(
                [
                    QtCore.QPoint(-constants.PLUG_RADIUS, constants.PLUG_RADIUS),
                    QtCore.QPoint(constants.PLUG_RADIUS, 0),
                    QtCore.QPoint(-constants.PLUG_RADIUS, -constants.PLUG_RADIUS),
                ]
            )
            plug_path.addPolygon(plug_polygon)

        else:
            plug_polygon = QtGui.QPolygon()
            w = 360 / 5
            for i in range(5):
                t = w * i - 90
                x = constants.PLUG_RADIUS * math.cos(math.radians(t))
                y = constants.PLUG_RADIUS * math.sin(math.radians(t))
                plug_polygon.append(QtCore.QPoint(x, y))
            plug_path.addPolygon(plug_polygon)

        plug_path.closeSubpath()
        self.plug_polygon.setPath(plug_path)
        self.plug_polygon.setPen(
            QtGui.QPen(
                QtGui.QColor(self.parent_node.bright_color_name),
                constants.NODE_CONTOUR_THICKNESS * 0.5,
            )
        )
        self.plug_polygon.setBrush(
            QtGui.QBrush(
                QtGui.QColor(
                    self.parent_node.base_color.red() + 35,
                    self.parent_node.base_color.green() + 35,
                    self.parent_node.base_color.blue() + 35,
                )
            )
        )
        self.plug_polygon.setZValue(50)

        self.plug_polygon.setData(0, constants.PLUG)
        # self.plug_polygon.setData(1, self)

        # Glow
        self.glow.setPath(plug_path)
        glow_pen = QtGui.QPen(
            QtGui.QColor(self.parent_node.bright_color_name),
            constants.NODE_SELECTED_GLOW_THICKNESS,
        )
        self.glow.setPen(glow_pen)
        blur = QtWidgets.QGraphicsBlurEffect()
        blur.setBlurRadius(glow_pen.width() * 1.5)
        self.glow.setGraphicsEffect(blur)
        self.glow.setZValue(40)

        # Move elements
        self.moveBy(
            0,
            constants.HEADER_HEIGHT
            + self.parent_node.extra_header
            + self.row_index * constants.STRIPE_HEIGHT,
        )

        if self.logic_attribute.connector_type == constants.INPUT:
            self.plug_polygon.moveBy(
                -constants.PLUG_RADIUS * 1.3,
                constants.STRIPE_HEIGHT / 2,
            )
            self.glow.moveBy(
                -constants.PLUG_RADIUS * 1.3,
                constants.STRIPE_HEIGHT / 2,
            )
        elif self.logic_attribute.connector_type == constants.OUTPUT:
            self.attr_text.moveBy(
                self.parent_node.node_width - self.attr_text.boundingRect().width(), 0
            )
            self.plug_polygon.moveBy(
                self.parent_node.node_width + constants.PLUG_RADIUS * 1.3,
                constants.STRIPE_HEIGHT / 2,
            )
            self.glow.moveBy(
                self.parent_node.node_width + constants.PLUG_RADIUS * 1.3,
                constants.STRIPE_HEIGHT / 2,
            )

    # CONNECT/DISCONNECT ----------------------
    def connect_graphic_attr(self, other_graphic_attr, check_logic=True):
        """
        Connect this graphic attribute to another one.

        Args:
            other_graphic_attr (GeneralGraphicAttribute): attribute to try to connect
            check_logic (bool): check the connection of logic attributes

        Returns: bool, whether the attribute could be connected
        """
        can_connect = True
        if check_logic:
            can_connect = self.logic_attribute.connect_to_other(
                other_graphic_attr.logic_attribute
            )
        if can_connect:
            if self.connector_type == constants.INPUT:
                self.connected_graphic_attrs = {other_graphic_attr}
                other_graphic_attr.connected_graphic_attrs.add(self)
            else:
                self.connected_graphic_attrs.add(other_graphic_attr)
                other_graphic_attr.connected_graphic_attrs = {self}

        self.show_connected_status()
        other_graphic_attr.show_connected_status()

        return can_connect

    def clear_connections(self):
        connected_g_attrs = list(self.connected_graphic_attrs)
        for connected_g_attr in connected_g_attrs:
            self.disconnect_from(connected_g_attr)

    def disconnect_from(self, other_graphic_attr):
        self.logic_attribute.disconnect_from_other(other_graphic_attr.logic_attribute)

        self.connected_graphic_attrs.remove(other_graphic_attr)
        other_graphic_attr.connected_graphic_attrs.remove(self)

        self.show_connected_status()
        other_graphic_attr.show_connected_status()

    def disconnect_input(self):
        if self.connector_type == constants.INPUT and self.connected_graphic_attrs:
            self.logic_attribute.disconnect_input()

            connected_out_graphic_attr = next(iter(self.connected_graphic_attrs))

            self.connected_graphic_attrs.remove(connected_out_graphic_attr)
            connected_out_graphic_attr.connected_graphic_attrs.remove(self)

            self.show_connected_status()
            connected_out_graphic_attr.show_connected_status()

    # UTILITY ----------------------
    def has_input_connected(self):
        return self.logic_attribute.has_input_connected()

    # VISUAL FEEDBACK ----------------------
    def show_connected_status(self):
        if self.connected_graphic_attrs:
            if constants.GLOW_EFFECTS:
                self.glow.show()
            self.plug_polygon.setPen(constants.CONNECTOR_USED_PEN)
        else:
            self.glow.hide()
            self.plug_polygon.setPen(
                QtGui.QPen(
                    QtGui.QColor(self.parent_node.bright_color_name),
                    constants.NODE_CONTOUR_THICKNESS * 0.5,
                )
            )

    # SPECIAL METHODS ----------------------
    def __str__(self):
        return self.logic_attribute.node_name
