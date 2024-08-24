# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import logging
from functools import partial
import math
import pprint

from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtSvg

from all_nodes import constants
from all_nodes import utils
from all_nodes.graphic.widgets.global_signaler import GlobalSignaler


GS = GlobalSignaler()

LOGGER = utils.get_logger(__name__)


# -------------------------------- NODE CLASS -------------------------------- #
class GeneralGraphicNode(QtWidgets.QGraphicsPathItem):
    def __init__(self, logic_node, color_name):
        # LOGIC NODE
        self.logic_node = logic_node

        # SHAPE
        self.extra_header = 0
        self.extra_bottom = 0
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
        if "svg" in self.logic_node.ICON_PATH:
            self.class_icon_renderer = QtSvg.QSvgRenderer(self.logic_node.ICON_PATH)
            self.class_icon = QtSvg.QGraphicsSvgItem(parentItem=self)
            self.class_icon.setSharedRenderer(self.class_icon_renderer)
            self.class_icon.setScale(
                constants.STRIPE_HEIGHT / self.class_icon.boundingRect().height()
            )
        else:
            class_pixmap = QtGui.QPixmap(self.logic_node.ICON_PATH)
            class_pixmap = class_pixmap.scaledToWidth(
                constants.STRIPE_HEIGHT,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            self.class_icon = QtWidgets.QGraphicsPixmapItem(class_pixmap, parent=self)

        self.class_text = QtWidgets.QGraphicsTextItem(parent=self)

        self.proxy_help_btn = QtWidgets.QGraphicsProxyWidget(parent=self)

        self.stripes = []

        self.selection_marquee = QtWidgets.QGraphicsPathItem(parent=self)
        self.selection_marquee.hide()

        self.deactivated_cross = QtWidgets.QGraphicsPathItem(parent=self)
        self.deactivated_cross.hide()

        self.error_marquee = QtWidgets.QGraphicsPathItem(parent=self)
        self.error_marquee.setFlag(QtWidgets.QGraphicsItem.ItemStacksBehindParent)
        self.error_marquee.hide()

        self.additional_info_text = QtWidgets.QGraphicsTextItem(parent=self)

        self.glow = QtWidgets.QGraphicsPathItem(parent=self)
        self.glow.hide()

        self.badge_renderer = QtSvg.QSvgRenderer("icons:badges.svg")
        self.badge_icon = QtSvg.QGraphicsSvgItem(parentItem=self)
        self.badge_icon.setSharedRenderer(self.badge_renderer)
        self.badge_icon.setElementId("neutral")
        self.badge_icon.hide()

        self.extras_renderer = QtSvg.QSvgRenderer("icons:ctx.svg")

        # ATTRIBUTES
        self.graphic_attributes = []

        # DIRECT INPUT WIDGETS AND PREVIEWS
        self.input_widgets = []
        self.proxy_input_widgets = []

        self.preview_widgets = []
        self.proxy_preview_widgets = []

        self.widget_registry = []

        # SETUP
        self.setup_node()
        self.setup_graphic_attributes()
        self.setup_input_widgets()
        self.setup_preview_widgets()
        self.setup_extras()

        self.make_shape()
        self.place_graphic_attributes()
        self.place_widgets()

        self.update_attributes_from_widgets()

        # Connect
        self.logic_node.signaler.is_executing.connect(self.show_executing)
        self.logic_node.signaler.status_changed.connect(self.show_result)
        self.logic_node.signaler.finished.connect(self.show_result)

    # PROPERTIES ----------------------
    @property
    def node_height(self):
        total_h = (
            constants.HEADER_HEIGHT
            + self.extra_header
            + (self.logic_node.get_max_in_or_out_count()) * constants.STRIPE_HEIGHT
            + self.extra_bottom
        )
        total_h += constants.STRIPE_HEIGHT

        return total_h

    @property
    def has_gui_inputs(self):
        if self.logic_node.get_gui_internals_inputs():
            return True

        return False

    @property
    def has_gui_previews(self):
        if self.logic_node.get_gui_internals_previews():
            return True

        return False

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

        # Calculate max
        self.node_width = max(
            2.5 * constants.CHAMFER_RADIUS
            + self.class_text.boundingRect().width()
            + self.proxy_help_btn.boundingRect().width()
            + 20,
            longest_in_name + longest_out_name + 2 * constants.CHAMFER_RADIUS + 20,
        )

        if self.has_gui_inputs:
            self.node_width = max(
                self.node_width,
                max(
                    w.width() + 2 * constants.CHAMFER_RADIUS for w in self.input_widgets
                ),
            )

        if self.has_gui_previews:
            self.node_width = max(
                self.node_width,
                max(
                    w.width() + 2 * constants.CHAMFER_RADIUS
                    for w in self.preview_widgets
                ),
            )

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

    def setup_graphic_attributes(self):
        """
        Create graphic attributes of this node
        """
        i = 0
        for attr in self.logic_node.get_input_attrs():
            attr = GeneralGraphicAttribute(attr, self, i)
            attr.setZValue(100)  # TODO maybe put all the setZValue together?
            self.graphic_attributes.append(attr)
            i += 1

        i = 0
        for attr in self.logic_node.get_output_attrs():
            attr = GeneralGraphicAttribute(attr, self, i)
            attr.setZValue(100)
            self.graphic_attributes.append(attr)
            i += 1

    def add_single_graphic_attribute(
        self,
        attribute_name,
        connector_type,
        data_type,
        gui_type=None,
        is_optional=False,
        value=None,
    ):
        # Check if it can be added
        new_logic_attr = self.logic_node.add_attribute(
            attribute_name, connector_type, data_type, gui_type, is_optional, value
        )
        if not new_logic_attr:
            GS.signals.main_screen_feedback.emit(
                "Cannot create attribute, name '{}' already exists in the node".format(
                    attribute_name
                ),
                logging.ERROR,
            )
            return

        # Create graphic attribute
        if connector_type in [constants.INPUT, constants.OUTPUT]:
            max_row = len(
                [
                    attribute
                    for attribute in self.graphic_attributes
                    if attribute.connector_type == connector_type
                ]
            )
            attr = GeneralGraphicAttribute(new_logic_attr, self, max_row)
            attr.setZValue(100)  # TODO maybe put all the setZValue together?
            self.graphic_attributes.append(attr)

        elif connector_type == constants.INTERNAL:
            self.setup_input_widgets()
            self.setup_preview_widgets()

        self.make_shape()
        self.place_graphic_attributes()
        self.place_widgets()

        # Feedback
        GS.signals.main_screen_feedback.emit(
            "Added new attribute '{}' to the node".format(attribute_name), logging.INFO
        )

    def make_shape(self):
        """
        Setup the shape and size of the node and its subcomponents.
        """
        # ESTABLISH WIDTH OF THE NODE
        self.guess_width_to_use()

        # BASIC SHAPE
        self.setZValue(20)
        self.setPen(
            QtGui.QPen(
                QtGui.QColor(self.bright_color_name), constants.NODE_CONTOUR_THICKNESS
            )
        )
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
        for stripe in self.stripes:
            stripe.setParentItem(None)
            del stripe
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
                stripe.setBrush(QtGui.QColor(255, 255, 255, 25))
            stripe.setZValue(10)
            self.stripes.append(stripe)

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

        # DEACTIVATED CROSS
        x_path = QtGui.QPainterPath()
        x_path.lineTo(
            QtCore.QPoint(
                self.node_width,
                self.node_height,
            ),
        )
        x_path.moveTo(
            QtCore.QPoint(0, self.node_height),
        )
        x_path.lineTo(
            QtCore.QPoint(
                self.node_width,
                0,
            ),
        )
        self.deactivated_cross.setPath(x_path)
        self.deactivated_cross.setPen(constants.NODE_DEACTIVATED_PEN)
        self.deactivated_cross.setZValue(300)

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

    def place_widgets(self):
        """
        Place the input and preview widgets in their correct position.
        """
        if self.has_gui_inputs:
            for i in range(len(self.input_widgets)):
                self.input_widgets[i].setFixedSize(
                    max(
                        self.node_width - 2 * constants.CHAMFER_RADIUS,
                        self.input_widgets[i].width(),
                    ),
                    self.input_widgets[i].height(),
                )

                self.proxy_input_widgets.append(
                    QtWidgets.QGraphicsProxyWidget(parent=self)
                )
                self.proxy_input_widgets[i].setWidget(self.input_widgets[i])
                self.proxy_input_widgets[i].setPos(
                    constants.CHAMFER_RADIUS, constants.HEADER_HEIGHT
                )
                self.proxy_input_widgets[i].setZValue(
                    200
                )  # TODO maybe put all the setZValue together?
                if i:
                    in_widget = self.proxy_input_widgets[i - 1].widget()
                    self.proxy_input_widgets[i].setPos(
                        constants.CHAMFER_RADIUS,
                        in_widget.pos().y() + in_widget.height(),
                    )

        if self.has_gui_previews:
            for i in range(len(self.preview_widgets)):
                self.preview_widgets[i].setFixedSize(
                    max(
                        self.node_width - 2 * constants.CHAMFER_RADIUS,
                        self.preview_widgets[i].width(),
                    ),
                    self.preview_widgets[i].height(),
                )

                self.proxy_preview_widgets.append(
                    QtWidgets.QGraphicsProxyWidget(parent=self)
                )
                self.proxy_preview_widgets[i].setWidget(self.preview_widgets[i])
                self.proxy_preview_widgets[i].setPos(
                    constants.CHAMFER_RADIUS,
                    constants.HEADER_HEIGHT
                    + self.extra_header
                    + (self.logic_node.get_max_in_or_out_count())
                    * constants.STRIPE_HEIGHT
                    + constants.CHAMFER_RADIUS,
                )
                if i:
                    prev_widget = self.proxy_preview_widgets[i - 1].widget()
                    self.proxy_preview_widgets[i].setPos(
                        constants.CHAMFER_RADIUS,
                        prev_widget.pos().y() + prev_widget.height(),
                    )

    def setup_input_widgets(self):
        """
        For special nodes that take input, setup widgets to receive the input
        """
        if not self.has_gui_inputs:
            return

        # Set type of widget depending on the type of input neede
        gui_internals_inputs = self.logic_node.get_gui_internals_inputs()

        for attr_name in gui_internals_inputs:
            # Check if a widget was already created
            if attr_name in self.widget_registry:
                continue
            else:
                self.widget_registry.append(attr_name)

            # Setup a widget for this attr
            gui_input_type = gui_internals_inputs.get(attr_name).get("gui_type")

            if gui_input_type == constants.InputsGUI.STR_INPUT:
                new_input_widget = QtWidgets.QLineEdit(parent=None)
                new_input_widget.setObjectName(attr_name)
                new_input_widget.setToolTip(f"Internal attribute: {attr_name}")
                new_input_widget.setFixedSize(
                    150,
                    int(constants.HEADER_HEIGHT),
                )
                new_input_widget.setStyleSheet(
                    "background:transparent; color:white; border:1px solid white;"
                )
                new_input_widget.setPlaceholderText("str here")
                if self.logic_node.get_attribute_value(attr_name):
                    new_input_widget.setText(
                        self.logic_node.get_attribute_value(attr_name)
                    )
                new_input_widget.textChanged.connect(
                    partial(
                        self.update_attributes_from_widgets,
                        attr_name,
                    )
                )
                self.input_widgets.append(new_input_widget)

            elif gui_input_type == constants.InputsGUI.MULTILINE_STR_INPUT:
                new_input_widget = QtWidgets.QPlainTextEdit(parent=None)
                new_input_widget.setObjectName(attr_name)
                new_input_widget.setToolTip(f"Internal attribute: {attr_name}")
                new_input_widget.setFixedSize(
                    300,
                    int(4 * constants.HEADER_HEIGHT),
                )
                new_input_widget.setStyleSheet(
                    "background:transparent; color:white; border:1px solid white;"
                )
                new_input_widget.setPlaceholderText("Text here")
                if self.logic_node.get_attribute_value(attr_name):
                    new_input_widget.setPlainText(
                        self.logic_node.get_attribute_value(attr_name)
                    )
                new_input_widget.textChanged.connect(
                    partial(
                        self.update_attributes_from_widgets,
                        attr_name,
                    )
                )
                self.input_widgets.append(new_input_widget)

            elif gui_input_type == constants.InputsGUI.DICT_INPUT:
                new_input_widget = QtWidgets.QPlainTextEdit(parent=None)
                new_input_widget.setObjectName(attr_name)
                new_input_widget.setToolTip(f"Internal attribute: {attr_name}")
                new_input_widget.setFixedSize(
                    300,
                    int(4 * constants.HEADER_HEIGHT),
                )
                new_input_widget.setStyleSheet(
                    "background:transparent; color:white; border:1px solid white;"
                )
                new_input_widget.setPlaceholderText("Text here")
                if self.logic_node.get_attribute_value(attr_name):
                    new_input_widget.setText(
                        self.logic_node.get_attribute_value(attr_name)
                    )
                new_input_widget.textChanged.connect(
                    partial(
                        self.update_attributes_from_widgets,
                        attr_name,
                    )
                )
                self.input_widgets.append(new_input_widget)

            elif gui_input_type == constants.InputsGUI.LIST_INPUT:
                new_input_widget = QtWidgets.QLineEdit(parent=None)
                new_input_widget.setObjectName(attr_name)
                new_input_widget.setToolTip(f"Internal attribute: {attr_name}")
                new_input_widget.setFixedSize(
                    150,
                    int(constants.HEADER_HEIGHT),
                )
                new_input_widget.setStyleSheet(
                    "background:transparent; color:white; border:1px solid white;"
                )
                new_input_widget.setPlaceholderText("list here")
                if self.logic_node.get_attribute_value(attr_name):
                    new_input_widget.setText(
                        str(self.logic_node.get_attribute_value(attr_name))
                    )
                new_input_widget.textChanged.connect(
                    partial(
                        self.update_attributes_from_widgets,
                        attr_name,
                    )
                )
                self.input_widgets.append(new_input_widget)

            elif gui_input_type == constants.InputsGUI.BOOL_INPUT:
                new_input_widget = QtWidgets.QCheckBox("False", parent=None)
                new_input_widget.setObjectName(attr_name)
                new_input_widget.setToolTip(f"Internal attribute: {attr_name}")
                new_input_widget.setFixedSize(150, int(constants.HEADER_HEIGHT))
                new_input_widget.setStyleSheet(
                    "QCheckBox::indicator{border : 1px solid white;}"
                    "QCheckBox::indicator:checked{ background:rgba(255,255,200,150); }"
                    "QCheckBox{ background:transparent; color:white}"
                )
                if self.logic_node.get_attribute_value(attr_name):
                    new_input_widget.setChecked(
                        self.logic_node.get_attribute_value(attr_name)
                    )
                new_input_widget.stateChanged.connect(
                    lambda: new_input_widget.setText(
                        ["False", "True"][new_input_widget.isChecked()]
                    )
                )
                new_input_widget.clicked.connect(
                    partial(self.update_attributes_from_widgets, attr_name)
                )
                self.input_widgets.append(new_input_widget)

            elif gui_input_type == constants.InputsGUI.INT_INPUT:
                new_input_widget = QtWidgets.QSpinBox(parent=None)
                new_input_widget.setObjectName(attr_name)
                new_input_widget.setToolTip(f"Internal attribute: {attr_name}")
                new_input_widget.setFixedSize(
                    150,
                    int(constants.HEADER_HEIGHT),
                )
                new_input_widget.setStyleSheet(
                    "background:transparent; color:white; border:1px solid white;"
                )
                new_input_widget.setMaximum(int(1e6))
                new_input_widget.setMinimum(int(-1e6))
                if self.logic_node.get_attribute_value(attr_name):
                    new_input_widget.setValue(
                        self.logic_node.get_attribute_value(attr_name)
                    )
                new_input_widget.valueChanged.connect(
                    partial(self.update_attributes_from_widgets, attr_name)
                )
                self.input_widgets.append(new_input_widget)

            elif gui_input_type == constants.InputsGUI.FLOAT_INPUT:
                new_input_widget = QtWidgets.QDoubleSpinBox(parent=None)
                new_input_widget.setObjectName(attr_name)
                new_input_widget.setToolTip(f"Internal attribute: {attr_name}")
                new_input_widget.setFixedSize(
                    150,
                    int(constants.HEADER_HEIGHT),
                )
                new_input_widget.setStyleSheet(
                    "background:transparent; color:white; border:1px solid white;"
                )
                new_input_widget.setMaximum(int(1e6))
                new_input_widget.setMinimum(int(-1e6))
                if self.logic_node.get_attribute_value(attr_name):
                    new_input_widget.setValue(
                        self.logic_node.get_attribute_value(attr_name)
                    )
                new_input_widget.valueChanged.connect(
                    partial(self.update_attributes_from_widgets, attr_name)
                )
                self.input_widgets.append(new_input_widget)

            elif gui_input_type == constants.InputsGUI.OPTION_INPUT:
                new_input_widget = QtWidgets.QComboBox(parent=None)
                new_input_widget.setObjectName(attr_name)
                new_input_widget.setToolTip(f"Internal attribute: {attr_name}")
                new_input_widget.setFixedSize(
                    150,
                    int(constants.HEADER_HEIGHT),
                )
                new_input_widget.adjustSize()
                new_input_widget.setFixedSize(
                    new_input_widget.width() + 20, new_input_widget.height()
                )
                new_input_widget.setStyleSheet(
                    "QComboBox { background:transparent; color:white; border:1px solid white; }"
                    "QWidget:item { color: black; background:white; }"
                )
                new_input_widget.addItems(
                    gui_internals_inputs.get(attr_name).get(
                        "options", constants.InputsGUI.OPTION_INPUT.value
                    )
                )
                if self.logic_node.get_attribute_value(attr_name):
                    new_input_widget.setCurrentText(
                        self.logic_node.get_attribute_value(attr_name)
                    )
                new_input_widget.currentIndexChanged.connect(
                    partial(self.update_attributes_from_widgets, attr_name)
                )
                self.input_widgets.append(new_input_widget)

            elif gui_input_type == constants.InputsGUI.TUPLE_INPUT:
                new_input_widget = QtWidgets.QLineEdit(parent=None)
                new_input_widget.setObjectName(attr_name)
                new_input_widget.setToolTip(f"Internal attribute: {attr_name}")
                new_input_widget.setFixedSize(
                    150,
                    int(constants.HEADER_HEIGHT),
                )
                new_input_widget.setStyleSheet(
                    "background:transparent; color:white; border:1px solid white;"
                )
                new_input_widget.setPlaceholderText("tuple here")
                if self.logic_node.get_attribute_value(attr_name):
                    new_input_widget.setText(
                        self.logic_node.get_attribute_value(attr_name)
                    )
                new_input_widget.textChanged.connect(
                    partial(
                        self.update_attributes_from_widgets,
                        attr_name,
                    )
                )
                self.input_widgets.append(new_input_widget)

        # Set font of the widgets
        for w in self.input_widgets:
            w.setFont(QtGui.QFont(constants.NODE_FONT, constants.HEADER_HEIGHT * 0.4))

        # Measure
        self.extra_header = sum([w.height() for w in self.input_widgets]) + 5

    def setup_preview_widgets(self):
        """
        For special nodes that can display previews, setup widgets
        """
        if not self.has_gui_previews:
            return

        # Separator label
        if not self.widget_registry:
            previews_label = QtWidgets.QLabel(parent=None)
            previews_label.setFixedSize(
                150,
                int(constants.STRIPE_HEIGHT),
            )
            previews_label.setStyleSheet(
                "background:transparent; color:white; border:none;"
            )
            previews_label.setText("- PREVIEWS -")
            self.preview_widgets.append(previews_label)

        # Set type of widget depending on the type of preview needed
        gui_internals_previews = self.logic_node.get_gui_internals_previews()

        for attr_name in gui_internals_previews:
            # Check if a widget was already created
            if attr_name in self.widget_registry:
                continue
            else:
                self.widget_registry.append(attr_name)

            # Create widget for attribute
            gui_preview_type = gui_internals_previews.get(attr_name).get("gui_type")

            if gui_preview_type == constants.PreviewsGUI.STR_PREVIEW:
                new_preview_widget = QtWidgets.QLineEdit(parent=None)
                new_preview_widget.setObjectName(attr_name)
                new_preview_widget.setToolTip(f"Internal attribute: {attr_name}")
                new_preview_widget.setReadOnly(True)
                new_preview_widget.setFixedSize(
                    150,
                    int(constants.STRIPE_HEIGHT),
                )
                new_preview_widget.setStyleSheet(
                    "background:transparent; color:white; border:1px dotted white;"
                )

                if self.logic_node.get_attribute_value(attr_name):
                    new_preview_widget.setText(
                        self.logic_node.get_attribute_value(attr_name)
                    )
                else:
                    new_preview_widget.setText(f"[{attr_name}]")

                self.preview_widgets.append(new_preview_widget)

            elif gui_preview_type == constants.PreviewsGUI.MULTILINE_STR_PREVIEW:
                new_preview_widget = QtWidgets.QPlainTextEdit(parent=None)
                new_preview_widget.setObjectName(attr_name)
                new_preview_widget.setToolTip(f"Internal attribute: {attr_name}")
                new_preview_widget.setReadOnly(True)
                new_preview_widget.setFixedSize(
                    300,
                    int(4 * constants.HEADER_HEIGHT),
                )
                new_preview_widget.setStyleSheet(
                    "background:transparent; color:white; border:1px dotted white;"
                )

                if self.logic_node.get_attribute_value(attr_name):
                    new_preview_widget.setPlaceholderText(
                        self.logic_node.get_attribute_value(attr_name)
                    )
                else:
                    new_preview_widget.setPlaceholderText(f"[{attr_name}]")

                self.preview_widgets.append(new_preview_widget)

            elif gui_preview_type == constants.PreviewsGUI.DICT_PREVIEW:
                new_preview_widget = QtWidgets.QPlainTextEdit(parent=None)
                new_preview_widget.setObjectName(attr_name)
                new_preview_widget.setToolTip(f"Internal attribute: {attr_name}")
                new_preview_widget.setReadOnly(True)
                new_preview_widget.setFixedSize(
                    300,
                    int(4 * constants.HEADER_HEIGHT),
                )
                new_preview_widget.setStyleSheet(
                    "background:transparent; color:white; border:1px dotted white;"
                )

                if self.logic_node.get_attribute_value(attr_name):
                    new_preview_widget.setPlaceholderText(
                        self.logic_node.get_attribute_value(attr_name)
                    )
                else:
                    new_preview_widget.setPlaceholderText(f"[{attr_name}]")

                self.preview_widgets.append(new_preview_widget)

            elif gui_preview_type == constants.PreviewsGUI.IMAGE_PREVIEW:
                new_preview_widget = QtWidgets.QLabel(parent=None)
                new_preview_widget.setObjectName(attr_name)
                new_preview_widget.setToolTip(f"Internal attribute: {attr_name}")
                new_preview_widget.setFixedSize(
                    constants.STRIPE_HEIGHT * 10,
                    constants.STRIPE_HEIGHT * 10,
                )
                new_preview_widget.setAlignment(
                    QtCore.Qt.AlignVCenter and QtCore.Qt.AlignCenter
                )
                new_preview_widget.setStyleSheet(
                    "background:transparent; color:white; border:none;"
                )
                if self.logic_node.get_attribute_value(attr_name):
                    pass  # TODO
                else:
                    new_preview_widget.setText(f"[{attr_name}]")

                self.preview_widgets.append(new_preview_widget)

        # Measure
        self.extra_bottom = sum([w.height() for w in self.preview_widgets])

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
        self.update_attributes_from_widgets()
        self.clear_previews()

    def show_executing(self):
        """
        Display visual indications around the node to show it is running.
        """
        self.badge_icon.show()

        self.badge_icon.setElementId("executing")
        self.badge_icon.setToolTip('<p style="color: magenta">Executing...<br>')

        self.error_marquee.hide()

    def show_result(self):
        """
        Display visual indications around the node to show the result of its execution.
        """
        self.badge_icon.show()

        if self.logic_node.success == constants.NOT_RUN:
            self.badge_icon.hide()
            self.error_marquee.hide()

        elif self.logic_node.success == constants.IN_LOOP:
            self.badge_icon.setElementId("loop")
            self.badge_icon.setToolTip('<p style="color: cyan">In loop<br>')

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

        # Previews
        if self.logic_node.success == constants.SUCCESSFUL:
            self.update_previews_from_attributes()

    # CHANGE ATTRIBUTES FROM INPUT WIDGETS ----------------------
    def update_attributes_from_widgets(self, *args):
        gui_internal_attr_name = args[0] if args else None
        for w in self.input_widgets:
            if (
                w.objectName() == gui_internal_attr_name
                or gui_internal_attr_name is None
            ):
                value = None

                if isinstance(w, QtWidgets.QLineEdit):
                    value = w.text() or None
                    if value is None:
                        self.logic_node[w.objectName()].clear()
                        continue
                    self.logic_node.set_attribute_from_str(w.objectName(), value)
                elif isinstance(w, QtWidgets.QPlainTextEdit):
                    value = w.toPlainText() or None
                    if value is None:
                        self.logic_node[w.objectName()].clear()
                        continue
                    self.logic_node.set_attribute_from_str(w.objectName(), value)
                elif isinstance(w, QtWidgets.QCheckBox):
                    value = w.isChecked()
                    self.logic_node[w.objectName()].set_value(value)
                elif isinstance(w, QtWidgets.QSpinBox):
                    value = w.value()
                    self.logic_node[w.objectName()].set_value(value)
                elif isinstance(w, QtWidgets.QDoubleSpinBox):
                    value = w.value()
                    self.logic_node[w.objectName()].set_value(value)
                elif isinstance(w, QtWidgets.QComboBox):
                    value = w.currentText()
                    self.logic_node[w.objectName()].set_value(value)

        if self.scene():
            GS.signals.attribute_editor_refresh_node_requested.emit(
                self.logic_node.uuid
            )

    # SHOW PREVIEWS ----------------------
    def update_previews_from_attributes(self):
        for w in self.preview_widgets:
            if not w.objectName():  # That is the label that starts the previews
                continue

            value = self.logic_node.get_attribute_value(w.objectName())

            if isinstance(w, QtWidgets.QLineEdit):
                w.setText(value)
            elif isinstance(w, QtWidgets.QPlainTextEdit):
                w.setPlainText(pprint.pformat(value))
            elif isinstance(w, QtWidgets.QCheckBox):
                w.setChecked(value)
            elif isinstance(w, QtWidgets.QSpinBox):
                w.setValue(value)
            elif isinstance(w, QtWidgets.QDoubleSpinBox):
                w.setValue(value)
            elif isinstance(w, QtWidgets.QComboBox):
                w.setCurrentText(value)
            elif isinstance(w, QtWidgets.QLabel):
                im2 = value.convert("RGB")
                data = im2.tobytes("raw", "RGB")
                image = QtGui.QImage(
                    data, im2.width, im2.height, QtGui.QImage.Format_RGB888
                )
                pix = QtGui.QPixmap.fromImage(image)
                w.setPixmap(
                    pix.scaled(w.width(), w.height(), QtCore.Qt.KeepAspectRatio)
                )

        if self.scene():
            GS.signals.attribute_editor_refresh_node_requested.emit(
                self.logic_node.uuid
            )

    def clear_previews(self):
        for w in self.preview_widgets:
            if not w.objectName():
                continue

            self.logic_node[w.objectName()].clear()

            if isinstance(w, QtWidgets.QLineEdit):
                w.setText(f"[{w.objectName()}]")
            elif isinstance(w, QtWidgets.QPlainTextEdit):
                w.setPlainText(f"[{w.objectName()}]")
            elif isinstance(w, QtWidgets.QCheckBox):
                w.setChecked(False)
            elif isinstance(w, QtWidgets.QSpinBox):
                w.setValue(0)
            elif isinstance(w, QtWidgets.QDoubleSpinBox):
                w.setValue(0.0)
            elif isinstance(w, QtWidgets.QComboBox):
                w.setCurrentIndex(0)
            elif isinstance(w, QtWidgets.QLabel):
                w.clear()
                w.setText(f"[{w.objectName()}]")

        if self.scene():
            GS.signals.attribute_editor_refresh_node_requested.emit(
                self.logic_node.uuid
            )

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

    def toggle_activated(self):
        """Toggle the activated state of the node."""
        active = self.logic_node.toggle_activated()
        self.deactivated_cross.setVisible(not active)

    def show_deactivated(self):
        """Force to show deactivated."""
        self.deactivated_cross.setVisible(True)

    # UTILITY ----------------------
    def update_name(self):
        """
        Update the text shown in the node's name.
        """
        self.class_text.setHtml(
            '<p align="left"><font color=white>{0}'.format(self.logic_node.node_name)
        )

    def get_as_code(self):
        format_dict = {
            "inputs_dict": self.logic_node.INPUTS_DICT,
            "outputs_dict": self.logic_node.OUTPUTS_DICT,
            "internals_dict": self.logic_node.INTERNALS_DICT,
            "class_name": self.logic_node.node_name,
            "is_context": self.logic_node.IS_CONTEXT,
        }

        template_file = QtCore.QFile(r"resources:class_template.txt")
        with open(template_file.fileName(), "r") as template:
            template_text = template.read()
            return template_text.format(**format_dict)

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

        elif self.logic_attribute.get_datatype_str() == "int":
            plug_polygon = QtGui.QPolygon(
                [
                    QtCore.QPoint(-constants.PLUG_RADIUS, -constants.PLUG_RADIUS),
                    QtCore.QPoint(constants.PLUG_RADIUS, -constants.PLUG_RADIUS),
                    QtCore.QPoint(constants.PLUG_RADIUS, constants.PLUG_RADIUS),
                    QtCore.QPoint(-constants.PLUG_RADIUS, constants.PLUG_RADIUS),
                ]
            )
            plug_path.addPolygon(plug_polygon)

        elif self.logic_attribute.get_datatype_str() == "float":
            plug_polygon = QtGui.QPolygon(
                [
                    QtCore.QPoint(-constants.PLUG_RADIUS, -constants.PLUG_RADIUS),
                    QtCore.QPoint(0.6 * constants.PLUG_RADIUS, -constants.PLUG_RADIUS),
                    QtCore.QPoint(constants.PLUG_RADIUS, -0.25 * constants.PLUG_RADIUS),
                    QtCore.QPoint(constants.PLUG_RADIUS, 0.25 * constants.PLUG_RADIUS),
                    QtCore.QPoint(0.6 * constants.PLUG_RADIUS, constants.PLUG_RADIUS),
                    QtCore.QPoint(-constants.PLUG_RADIUS, constants.PLUG_RADIUS),
                ]
            )
            plug_path.addPolygon(plug_polygon)

        elif self.logic_attribute.get_datatype_str() in ["Run", "RunLoop"]:
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
        self.setPos(
            0,
            constants.HEADER_HEIGHT
            + self.parent_node.extra_header
            + self.row_index * constants.STRIPE_HEIGHT,
        )

        if self.logic_attribute.connector_type == constants.INPUT:
            self.plug_polygon.setPos(
                -constants.PLUG_RADIUS * 1.3,
                constants.STRIPE_HEIGHT / 2,
            )
            self.glow.setPos(
                -constants.PLUG_RADIUS * 1.3,
                constants.STRIPE_HEIGHT / 2,
            )
        elif self.logic_attribute.connector_type == constants.OUTPUT:
            self.attr_text.setPos(
                self.parent_node.node_width - self.attr_text.boundingRect().width(), 0
            )
            self.plug_polygon.setPos(
                self.parent_node.node_width + constants.PLUG_RADIUS * 1.3,
                constants.STRIPE_HEIGHT / 2,
            )
            self.glow.setPos(
                self.parent_node.node_width + constants.PLUG_RADIUS * 1.3,
                constants.STRIPE_HEIGHT / 2,
            )

    # CONNECT/DISCONNECT ----------------------
    def connect_graphic_attr(self, other_graphic_attr, check_logic=True) -> tuple:
        """
        Connect this graphic attribute to another one.

        Args:
            other_graphic_attr (GeneralGraphicAttribute): attribute to try to connect
            check_logic (bool): check the connection of logic attributes

        Returns: tuple(bool, str), whether the attribute could be connected and a message with the reason
        """
        can_connect = True
        reason = ""
        if check_logic:
            can_connect, reason = self.logic_attribute.connect_to_other(
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

        return can_connect, reason

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
