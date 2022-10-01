# -*- coding: UTF-8 -*-
"""
Author: Jaime Rivera
Date: November 2022
Copyright: MIT License

           Copyright (c) 2022 Jaime Rivera

           Permission is hereby granted, free of charge, to any person obtaining a copy
           of this software and associated documentation files (the "Software"), to deal
           in the Software without restriction, including without limitation the rights
           to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
           copies of the Software, and to permit persons to whom the Software is
           furnished to do so, subject to the following conditions:

           The above copyright notice and this permission notice shall be included in all
           copies or substantial portions of the Software.

           THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
           IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
           FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
           AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
           LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
           OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
           SOFTWARE.

Brief:
"""

__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import logging
import os
import pprint
import subprocess

from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui
import yaml

from all_nodes import constants
from all_nodes.graphic.graphic_node import GeneralGraphicNode, GeneralGraphicAttribute
from all_nodes.logic import ALL_CLASSES
from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes.logic.logic_scene import LogicScene
from all_nodes import utils
from all_nodes.graphic.widgets.global_signaler import GLOBAL_SIGNALER as GS


LOGGER = utils.get_logger(__name__)


# -------------------------------- CUSTOM GRAPHICS VIEW -------------------------------- #


class CustomGraphicsView(QtWidgets.QGraphicsView):
    def __init__(self):
        QtWidgets.QGraphicsView.__init__(self)
        self.setRenderHints(QtGui.QPainter.Antialiasing)
        self.setAcceptDrops(True)

        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.NoAnchor)

        self.middle_pressed = False

        self.feedback_line = QtWidgets.QLineEdit(parent=self)
        self.feedback_line.setReadOnly(True)
        self.feedback_line.setFont(QtGui.QFont("arial", 12))
        self.feedback_line.hide()

        self.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)

    def show_feedback(self, message, level=logging.INFO):
        """
        Display a basic piece of feedback on screen, on top of the graphics scene.

        Args:
            message (str): message to display
            level (int): level of the message

        """
        effect = QtWidgets.QGraphicsOpacityEffect(self.feedback_line)
        anim = QtCore.QPropertyAnimation(effect, b"opacity", parent=self)
        anim.setStartValue(1)
        anim.setEndValue(0)
        anim.setDuration(5500)

        if level == logging.DEBUG:
            if not constants.IN_DEV:
                return
            self.feedback_line.setStyleSheet(
                "color:cyan; background-color:transparent; border:none"
            )
            message = "[DEBUG] " + message
        elif level == logging.INFO:
            self.feedback_line.setStyleSheet(
                "color:lime; background-color:transparent; border:none"
            )
            message = "[INFO] " + message
        elif level == logging.WARNING:
            self.feedback_line.setStyleSheet(
                "color:orange; background-color:transparent; border:none"
            )
            message = "[WARNING] " + message
        elif level == logging.ERROR:
            self.feedback_line.setStyleSheet(
                "color:red; background-color:transparent; border:none"
            )
            message = "[ERROR] " + message
            anim.setDuration(8000)

        self.feedback_line.show()
        self.feedback_line.setText(message)
        self.feedback_line.setGraphicsEffect(effect)
        anim.start()

    def resizeEvent(self, event):
        QtWidgets.QGraphicsView.resizeEvent(self, event)
        self.feedback_line.move(25, self.height() - 50)
        self.feedback_line.setFixedSize(self.width(), 30)

    def mousePressEvent(self, event):
        self.middle_pressed = False

        if event.button() == QtCore.Qt.MidButton:
            self._dragPos = event.pos()
            self.middle_pressed = True

        QtWidgets.QGraphicsView.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        new_pos = event.pos()

        if self.middle_pressed:
            disp = new_pos - self._dragPos
            self._dragPos = new_pos
            self.translate(disp.x(), disp.y())

        QtWidgets.QGraphicsView.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MidButton:
            self.middle_pressed = False

        QtWidgets.QGraphicsView.mouseReleaseEvent(self, event)

    def wheelEvent(self, event):
        zoom_increase = 1.45
        zoom_decrease = 0.65

        old_pos = self.mapToScene(event.pos())

        if event.delta() > 0:
            self.scale(zoom_increase, zoom_increase)
        else:
            self.scale(zoom_decrease, zoom_decrease)

        new_pos = self.mapToScene(event.pos())
        disp = new_pos - old_pos
        self.translate(disp.x(), disp.y())

    def dragEnterEvent(self, event):
        QtWidgets.QGraphicsView.dragEnterEvent(self, event)
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        QtWidgets.QGraphicsView.dragMoveEvent(self, event)
        event.acceptProposedAction()


# -------------------------------- CUSTOM SCENE CLASS -------------------------------- #
class CustomScene(QtWidgets.QGraphicsScene):

    dropped_node = QtCore.Signal(int, int)
    in_screen_feedback = QtCore.Signal(str, int)

    def __init__(self):
        QtWidgets.QGraphicsScene.__init__(self)

        # Logic scene
        self.logic_scene = LogicScene()

        # Nodes
        self.all_nodes = set()

        # PATH TESTS
        self.testing_graphic_attr = None

        self.testing_path_glow = QtWidgets.QGraphicsPathItem()
        self.testing_path_glow.setPen(constants.LINE_GLOW_PEN)
        blur = QtWidgets.QGraphicsBlurEffect()
        blur.setBlurRadius(constants.LINE_GLOW_PEN.width() * 1.5)
        self.testing_path_glow.setGraphicsEffect(blur)
        self.testing_path_glow.setZValue(-1)
        self.addItem(self.testing_path_glow)

        self.testing_path = QtWidgets.QGraphicsPathItem()
        self.testing_path.setPen(constants.TEST_LINE_PEN)
        self.testing_path.setZValue(-1)
        self.addItem(self.testing_path)

    def drawBackground(self, painter, rect):
        pen = QtGui.QPen(QtGui.QColor(255, 230, 255, 150), 2)
        painter.setPen(pen)
        for i in range(-40_000, 40_000, 200):
            if i > rect.x() and i < rect.x() + rect.width():
                painter.drawLine(QtCore.QLine(i, -40_000, i, 40_000))
            if i > rect.y() and i < rect.y() + rect.height():
                painter.drawLine(QtCore.QLine(-40_000, i, 40_000, i))

    def add_graphic_node_by_name(
        self, node_classname: str, x: int = 0, y: int = 0
    ) -> GeneralGraphicNode:
        for m in sorted(ALL_CLASSES):
            color = ALL_CLASSES[m]["color"]
            for name, cls in ALL_CLASSES[m]["classes"]:
                if node_classname == name:
                    new_logic_node = self.logic_scene.add_node_by_name(node_classname)
                    new_graph_node = GeneralGraphicNode(new_logic_node, color)
                    self.addItem(new_graph_node)
                    self.all_nodes.add(new_graph_node)
                    new_graph_node.setPos(x, y)
                    self.in_screen_feedback.emit(
                        "Created graphic node {}".format(node_classname), logging.INFO
                    )
                    return new_graph_node

    def add_graphic_node_from_logic_node(self, logic_node, x: int = 0, y: int = 0):
        for m in sorted(ALL_CLASSES):
            color = ALL_CLASSES[m]["color"]
            for name, cls in ALL_CLASSES[m]["classes"]:
                if logic_node.class_name == name:
                    new_graph_node = GeneralGraphicNode(logic_node, color)
                    self.addItem(new_graph_node)
                    self.all_nodes.add(new_graph_node)
                    LOGGER.info(
                        "Created graphic node from logic node {} at x:{} y:{}".format(
                            logic_node.full_name, x, y
                        )
                    )
                    new_graph_node.moveBy(x, y)
                    return new_graph_node

    def delete_node(self, graphic_node: GeneralGraphicNode):
        """
        Delete graphic node from this scene.

        Args:
            graphic_node (GeneralGraphicNode): node to delete

        """
        self.clear_node_lines(graphic_node)
        graphic_node.clear_all_connections()
        self.all_nodes.remove(graphic_node)
        self.removeItem(graphic_node)

        self.logic_scene.remove_node_by_name(graphic_node.logic_node.full_name)

        del graphic_node

    def selected_nodes(self) -> list:
        """
        Gather all selected nodes.

        Returns: list, with all selected nodes.

        """
        sel_nodes = []
        for n in self.all_nodes:
            if n.isSelected():
                sel_nodes.append(n)
        return sel_nodes

    def clear_node_lines(self, node: GeneralGraphicNode):
        for line in self.items():
            g_1, g_2 = line.data(1), line.data(2)
            if line.data(0) == constants.CONNECTOR_LINE and node in [
                g_1.parent_node,
                g_2.parent_node,
            ]:
                self.removeItem(line)

    def redraw_node_lines(self, node: GeneralGraphicNode):
        graphic_attrs = [
            c
            for c in self.items()
            if c.data(0) == "GRAPHIC_ATTRIBUTE" and c.parent_node == node
        ]

        lines_to_redraw = set()
        for g in graphic_attrs:
            g_1, g_2 = None, None
            for line in self.items():
                g_1, g_2 = line.data(1), line.data(2)

                if line.data(0) == constants.CONNECTOR_LINE and g in [g_1, g_2]:
                    self.removeItem(line)
                    lines_to_redraw.add((g_1, g_2))

        if node in self.items():
            for g_1, g_2 in lines_to_redraw:
                self.draw_valid_line(g_1, g_2)

    def connect_graphic_attrs(
        self,
        graphic_attr_1: GeneralGraphicAttribute,
        graphic_attr_2: GeneralGraphicAttribute,
        check_logic=True,
    ):

        # Remove previously existing lines between these graphic_attrs
        for item in self.items():
            if item.data(0) == constants.CONNECTOR_LINE:
                if graphic_attr_1 in [
                    item.data(1),
                    item.data(2),
                ] and graphic_attr_2 in [
                    item.data(1),
                    item.data(2),
                ]:
                    self.removeItem(item)

        # Connect
        if graphic_attr_1.connect_graphic_attr(graphic_attr_2, check_logic):
            self.in_screen_feedback.emit(
                "Connected graphic attributes!",
                logging.DEBUG,
            )
            self.draw_valid_line(graphic_attr_1, graphic_attr_2)
        else:
            self.in_screen_feedback.emit(
                "Cannot connect those attributes",
                logging.ERROR,
            )

    def draw_valid_line(self, graphic_attr_1, graphic_attr_2):
        """
        Draw a line in between to graphic attributes that we know can be connected.

        Args:
            graphic_attr_1 (GeneralGraphicAttribute)
            graphic_attr_2 (GeneralGraphicAttribute)

        """
        p1, p2 = (
            graphic_attr_1.plug_coords(),
            graphic_attr_2.plug_coords(),
        )

        new_path = QtGui.QPainterPath(p1)
        c_p1 = QtCore.QPoint(((p2.x() + p1.x()) / 2) + 10, p1.y())
        c_p2 = QtCore.QPoint(((p2.x() + p1.x()) / 2) - 10, p2.y())
        if constants.STRAIGHT_LINES:
            new_path.lineTo(p2)
        else:
            new_path.cubicTo(c_p1, c_p2, p2)

        new_valid_line_glow = QtWidgets.QGraphicsPathItem(new_path)
        new_valid_line_glow.setPen(constants.LINE_GLOW_PEN)
        blur = QtWidgets.QGraphicsBlurEffect()
        blur.setBlurRadius(constants.LINE_GLOW_PEN.width() * 1.5)
        new_valid_line_glow.setGraphicsEffect(blur)
        new_valid_line_glow.setZValue(-1)
        new_valid_line_glow.setData(0, constants.CONNECTOR_LINE)
        new_valid_line_glow.setData(1, graphic_attr_1)
        new_valid_line_glow.setData(2, graphic_attr_2)
        if constants.GLOW_EFFECTS:
            self.addItem(new_valid_line_glow)

        new_valid_line = QtWidgets.QGraphicsPathItem(new_path)
        new_valid_line.setPen(constants.VALID_LINE_PEN)
        new_valid_line.setZValue(-1)
        new_valid_line.setData(0, constants.CONNECTOR_LINE)
        new_valid_line.setData(1, graphic_attr_1)
        new_valid_line.setData(2, graphic_attr_2)
        self.addItem(new_valid_line)

    def disconnect_graphic_attrs(
        self,
        graphic_attr_1: GeneralGraphicAttribute,
        graphic_attr_2: GeneralGraphicAttribute,
    ):
        graphic_attr_1.disconnect_from(graphic_attr_2)
        GS.attribute_editor_global_refresh_requested.emit()

    def save_to_file(self):
        """
        Save this graphics scene to a file.
        """
        # Ask for filepath
        dialog = QtWidgets.QFileDialog()
        result = dialog.getSaveFileName(caption="Specify target file", filter="*.yml")
        if not result[0] or not result[1]:
            return
        target_file = result[0]

        # Grab logic scene info and add the xy coords
        the_dict = self.logic_scene.convert_scene_to_dict()
        for g_node in self.all_nodes:
            node_name = g_node.logic_node.full_name
            for node_dict in the_dict["nodes"]:
                if node_name in node_dict:
                    node_dict[node_name]["x_pos"] = int(g_node.scenePos().x())
                    node_dict[node_name]["y_pos"] = int(g_node.scenePos().y())
                    break

        # Save logic scene
        self.logic_scene.save_to_file(target_file, the_dict)

    def load_from_file(self, source_file: str):
        """
        Create a graphic scene from a file.

        Args:
            source_file (str): filepath of scene to load

        """
        # Grab the scene dict and create logic nodes
        scene_dict = dict()
        with open(source_file, "r") as file:
            scene_dict = yaml.safe_load(file)

        new_logic_nodes = self.logic_scene.load_from_file(source_file)

        # Create graphic nodes
        for logic_node in new_logic_nodes:
            for node_dict in scene_dict["nodes"]:
                node_name = next(iter(node_dict))
                if logic_node.full_name.endswith(node_name):
                    self.add_graphic_node_from_logic_node(
                        logic_node,
                        node_dict[node_name]["x_pos"],
                        node_dict[node_name]["y_pos"],
                    )
                    break

        # Connections
        all_graphic_attrs = []
        for g_node in self.all_nodes:
            if g_node.logic_node in new_logic_nodes:
                for g_attribute in g_node.graphic_attributes:
                    all_graphic_attrs.append(g_attribute)

        for g_attribute in all_graphic_attrs:
            if g_attribute.connector_type != constants.OUTPUT:
                continue
            connected_logic_attributes = []
            for (
                connected_logic_attribute
            ) in g_attribute.logic_attribute.connected_attributes:
                connected_logic_attributes.append(connected_logic_attribute.full_name)
            for logic_attr_full_name in connected_logic_attributes:
                for other_g_attribute in all_graphic_attrs:
                    if (
                        other_g_attribute.logic_attribute.full_name
                        == logic_attr_full_name
                    ):
                        LOGGER.info(
                            "Connected graphic attributes {} -> {}".format(
                                g_attribute.logic_attribute.full_name,
                                other_g_attribute.logic_attribute.full_name,
                            )
                        )
                        self.connect_graphic_attrs(
                            g_attribute, other_g_attribute, check_logic=False
                        )
                        break

    def contextMenuEvent(self, event):
        selection_rect = QtCore.QRect(
            event.scenePos().x() - 1,
            event.scenePos().y() - 1,
            1,
            1,
        )
        test_items = self.items(selection_rect)
        for item in test_items:
            if item and item.data(0) == constants.GRAPHIC_NODE:
                menu = QtWidgets.QMenu()
                rename_action = menu.addAction("Rename this node")
                rename_action.setIcon(QtGui.QIcon("icons:rename.png"))
                rename_action.triggered.connect(lambda: self.rename_graphic_node(item))
                examine_code_action = menu.addAction("Examine code (E)")
                examine_code_action.setIcon(QtGui.QIcon("icons:examine.png"))
                examine_code_action.triggered.connect(lambda: self.examine_code(item))
                run_single_node_action = menu.addAction("Run only this node (Return ⏎)")
                run_single_node_action.setIcon(QtGui.QIcon("icons:run_one.svg"))
                run_single_node_action.triggered.connect(
                    lambda: self.run_single_node(item)
                )
                reset_single_node_action = menu.addAction("Reset only this node (R)")
                reset_single_node_action.setIcon(QtGui.QIcon("icons:reset.png"))
                reset_single_node_action.triggered.connect(
                    lambda: self.reset_single_node(item)
                )
                if constants.IN_DEV:
                    menu.addSeparator()
                    print_node_log_action = menu.addAction("Print node log")
                    print_node_log_action.setIcon(QtGui.QIcon("icons:nodes_2.png"))
                    print_node_log_action.triggered.connect(lambda: self.show_log(item))
                f = QtCore.QFile(
                    r"ui:stylesheet.qss"
                )  # TODO not ideal, maybe a reduced qss?
                with open(f.fileName(), "r") as s:
                    menu.setStyleSheet(s.read())
                menu.exec_(event.screenPos(), parent=self)
                break

        QtWidgets.QGraphicsScene.contextMenuEvent(self, event)

    def rename_graphic_node(self, graphic_node: GeneralGraphicNode):
        logic_node = graphic_node.logic_node
        new_name, ok = QtWidgets.QInputDialog().getText(
            None,
            "Rename node " + logic_node.full_name,
            "New name:",
        )
        if ok and new_name:
            if self.logic_scene.rename_node(logic_node, new_name):
                graphic_node.update_name()
                GS.attribute_editor_refresh_node_requested.emit(logic_node.uuid)
            else:
                if logic_node.full_name == new_name:
                    self.in_screen_feedback.emit(
                        "Cannot rename to '{}', it is the same name as now".format(
                            new_name
                        ),
                        logging.INFO,
                    )
                else:
                    if not GeneralLogicNode.name_is_valid(new_name):
                        self.in_screen_feedback.emit(
                            "Cannot rename to '{}', naming must start with uppercase and "
                            "cannot include special characters".format(new_name),
                            logging.WARNING,
                        )
                    else:
                        self.in_screen_feedback.emit(
                            "Cannot rename to '{}', "
                            "check that no other node has that name".format(new_name),
                            logging.WARNING,
                        )

    def examine_code(self, graphic_node: GeneralGraphicNode):
        """
        Show the code of a node in an external editor.

        Args:
            graphic_node (GeneralGraphicNode): node to examine code from

        """
        logic_node = graphic_node.logic_node
        try:
            subprocess.Popen(["notepad", logic_node.filepath])
        except Exception as e:
            msg = "Could not open the code in editor: {}".format(e)
            LOGGER.error(msg)
            self.in_screen_feedback.emit(msg, logging.ERROR)

    def show_log(self, graphic_node: GeneralGraphicNode):
        print(
            "\n{}\n{}".format(
                graphic_node.logic_node.full_name,
                "-" * len(graphic_node.logic_node.full_name),
            )
        )
        pprint.pprint(graphic_node.logic_node.get_node_full_dict())

    def run_single_node(self, graphic_node: GeneralGraphicNode):
        logic_node = graphic_node.logic_node
        self.in_screen_feedback.emit("Running only selected node(s)", logging.INFO)
        logic_node.run_single()
        graphic_node.show_result()
        GS.attribute_editor_global_refresh_requested.emit()

    def reset_single_node(self, graphic_node: GeneralGraphicNode):
        graphic_node.reset()
        graphic_node.logic_node.reset()
        self.in_screen_feedback.emit("Resetting selected node(s)", logging.INFO)
        GS.attribute_editor_global_refresh_requested.emit()

    def deselect_all(self):
        for n in self.all_nodes:
            n.setSelected(False)

    def mousePressEvent(self, event):
        QtWidgets.QGraphicsScene.mousePressEvent(self, event)

        if not event.button() == QtCore.Qt.LeftButton:
            return

        test_item = None
        selection_rect = QtCore.QRect(
            event.scenePos().x() - 3 * constants.PLUG_RADIUS,
            event.scenePos().y() - constants.PLUG_RADIUS,
            6 * constants.PLUG_RADIUS,
            2 * constants.PLUG_RADIUS,
        )
        test_items = self.items(selection_rect)
        for item in test_items:
            if item and item.data(0) == constants.PLUG:
                test_item = item
                break

        if test_item:
            self.testing_graphic_attr = test_item.parentItem()

            if (
                self.testing_graphic_attr.has_input_connected()
            ):  # It is input and had connection
                connected_out_graphic_attr = next(
                    iter(self.testing_graphic_attr.connected_graphic_attrs)
                )
                self.disconnect_graphic_attrs(
                    connected_out_graphic_attr, self.testing_graphic_attr
                )
                for item in self.items():
                    if item.data(0) == constants.CONNECTOR_LINE:
                        if self.testing_graphic_attr in [item.data(1), item.data(2)]:
                            self.removeItem(item)
                self.testing_graphic_attr = connected_out_graphic_attr

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        QtWidgets.QGraphicsScene.mouseDoubleClickEvent(self, event)
        selection_rect = QtCore.QRect(
            event.scenePos().x() - 1,
            event.scenePos().y() - 1,
            1,
            1,
        )
        test_items = self.items(selection_rect)
        for item in test_items:
            if item and item.data(0) == constants.GRAPHIC_NODE:
                GS.attribute_editor_node_addition_requested.emit(item.logic_node.uuid)
                break

    def mouseMoveEvent(self, event):
        QtWidgets.QGraphicsScene.mouseMoveEvent(self, event)

        if self.testing_graphic_attr:
            if constants.GLOW_EFFECTS:
                self.testing_path_glow.show()
            self.testing_path.show()

            test_origin = self.testing_graphic_attr.plug_coords()
            new_path = QtGui.QPainterPath(test_origin)

            p1 = self.testing_path.path().pointAtPercent(0)
            p2 = event.scenePos()
            c_p1 = QtCore.QPoint(((p2.x() + p1.x()) / 2) + 10, p1.y())
            c_p2 = QtCore.QPoint(((p2.x() + p1.x()) / 2) - 10, p2.y())
            if constants.STRAIGHT_LINES:
                new_path.lineTo(p2)
            else:
                new_path.cubicTo(c_p1, c_p2, p2)

            if new_path.length() > 7000:
                self.testing_path.hide()
                self.testing_path_glow.hide()
            else:
                self.testing_path.show()
                if constants.GLOW_EFFECTS:
                    self.testing_path_glow.show()

            self.testing_path.setPath(new_path)
            self.testing_path_glow.setPath(new_path)

    def mouseReleaseEvent(self, event):
        QtWidgets.QGraphicsScene.mouseReleaseEvent(self, event)

        if not event.button() == QtCore.Qt.LeftButton:
            return

        event_x = event.scenePos().x()
        event_y = event.scenePos().y()

        test_item = None
        selection_rect = QtCore.QRect(
            event_x - 3 * constants.PLUG_RADIUS,
            event_y - constants.PLUG_RADIUS,
            6 * constants.PLUG_RADIUS,
            2 * constants.PLUG_RADIUS,
        )
        test_items = self.items(selection_rect)
        for item in test_items:
            if item and item.data(0) == constants.PLUG:
                test_item = item
                break

        if self.testing_graphic_attr and test_item:
            graphic_attr_1 = self.testing_graphic_attr
            graphic_attr_2 = test_item.parentItem()
            if graphic_attr_1.parent_node != graphic_attr_2.parent_node:
                if graphic_attr_2.connector_type == constants.INPUT:
                    graphic_attr_2.disconnect_input()
                    for line in self.items():
                        if line.data(
                            0
                        ) == constants.CONNECTOR_LINE and graphic_attr_2 in [
                            line.data(1),
                            line.data(2),
                        ]:
                            self.removeItem(line)
                self.connect_graphic_attrs(graphic_attr_1, graphic_attr_2)
            else:
                self.in_screen_feedback.emit(
                    "Those two attributes belong to the same node!",
                    logging.WARNING,
                )
        elif self.testing_graphic_attr and test_item is None:
            graphic_attr_1 = self.testing_graphic_attr
            if graphic_attr_1.connector_type == constants.INPUT:
                new_g_node = None
                if graphic_attr_1.logic_attribute.data_type == str:
                    new_g_node = self.add_graphic_node_by_name(
                        "StrInput", event_x, event_y
                    )
                    graphic_attr_2 = new_g_node["out_str"]
                    self.connect_graphic_attrs(graphic_attr_1, graphic_attr_2)
                elif graphic_attr_1.logic_attribute.data_type == list:
                    new_g_node = self.add_graphic_node_by_name(
                        "ListInput", event_x, event_y
                    )
                    graphic_attr_2 = new_g_node["out_list"]
                    self.connect_graphic_attrs(graphic_attr_1, graphic_attr_2)
                elif graphic_attr_1.logic_attribute.data_type == dict:
                    new_g_node = self.add_graphic_node_by_name(
                        "DictInput", event_x, event_y
                    )
                    graphic_attr_2 = new_g_node["out_dict"]
                    self.connect_graphic_attrs(graphic_attr_1, graphic_attr_2)
                elif graphic_attr_1.logic_attribute.data_type == int:
                    new_g_node = self.add_graphic_node_by_name(
                        "IntInput", event_x, event_y
                    )
                    graphic_attr_2 = new_g_node["out_int"]
                    self.connect_graphic_attrs(graphic_attr_1, graphic_attr_2)
                elif graphic_attr_1.logic_attribute.data_type == bool:
                    new_g_node = self.add_graphic_node_by_name(
                        "BoolInput", event_x, event_y
                    )
                    graphic_attr_2 = new_g_node["out_bool"]
                    self.connect_graphic_attrs(graphic_attr_1, graphic_attr_2)

                if new_g_node:
                    new_g_node.moveBy(
                        event_x
                        - graphic_attr_2.plug_coords().x()
                        + 3 * constants.PLUG_RADIUS,
                        event_y - graphic_attr_2.plug_coords().y(),
                    )

        self.testing_graphic_attr = None
        self.testing_path.hide()
        self.testing_path_glow.hide()

        GS.attribute_editor_global_refresh_requested.emit()

    def reset_all_graphic_nodes(self):
        utils.print_separator("Resetting all graphic nodes")
        for g_node in self.all_nodes:
            g_node.reset()

    def show_result_on_nodes(self):
        """Display the internal result of each node."""
        for g_node in self.all_nodes:
            g_node.show_result()

    def reset_graphic_scene(self):
        self.reset_all_graphic_nodes()
        self.logic_scene.reset_all_nodes()
        GS.attribute_editor_global_refresh_requested.emit()

    def run_graphic_scene(self):
        self.reset_all_graphic_nodes()
        self.logic_scene.run_all_nodes()
        self.show_result_on_nodes()
        GS.attribute_editor_global_refresh_requested.emit()

    def keyPressEvent(self, event: QtWidgets.QGraphicsScene.event):
        QtWidgets.QGraphicsScene.keyPressEvent(self, event)

        if self.focusItem():  # Means we are editing a widget in some input node
            return

        if event.key() == QtCore.Qt.Key_Delete:
            for n in self.selected_nodes():
                GS.attribute_editor_remove_node_requested.emit(n.logic_node.uuid)
                self.delete_node(n)
        elif event.key() == QtCore.Qt.Key_F:
            self.fit_in_view()
        elif event.key() == QtCore.Qt.Key_Return:
            for n in self.selected_nodes():
                self.run_single_node(n)
        elif event.key() == QtCore.Qt.Key_R:
            for n in self.selected_nodes():
                self.reset_single_node(n)
        elif event.key() == QtCore.Qt.Key_E:
            for n in self.selected_nodes():
                self.examine_code(n)

    def fit_in_view(self):
        self.parent().resetMatrix()
        nodes = list(self.all_nodes)
        if self.selected_nodes():
            nodes = self.selected_nodes()
        rect = nodes[0].sceneBoundingRect()
        for n in nodes:
            rect = rect.united(n.sceneBoundingRect())

        self.parent().fitInView(rect, QtCore.Qt.KeepAspectRatio)

    def dragEnterEvent(self, event):
        QtWidgets.QGraphicsScene.dragEnterEvent(self, event)
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        QtWidgets.QGraphicsScene.dragMoveEvent(self, event)
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        QtWidgets.QGraphicsScene.dragLeaveEvent(self, event)
        event.acceptProposedAction()

    def dropEvent(self, event):
        event_data = event.mimeData()
        if event_data.hasUrls():
            event_urls = event_data.urls()
            for url in event_urls:
                if os.path.isfile(url.toLocalFile()):
                    self.load_from_file(url.toLocalFile())
        else:
            self.dropped_node.emit(
                event.scenePos().x() - 100, event.scenePos().y() - 100
            )
        QtWidgets.QGraphicsScene.dropEvent(self, event)
        event.acceptProposedAction()
