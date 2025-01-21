# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import datetime
import logging
import math
import os
import platform
import pprint
import re
import subprocess
import sys

from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui
import yaml

from all_nodes import constants
from all_nodes.graphic.graphic_annotation import GeneralGraphicAnnotation
from all_nodes.graphic.graphic_node import GeneralGraphicNode, GeneralGraphicAttribute
from all_nodes.logic.class_registry import CLASS_REGISTRY as CR
from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes.logic.logic_scene import LogicScene
from all_nodes import utils
from all_nodes.graphic.widgets.attribute_picker import AttributePicker
from all_nodes.graphic.widgets.class_searcher import ClassSearcher
from all_nodes.graphic.widgets.global_signaler import GlobalSignaler
from all_nodes.graphic.widgets.small_widgets import FeedbackLineEdit


GS = GlobalSignaler()

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

        self.drag_pos = None
        self.middle_pressed = False
        self.left_pressed = False

        self.feedback_lines = []
        self.feedback_line = QtWidgets.QLineEdit(parent=self)
        self.feedback_line.setReadOnly(True)
        self.feedback_line.setFont(QtGui.QFont("arial", 12))
        self.feedback_line.hide()

        self.run_btn = QtWidgets.QPushButton("Run scene", parent=self)
        self.run_btn.setFixedSize(160, 35)
        self.run_btn.setFont(QtGui.QFont("arial", 10))
        self.run_btn.setIcon(QtGui.QIcon("icons:brain.png"))

        self.reset_btn = QtWidgets.QPushButton("Reset scene", parent=self)
        self.reset_btn.setFixedSize(160, 35)
        self.reset_btn.setFont(QtGui.QFont("arial", 10))
        self.reset_btn.setIcon(QtGui.QIcon("icons:reset.png"))

        self.hourglass_animation = QtWidgets.QLabel(parent=self)
        self.hourglass_animation.setAlignment(QtCore.Qt.AlignCenter)
        ag_file = "ui:hourglass.gif"
        self.movie = QtGui.QMovie(ag_file, QtCore.QByteArray(), self)
        self.movie.setCacheMode(QtGui.QMovie.CacheAll)
        self.movie.setSpeed(100)
        self.hourglass_animation.setMovie(self.movie)
        self.movie.start()
        self.hourglass_animation.hide()

        self.class_searcher = ClassSearcher(parent=self)
        self.class_searcher.hide()
        GS.signals.class_searcher_move.connect(self.move_search_bar)

        self.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)

        # Signals connection
        self.reset_btn.clicked.connect(self.reset)
        self.run_btn.clicked.connect(self.run)

        GS.signals.execution_started.connect(self.hourglass_animation.show)
        GS.signals.execution_finished.connect(self.hourglass_animation.hide)
        GS.signals.class_scanning_finished.connect(
            lambda: self.show_feedback("Finished scanning classes", level=logging.INFO)
        )

    # RUN AND REFRESH ----------------------
    def run(self):
        """
        Run the current scene.
        """
        if self.scene():
            self.scene().run_graphic_scene()
            GS.signals.attribute_editor_global_refresh_requested.emit()

    def reset(self):
        """
        Reset the current scene.
        """
        if self.scene():
            self.scene().reset_graphic_scene()
            GS.signals.attribute_editor_global_refresh_requested.emit()

    # UTILITY ----------------------
    def show_feedback(self, message, level=logging.INFO):
        """
        Display a basic piece of feedback on screen, on top of the graphics scene.

        Args:
            message (str): message to display
            level (int): level of the message
        """
        new_feedback_line = FeedbackLineEdit(parent=self)

        effect = QtWidgets.QGraphicsOpacityEffect(new_feedback_line)
        anim = QtCore.QPropertyAnimation(effect, b"opacity", parent=self)
        anim.setStartValue(1)
        anim.setEndValue(0)
        anim.setDuration(5500)

        if level == logging.DEBUG:
            if not constants.IN_DEV:
                return
            new_feedback_line.setStyleSheet(
                "color:cyan; background-color:transparent; border:none"
            )
            message = "[DEBUG] " + message
        elif level == logging.INFO:
            new_feedback_line.setStyleSheet(
                "color:lime; background-color:transparent; border:none"
            )
            message = "[INFO] " + message
        elif level == logging.WARNING:
            new_feedback_line.setStyleSheet(
                "color:orange; background-color:transparent; border:none"
            )
            message = "[WARNING] " + message
        elif level == logging.ERROR:
            new_feedback_line.setStyleSheet(
                "color:red; background-color:transparent; border:none"
            )
            message = "[ERROR] " + message
            anim.setDuration(8000)

        new_feedback_line.show()
        new_feedback_line.setText(message)
        new_feedback_line.setGraphicsEffect(effect)
        new_feedback_line.stackUnder(self.reset_btn)
        new_feedback_line.stackUnder(self.run_btn)
        anim.start()

        new_feedback_line.setFixedSize(self.width(), 30)
        self.feedback_lines.insert(0, new_feedback_line)

        if len(self.feedback_lines) > 5:
            self.feedback_lines.pop()

        for line in self.feedback_lines:
            line.move(25, self.height() - 50 - self.feedback_lines.index(line) * 30)

    def move_search_bar(self, x, y):
        """
        Move the classes search bar to a new position

        Args:
            x (int)
            y (int)
        """
        self.class_searcher.move(self.mapFromGlobal(QtCore.QPoint(x, y)))
        self.class_searcher.reset()

    # RESIZE EVENTS ----------------------
    def resizeEvent(self, event):
        self.hourglass_animation.move(self.width() - 200, self.height() - 200)
        self.hourglass_animation.setFixedSize(200, 200)
        self.movie.setScaledSize(QtCore.QSize(200, 200))

        for line in self.feedback_lines:
            line.move(25, self.height() - 50 - self.feedback_lines.index(line) * 30)
            line.setFixedSize(self.width(), 30)

        self.reset_btn.move(self.width() - 380, self.height() - 55)
        self.run_btn.move(self.width() - 200, self.height() - 55)

        QtWidgets.QGraphicsView.resizeEvent(self, event)

    # MOUSE EVENTS ----------------------
    def mousePressEvent(self, event):
        self.middle_pressed = False

        self.drag_pos = event.pos()
        if event.button() == QtCore.Qt.MidButton:
            self.middle_pressed = True
        elif event.button() == QtCore.Qt.LeftButton:
            self.left_pressed = True
            self.class_searcher.hide()

        QtWidgets.QGraphicsView.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        new_pos = event.pos()

        if self.middle_pressed and self.drag_pos:
            disp = new_pos - self.drag_pos
            self.drag_pos = new_pos
            transform = self.transform()
            deltaX = disp.x() / transform.m11()
            deltaY = disp.y() / transform.m22()
            self.translate(deltaX, deltaY)

        QtWidgets.QGraphicsView.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MidButton:
            self.middle_pressed = False
            self.drag_pos = None

        QtWidgets.QGraphicsView.mouseReleaseEvent(self, event)

    def wheelEvent(self, event):
        zoom_increase = 1.45
        zoom_decrease = 0.65

        if event.delta() > 0:
            self.scale(zoom_increase, zoom_increase)
        else:
            self.scale(zoom_decrease, zoom_decrease)

    # DRAG AND DROP EVENT ----------------------
    def dragEnterEvent(self, event):
        QtWidgets.QGraphicsView.dragEnterEvent(self, event)
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        QtWidgets.QGraphicsView.dragMoveEvent(self, event)
        event.acceptProposedAction()


# -------------------------------- CUSTOM SCENE CLASS -------------------------------- #
class CustomScene(QtWidgets.QGraphicsScene):
    def __init__(self, context=None):
        QtWidgets.QGraphicsScene.__init__(self)

        # Logic scene
        self.logic_scene = context.internal_scene if context else LogicScene()
        self.filepath = context.CONTEXT_DEFINITION_FILE if context else None

        # Nodes
        self.all_graphic_nodes = set()

        # Annotations
        self.all_graphic_annotations = set()

        # Path tests
        self.testing_graphic_attr = None

        self.testing_path = ConnectorLine()
        self.testing_path.set_testing_appearance()
        self.testing_path.hide()
        self.addItem(self.testing_path)

    # SCENE SETUP ----------------------
    def drawBackground(self, painter, rect):
        pen = QtGui.QPen(QtGui.QColor(255, 230, 255, 150), 2)
        painter.setPen(pen)
        for i in range(-20_000, 20_000, 200):
            if i > rect.x() and i < rect.x() + rect.width():
                painter.drawLine(QtCore.QLine(i, -20_000, i, 20_000))
            if i > rect.y() and i < rect.y() + rect.height():
                painter.drawLine(QtCore.QLine(-20_000, i, 20_000, i))

    # ANNOTATIONS ----------------------
    def add_annotation_by_type(
        self, annotation_type: str, x: int = 0, y: int = 0
    ) -> GeneralGraphicAnnotation:
        new_annotation = GeneralGraphicAnnotation(annotation_type)
        new_annotation.setPos(x, y)
        self.all_graphic_annotations.add(new_annotation)
        self.addItem(new_annotation)
        return new_annotation

    # ADD AND DELETE NODES ----------------------
    def add_graphic_node_by_class_name(
        self, node_classname: str, x: int = 0, y: int = 0
    ) -> GeneralGraphicNode:
        """
        Create a new graphic node just by giving the class name

        Args:
            node_classname (str): class name to be instantiated
            x (int): optional, coords to place the node at
            y (int): optional, coords to place the node at

        Returns:
            GeneralGraphicNode: newly created node
        """
        all_classes = CR.get_all_classes()
        for lib in sorted(all_classes):
            for m in all_classes[lib]:
                color = all_classes[lib][m]["color"]
                for name, _ in all_classes[lib][m]["classes"]:
                    if node_classname == name:
                        new_logic_node = self.logic_scene.add_node_by_name(
                            node_classname
                        )
                        new_graph_node = GeneralGraphicNode(new_logic_node, color)
                        self.addItem(new_graph_node)
                        self.all_graphic_nodes.add(new_graph_node)
                        new_graph_node.setPos(x, y)
                        GS.signals.main_screen_feedback.emit(
                            "Created graphic node {}".format(node_classname),
                            logging.INFO,
                        )
                        return new_graph_node

        GS.signals.main_screen_feedback.emit(
            "Could not create graphic node {}".format(node_classname),
            logging.ERROR,
        )
        return None

    def add_graphic_node_from_logic_node(
        self, logic_node, x: int = 0, y: int = 0
    ) -> GeneralGraphicNode:
        """
        Create a new graphic node from an existing logic node

        Args:
            logic_node (GeneralLogicNode): logic node to be represented graphically
            x (int): optional, coords to place the node at
            y (int): optional, coords to place the node at

        Returns:
            GeneralGraphicNode: newly created node
        """
        all_classes = CR.get_all_classes()
        for lib in sorted(all_classes):
            for m in all_classes[lib]:
                color = all_classes[lib][m]["color"]
                for name, _ in all_classes[lib][m]["classes"]:
                    if logic_node.class_name == name:
                        new_graph_node = GeneralGraphicNode(logic_node, color)
                        self.addItem(new_graph_node)
                        self.all_graphic_nodes.add(new_graph_node)
                        LOGGER.info(
                            "Created graphic node from logic node {} at x:{} y:{}".format(
                                logic_node.node_name, x, y
                            )
                        )
                        new_graph_node.moveBy(x, y)
                        if not logic_node.active:
                            new_graph_node.show_deactivated()
                        return new_graph_node

    def delete_node(self, graphic_node: GeneralGraphicNode):
        """
        Delete graphic node from this scene.

        Args:
            graphic_node (GeneralGraphicNode): node to delete
        """
        self.clear_node_lines(graphic_node)
        graphic_node.clear_all_connections()
        self.all_graphic_nodes.remove(graphic_node)
        self.removeItem(graphic_node)

        self.logic_scene.remove_node_by_name(graphic_node.logic_node.node_name)

        del graphic_node

    def delete_annotation(self, graphic_annotation: GeneralGraphicAnnotation):
        self.all_graphic_annotations.remove(graphic_annotation)
        self.removeItem(graphic_annotation)
        del graphic_annotation

    # NODE CONNECTIONS/LINES ----------------------
    def connect_graphic_attrs(
        self,
        graphic_attr_1: GeneralGraphicAttribute,
        graphic_attr_2: GeneralGraphicAttribute,
        check_logic=True,
    ):
        """
        Attempt to connect two graphic attributes.

        Args:
            graphic_attr_1 (GeneralGraphicAttribute): graphic attribute to be connected
            graphic_attr_2 (GeneralGraphicAttribute): graphic attribute to be connected
            check_logic (bool): optional, whether or not the possibility of connecting should be checked
        """

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
        can_connect, reason = graphic_attr_1.connect_graphic_attr(
            graphic_attr_2, check_logic
        )
        if can_connect:
            GS.signals.main_screen_feedback.emit(
                reason,
                logging.DEBUG,
            )
            self.draw_valid_line(graphic_attr_1, graphic_attr_2)
        else:
            GS.signals.main_screen_feedback.emit(
                reason,
                logging.WARNING,
            )

    def draw_valid_line(self, graphic_attr_1, graphic_attr_2):
        """
        Draw a line in between to graphic attributes that we know can be connected.

        Args:
            graphic_attr_1 (GeneralGraphicAttribute)
            graphic_attr_2 (GeneralGraphicAttribute)
        """
        connector_line = ConnectorLine(graphic_attr_1, graphic_attr_2)
        self.addItem(connector_line)
        connector_line.setZValue(-1)

    def redraw_node_lines(self, node: GeneralGraphicNode):
        """
        Redraw all input and output lines that arrive to/from a node.

        Args:
            node (GeneralGraphicNode): node to redraw lines for
        """
        graphic_attrs = [
            c
            for c in self.items()
            if c.data(0) == constants.GRAPHIC_ATTRIBUTE and c.parent_node == node
        ]

        for g in graphic_attrs:
            g_1, g_2 = None, None
            for line in self.items():
                if line.data(0) != constants.CONNECTOR_LINE:
                    continue
                g_1, g_2 = line.data(1), line.data(2)

                if g in [g_1, g_2]:
                    line.repath()

    def disconnect_graphic_attrs(
        self,
        graphic_attr_1: GeneralGraphicAttribute,
        graphic_attr_2: GeneralGraphicAttribute,
    ):
        """
        Disconnect two graphic attributes.

        Args:
            graphic_attr_1 (GeneralGraphicAttribute)
            graphic_attr_2 (GeneralGraphicAttribute)
        """
        graphic_attr_1.disconnect_from(graphic_attr_2)
        GS.signals.attribute_editor_global_refresh_requested.emit()

    def clear_node_lines(self, node: GeneralGraphicNode):
        """
        Remove all input and output lines that arrive to/from a node.

        Args:
            node (GeneralGraphicNode): node to remove lines for
        """
        for line in self.items():
            g_1, g_2 = line.data(1), line.data(2)
            if g_1 is None or g_2 is None:
                continue
            if line.data(0) == constants.CONNECTOR_LINE and node in [
                g_1.parent_node,
                g_2.parent_node,
            ]:
                self.removeItem(line)

    # SAVE AND LOAD ----------------------
    def set_filepath(self, filepath):
        self.filepath = filepath

    def save_to_file(self, filepath=None):
        """
        Save this graphics scene to a file.

        Args:
            filepath (str, optional): filepath to save to. Defaults to None.
        """
        target_file = filepath
        if not filepath:
            dialog = QtWidgets.QFileDialog()
            result = dialog.getSaveFileName(
                caption="Specify target file", filter="*.yml *.ctx"
            )
            if not result[0] or not result[1]:
                return
            target_file = result[0]
        else:
            dlg = QtWidgets.QMessageBox(parent=None)
            dlg.setWindowTitle("Save scene")
            dlg.setText(
                f"<p style='white-space:pre'>Are you sure?<br>This will overwrite the scene at:<br>{filepath}"
            )
            dlg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            dlg.setIcon(QtWidgets.QMessageBox.Question)
            button = dlg.exec_()

            if button == QtWidgets.QMessageBox.No:
                return

        # Grab logic scene info and add the xy coords
        the_dict = self.logic_scene.convert_scene_to_dict()
        for g_node in self.all_graphic_nodes:
            node_name = g_node.logic_node.node_name
            for node_dict in the_dict["nodes"]:
                if node_name in node_dict:
                    node_dict[node_name]["x_pos"] = int(g_node.scenePos().x())
                    node_dict[node_name]["y_pos"] = int(g_node.scenePos().y())
                    break

        # Add annotations
        if self.all_graphic_annotations:
            the_dict["annotations"] = list()
            annotation_count = 0
            for ann in self.all_graphic_annotations:
                annotation_dict = dict()
                annotation_dict["annotation_type"] = ann.get_type()
                annotation_dict["x_pos"] = int(ann.scenePos().x())
                annotation_dict["y_pos"] = int(ann.scenePos().y())
                if ann.get_text():
                    annotation_dict["text"] = str(ann.get_text())
                the_dict["annotations"].append(annotation_dict)
                annotation_count += 1

        # Save logic scene
        self.logic_scene.save_to_file(target_file, the_dict)

    def load_from_file(self, source_file: str, create_logic_nodes=True):
        """
        Create a graphic scene from a file.

        Args:
            source_file (str): filepath of scene to load
        """
        # Set filepath
        self.set_filepath(source_file)

        # Grab the scene dict and create logic nodes
        scene_dict = dict()
        with open(source_file, "r") as file:
            scene_dict = yaml.safe_load(file)

        new_logic_nodes = self.logic_scene.all_logic_nodes
        if create_logic_nodes:
            new_logic_nodes = self.logic_scene.load_from_file(source_file)

        # Create graphic nodes
        for logic_node in new_logic_nodes:
            for node_dict in scene_dict["nodes"]:
                node_name = next(iter(node_dict))
                if logic_node.node_name == node_name:
                    self.add_graphic_node_from_logic_node(
                        logic_node,
                        node_dict[node_name]["x_pos"],
                        node_dict[node_name]["y_pos"],
                    )
                    break

        # Create annotations
        if "annotations" in scene_dict:
            for ann_dict in scene_dict["annotations"]:
                new_annotation = self.add_annotation_by_type(
                    ann_dict["annotation_type"], ann_dict["x_pos"], ann_dict["y_pos"]
                )
                new_annotation.set_text(ann_dict.get("text", ""))

        # Connections
        all_graphic_attrs = []
        for g_node in self.all_graphic_nodes:
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
                connected_logic_attributes.append(connected_logic_attribute.dot_name)
            for logic_attr_full_name in connected_logic_attributes:
                for other_g_attribute in all_graphic_attrs:
                    if (
                        other_g_attribute.logic_attribute.dot_name
                        == logic_attr_full_name
                    ):
                        LOGGER.info(
                            "Connected graphic attributes {} -> {}".format(
                                g_attribute.logic_attribute.dot_name,
                                other_g_attribute.logic_attribute.dot_name,
                            )
                        )
                        self.connect_graphic_attrs(
                            g_attribute, other_g_attribute, check_logic=False
                        )
                        break

    # NODE-SPECIFIC ----------------------
    def rename_graphic_node(self, graphic_node: GeneralGraphicNode):
        """
        Rename a graphic node in the scene.

        Args:
            graphic_node (GeneralGraphicNode): node to be renamed

        """
        logic_node = graphic_node.logic_node
        new_name, ok = QtWidgets.QInputDialog().getText(
            None,
            "Rename node " + logic_node.node_name,
            "New name:",
        )  # TODO find how to style this

        if ok and new_name:
            if self.logic_scene.rename_node(logic_node, new_name):
                graphic_node.update_name()
                GS.signals.attribute_editor_refresh_node_requested.emit(logic_node.uuid)
                GS.signals.tab_names_refresh_requested.emit()
            else:
                if logic_node.node_name == new_name:
                    GS.signals.main_screen_feedback.emit(
                        "Cannot rename to '{}', it is the same name as now".format(
                            new_name
                        ),
                        logging.INFO,
                    )
                else:
                    if not GeneralLogicNode.name_is_valid(new_name):
                        GS.signals.main_screen_feedback.emit(
                            "Cannot rename to '{}', naming must start with uppercase and "
                            "cannot include special characters".format(new_name),
                            logging.WARNING,
                        )
                    else:
                        GS.signals.main_screen_feedback.emit(
                            "Cannot rename to '{}', "
                            "check that no other node has that name".format(new_name),
                            logging.WARNING,
                        )

    def examine_code(self, graphic_node_list: list = None):
        """
        Show the code of a node in an external editor.

        If the node is a context, show its .yml definition file as well.

        Args:
            graphic_node_list (list): node to examine code from
        """
        if not graphic_node_list:
            graphic_node_list = self.selected_nodes()

        commands = []

        if platform.system() == "Windows":
            commands.extend(["notepad", "notepad++"])
        elif platform.system() == "Linux":
            commands.extend(["gedit", "pluma"])

        for graphic_node in graphic_node_list:
            logic_node = graphic_node.logic_node

            for command in commands:
                try:
                    subprocess.Popen([command, logic_node.FILEPATH])
                    if logic_node.IS_CONTEXT:
                        subprocess.Popen([command, logic_node.CONTEXT_DEFINITION_FILE])

                    break

                except Exception as e:
                    msg = "Could not use editor '{}': {}".format(command, e)
                    LOGGER.debug(msg)

    def expand_contexts(self, graphic_node_list: list = None):
        """
        Launch signal to expand a selected context node.

        Args:
            graphic_node_list (list): nodes to be expanded
        """
        if not graphic_node_list:
            graphic_node_list = self.selected_nodes()
        for graphic_node in graphic_node_list:
            if graphic_node.logic_node.IS_CONTEXT:
                GS.signals.context_expansion_requested.emit(
                    graphic_node.logic_node.uuid
                )

    def show_log(self, graphic_node: GeneralGraphicNode):
        """
        For debugging purposes, print to screen internal information of a node.

        Args:
            graphic_node (GeneralGraphicNode): node to display info from.
        """
        print(
            "\n{}\n{}".format(
                graphic_node.logic_node.node_name,
                "-" * len(graphic_node.logic_node.node_name),
            )
        )
        pprint.pprint(graphic_node.logic_node.get_node_full_dict())

    def run_nodes(self, graphic_node_list: list = None):
        """
        Execute a graphic node.

        Args:
             graphic_node_list (list): nodes to execute
        """
        # Check nodes to execute
        if not graphic_node_list:
            graphic_node_list = self.selected_nodes()

        if not graphic_node_list:
            GS.signals.main_screen_feedback.emit(
                "No nodes selected, nothing to execute", logging.WARNING
            )
            return

        # Execution
        GS.signals.main_screen_feedback.emit(
            "Running only selected node(s)", logging.INFO
        )
        GS.signals.execution_started.emit()

        self.logic_scene.run_list_of_nodes(
            [graphic_node.logic_node for graphic_node in graphic_node_list]
        )

    def reset_nodes(self, graphic_node_list: list = None):
        """
        Reset appearance of a graphic node and then also reset its
        internal logic node.

        Args:
             graphic_node_list (list): nodes to reset
        """
        if not graphic_node_list:
            graphic_node_list = self.selected_nodes()
        for graphic_node in graphic_node_list:
            graphic_node.reset()
            graphic_node.logic_node.reset()

        GS.signals.main_screen_feedback.emit("Resetting selected node(s)", logging.INFO)
        GS.signals.attribute_editor_global_refresh_requested.emit()

    def soft_reset_nodes(self, graphic_node_list: list = None):
        """
        Reset appearance of a graphic node and then also soft-reset its
        internal logic node.

        Args:
            graphic_node_list (list): nodes to soft-reset
        """
        if not graphic_node_list:
            graphic_node_list = self.selected_nodes()
        for graphic_node in graphic_node_list:
            graphic_node.reset()
            graphic_node.logic_node.soft_reset()

        GS.signals.main_screen_feedback.emit(
            "Soft-resetting selected node(s)", logging.INFO
        )
        GS.signals.attribute_editor_global_refresh_requested.emit()

    def toggle_activated_nodes(self, graphic_node_list: list = None):
        """
        Toggle whether or not a graphic node is activated.

        Args:
            graphic_node_list (list): nodes to toggle activation of
        """
        if not graphic_node_list:
            graphic_node_list = self.selected_nodes()
        for graphic_node in graphic_node_list:
            graphic_node.toggle_activated()

        # GS.signals.attribute_editor_global_refresh_requested.emit()  # TODO consider this in attribute editor?

    def add_attr_to_node(self, graphic_node: GeneralGraphicNode):
        a_picker = AttributePicker()
        if a_picker.get_results():
            graphic_node.add_single_graphic_attribute(*a_picker.get_results())

    def export_nodes_code(self, graphic_node_list: list):
        if not graphic_node_list:
            graphic_node_list = self.selected_nodes()

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        py_contents = (
            f"# ------ File written by 'all_nodes' {timestamp} ------ # \n\n"
            "from all_nodes.constants import InputsGUI, PreviewsGUI \n"
            "from all_nodes.logic.logic_node import GeneralLogicNode \n"
            "from all_nodes import utils \n\n\n"
            "LOGGER = utils.get_logger(__name__)\n\n\n"
        )

        dialog = QtWidgets.QFileDialog()
        result = dialog.getExistingDirectory(
            caption="Specify target file", filter="*.yml *.ctx"
        )
        if not result:
            return

        out_path = os.path.join(result, f"all_nodes_{timestamp}.py")

        with open(out_path, "w") as f:
            f.write(py_contents)

        for g_node in graphic_node_list:
            code = g_node.get_as_code()
            code = re.sub(
                "<class '(?P<datatype>[a-zA-Z_.0-9]+)'>", "\g<datatype>", code
            )
            code = re.sub(
                "<(?P<guitype>[a-zA-Z0-9._]+): '[a-zA-Z ]+'+>",
                "\g<guitype>",
                code,
            )
            with open(out_path, "a") as f:
                f.write(code)
                f.write("\n\n\n")

        try:
            subprocess.Popen([sys.executable, "-m", "ruff", "format", out_path])
        except Exception as e:
            msg = "Could not use ruff: {}".format(e)
            LOGGER.info(msg)

        LOGGER.info(f"Exported code to {out_path}")
        GS.signals.main_screen_feedback.emit(
            f"Exported code to {out_path}", logging.INFO
        )

    def deselect_all(self):
        """
        Deselect all graphic nodes.
        """
        for n in self.all_graphic_nodes:
            n.setSelected(False)

    # ANNOTATION SPECIFIC ----------------------
    def bring_annotation_to_front(self, annotation_list: list):
        if not annotation_list:
            annotation_list = self.selected_annotations()

        for annotation in annotation_list:
            annotation.setZValue(500)

    def move_annotation_backward(self, annotation_list: list):
        if not annotation_list:
            annotation_list = self.selected_annotations()

        for annotation in annotation_list:
            annotation.setZValue(-500)

    # SCENE EXECUTION ----------------------
    def reset_all_graphic_nodes(self):
        """
        Reset all graphic nodes.
        """
        utils.print_separator("Resetting all graphic nodes")
        for g_node in self.all_graphic_nodes:
            g_node.reset()

    def show_result_on_nodes(self):
        """
        Display the internal result of each graphic node.
        """
        for g_node in self.all_graphic_nodes:
            g_node.show_result()

    def reset_graphic_scene(self):
        """
        Reset the appearance of all the nodes in this graphic scene.
        """
        self.reset_all_graphic_nodes()
        self.logic_scene.reset_all_nodes()
        GS.signals.attribute_editor_global_refresh_requested.emit()

    def run_graphic_scene(self):
        """
        Run all the nodes in this graphic scene.
        """
        GS.signals.execution_started.emit()
        self.reset_all_graphic_nodes()
        self.logic_scene.run_all_nodes()

    # UTILITY ----------------------
    def selected_nodes(self) -> list:
        """
        Gather all selected nodes.

        Returns:
            list: with all selected nodes.
        """
        sel_nodes = []
        for n in self.all_graphic_nodes:
            if n.isSelected():
                sel_nodes.append(n)
        return sel_nodes

    def selected_annotations(self) -> list:
        sel_annotations = []
        for a in self.all_graphic_annotations:
            if a.isSelected():
                sel_annotations.append(a)
        return sel_annotations

    def fit_in_view(self):
        """
        If selected nodes, fit all of them in the view. Otherwise, fit all nodes.
        """
        self.parent().resetMatrix()
        nodes = list(self.all_graphic_nodes) + list(self.all_graphic_annotations)
        if self.selected_nodes() or self.selected_annotations():
            nodes = list(self.selected_nodes()) + list(self.selected_annotations())
        if not nodes:
            return
        rect = nodes[0].sceneBoundingRect()
        for n in nodes:
            rect = rect.united(n.sceneBoundingRect())

        self.parent().fitInView(
            rect + QtCore.QMarginsF(20.0, 20.0, 20.0, 20.0), QtCore.Qt.KeepAspectRatio
        )

    # CONTEXT EVENTS ----------------------
    def contextMenuEvent(self, event):
        selection_rect = QtCore.QRect(
            event.scenePos().x() - 1,
            event.scenePos().y() - 1,
            1,
            1,
        )
        test_items = self.items(selection_rect)
        if test_items:
            for item in test_items:
                if item and item.data(0) == constants.GRAPHIC_NODE:
                    self.menu_node(event, item)
                    break
                elif item and item.data(0) == constants.GRAPHIC_ANNOTATION:
                    self.menu_annotation(event, item)
                    break
        else:
            self.menu_scene(event)

        QtWidgets.QGraphicsScene.contextMenuEvent(self, event)

    def menu_node(self, event, node):
        menu = QtWidgets.QMenu()  # TODO add tooltips

        # Common actions
        rename_action = menu.addAction(" Rename this node")
        rename_action.setIcon(QtGui.QIcon("icons:rename.png"))
        rename_action.triggered.connect(lambda: self.rename_graphic_node(node))

        examine_code_action = menu.addAction(" Examine code")
        examine_code_action.setIcon(QtGui.QIcon("icons:examine.png"))
        examine_code_action.triggered.connect(lambda: self.examine_code([node]))

        # Execution-related  actions
        menu.addSeparator()

        run_nodes_action = menu.addAction(" Run only this node")
        run_nodes_action.setIcon(QtGui.QIcon("icons:run_one.svg"))
        run_nodes_action.triggered.connect(lambda: self.run_nodes([node]))

        reset_nodes_action = menu.addAction(" Reset only this node")
        reset_nodes_action.setIcon(QtGui.QIcon("icons:reset.png"))
        reset_nodes_action.triggered.connect(lambda: self.reset_nodes([node]))

        deactivate_single_node_action = menu.addAction(
            " Activate/deactivate only this node"
        )
        deactivate_single_node_action.setIcon(QtGui.QIcon("icons:close.svg"))
        deactivate_single_node_action.triggered.connect(
            lambda: self.toggle_activated_nodes([node])
        )

        # Context-specific
        if node.logic_node.IS_CONTEXT:
            menu.addSeparator()
            expand_context_action = menu.addAction(" Expand context")
            expand_context_action.setIcon(QtGui.QIcon("icons:cubes.svg"))
            expand_context_action.triggered.connect(
                lambda: self.expand_contexts([node])
            )

        # Add attributes
        menu.addSeparator()
        add_attr_to_node_action = menu.addAction(" Add new attribute to this node")
        add_attr_to_node_action.setIcon(QtGui.QIcon("icons:plus.svg"))
        add_attr_to_node_action.triggered.connect(lambda: self.add_attr_to_node(node))

        # Export code
        export_nodes_code_action = menu.addAction(" Export this node's code")
        export_nodes_code_action.setIcon(QtGui.QIcon("icons:wand.svg"))
        export_nodes_code_action.triggered.connect(
            lambda: self.export_nodes_code([node])
        )

        # Debug
        menu.addSeparator()
        soft_reset_nodes_action = menu.addAction(" [DEBUG] Soft-reset only this node")
        soft_reset_nodes_action.setIcon(QtGui.QIcon("icons:reset.png"))
        soft_reset_nodes_action.triggered.connect(lambda: self.soft_reset_nodes([node]))

        # DEV-specific
        if constants.IN_DEV:
            menu.addSeparator()
            print_node_log_action = menu.addAction(" Print node log")
            print_node_log_action.setIcon(QtGui.QIcon("icons:nodes_2.png"))
            print_node_log_action.triggered.connect(lambda: self.show_log(node))

        # Style
        f = QtCore.QFile(r"ui:stylesheet.qss")  # TODO not ideal, maybe a reduced qss?
        with open(f.fileName(), "r") as s:
            menu.setStyleSheet(s.read())

        # Exec
        menu.exec_(event.screenPos(), parent=self)

    def menu_annotation(self, event, node):
        menu = QtWidgets.QMenu()  # TODO add tooltips

        bring_forward_action = menu.addAction(" Bring annotation to front")
        bring_forward_action.setIcon(QtGui.QIcon("icons:front.svg"))
        bring_forward_action.triggered.connect(
            lambda: self.bring_annotation_to_front([node])
        )

        move_backward_action = menu.addAction(" Move annotation back")
        move_backward_action.setIcon(QtGui.QIcon("icons:back.svg"))
        move_backward_action.triggered.connect(
            lambda: self.move_annotation_backward([node])
        )

        # Style
        f = QtCore.QFile(r"ui:stylesheet.qss")  # TODO not ideal, maybe a reduced qss?
        with open(f.fileName(), "r") as s:
            menu.setStyleSheet(s.read())

        # Exec
        menu.exec_(event.screenPos(), parent=self)

    def menu_scene(self, event):
        menu = QtWidgets.QMenu()  # TODO add tooltips

        # Common actions
        run_action = menu.addAction(" Run this scene")
        run_action.setIcon(QtGui.QIcon("icons:brain.png"))
        run_action.triggered.connect(self.run_graphic_scene)

        # Saving
        if self.filepath:
            menu.addSeparator()
            save_action = menu.addAction(
                f" Save changes to {os.path.basename(self.filepath)}"
            )
            save_action.setIcon(QtGui.QIcon("icons:save.svg"))
            save_action.triggered.connect(lambda: self.save_to_file(self.filepath))
        else:
            save_action = menu.addAction(" Save scene as")
            save_action.setIcon(QtGui.QIcon("icons:save_as.svg"))
            save_action.triggered.connect(self.save_to_file)

        # Style
        f = QtCore.QFile(r"ui:stylesheet.qss")  # TODO not ideal, maybe a reduced qss?
        with open(f.fileName(), "r") as s:
            menu.setStyleSheet(s.read())

        # Exec
        menu.exec_(event.screenPos(), parent=self)

    # KEYBOARD EVENTS ----------------------
    def event(self, event: QtWidgets.QGraphicsScene.event):
        # Only use keyboard events
        if not (event.type() == QtCore.QEvent.KeyPress):
            return QtWidgets.QGraphicsScene.event(self, event)

        # See that we are not working on a node widget
        if self.focusItem():  # Means we are editing a widget in some input node
            return QtWidgets.QGraphicsScene.event(self, event)

        modifiers = QtWidgets.QApplication.keyboardModifiers()

        # --- Examine code
        if event.key() == QtCore.Qt.Key_E and not modifiers:
            self.examine_code(self.selected_nodes())

        # --- Execution
        elif event.key() == QtCore.Qt.Key_Return and not modifiers:
            self.run_nodes(self.selected_nodes())

        elif event.key() == QtCore.Qt.Key_R and not modifiers:
            self.reset_nodes(self.selected_nodes())

        # --- Toggle activation
        elif event.key() == QtCore.Qt.Key_D and not modifiers:
            self.toggle_activated_nodes(self.selected_nodes())

        # --- Context expansion
        elif (
            event.key() == QtCore.Qt.Key_Return
            and modifiers == QtCore.Qt.ControlModifier
        ):
            self.expand_contexts(self.selected_nodes())

        # --- Export code
        elif event.key() == QtCore.Qt.Key_E and modifiers == QtCore.Qt.ControlModifier:
            self.export_nodes_code(self.selected_nodes())

        # --- Soft-reset
        elif event.key() == QtCore.Qt.Key_S:
            self.soft_reset_nodes(self.selected_nodes())

        # --- Delete
        elif event.key() == QtCore.Qt.Key_Delete:
            for n in self.selected_nodes():
                GS.signals.attribute_editor_remove_node_requested.emit(
                    n.logic_node.uuid
                )
                self.delete_node(n)

            for a in self.selected_annotations():
                self.delete_annotation(a)

        # --- Fit in view
        elif event.key() == QtCore.Qt.Key_F:
            self.fit_in_view()

        # --- Class search
        elif event.key() == QtCore.Qt.Key_Tab and not modifiers:
            GS.signals.class_searcher_move.emit(
                QtGui.QCursor.pos().x(), QtGui.QCursor.pos().y()
            )

        return QtWidgets.QGraphicsScene.event(self, event)

    # MOUSE EVENTS ----------------------
    def mousePressEvent(self, event):
        QtWidgets.QGraphicsScene.mousePressEvent(
            self, event
        )  # TODO check if these have to go at the bottom and with return

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
                GS.signals.attribute_editor_node_addition_requested.emit(
                    item.logic_node.uuid
                )
                break

    def mouseMoveEvent(self, event):
        QtWidgets.QGraphicsScene.mouseMoveEvent(self, event)

        if self.testing_graphic_attr:
            self.testing_path.show()

            test_origin = self.testing_graphic_attr.plug_coords()

            p1 = test_origin
            p2 = event.scenePos()

            new_path = ConnectorLine.calculate_path(p1, p2)

            if new_path.length() > 7000:
                self.testing_path.hide()
            else:
                self.testing_path.show()

            self.testing_path.set_new_path(new_path)

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
                GS.signals.main_screen_feedback.emit(
                    "Those two attributes belong to the same node!",
                    logging.WARNING,
                )
        elif self.testing_graphic_attr and test_item is None:
            graphic_attr_1 = self.testing_graphic_attr
            if graphic_attr_1.connector_type == constants.INPUT:
                new_g_node = None
                if graphic_attr_1.logic_attribute.data_type is str:
                    new_g_node = self.add_graphic_node_by_class_name(
                        "StrInput", event_x, event_y
                    )
                    graphic_attr_2 = new_g_node["out_str"]
                    self.connect_graphic_attrs(graphic_attr_1, graphic_attr_2)
                elif graphic_attr_1.logic_attribute.data_type is list:
                    new_g_node = self.add_graphic_node_by_class_name(
                        "ListInput", event_x, event_y
                    )
                    graphic_attr_2 = new_g_node["out_list"]
                    self.connect_graphic_attrs(graphic_attr_1, graphic_attr_2)
                elif graphic_attr_1.logic_attribute.data_type is dict:
                    new_g_node = self.add_graphic_node_by_class_name(
                        "DictInput", event_x, event_y
                    )
                    graphic_attr_2 = new_g_node["out_dict"]
                    self.connect_graphic_attrs(graphic_attr_1, graphic_attr_2)
                elif graphic_attr_1.logic_attribute.data_type is int:
                    new_g_node = self.add_graphic_node_by_class_name(
                        "IntInput", event_x, event_y
                    )
                    graphic_attr_2 = new_g_node["out_int"]
                    self.connect_graphic_attrs(graphic_attr_1, graphic_attr_2)
                elif graphic_attr_1.logic_attribute.data_type is float:
                    new_g_node = self.add_graphic_node_by_class_name(
                        "FloatInput", event_x, event_y
                    )
                    graphic_attr_2 = new_g_node["out_float"]
                    self.connect_graphic_attrs(graphic_attr_1, graphic_attr_2)
                elif graphic_attr_1.logic_attribute.data_type is bool:
                    new_g_node = self.add_graphic_node_by_class_name(
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

        GS.signals.attribute_editor_global_refresh_requested.emit()

    # DRAG AND DROP EVENT ----------------------
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
        # TODO make sure this can only happen after GS emits signal of all classes scanned
        event_data = event.mimeData()
        if event_data.hasUrls():
            event_urls = event_data.urls()
            for url in event_urls:
                if os.path.isfile(url.toLocalFile()):
                    self.load_from_file(url.toLocalFile())
        else:
            GS.signals.dropped_node.emit(
                self.parent().mapFromScene(event.scenePos()) - QtCore.QPoint(20, 20)
            )
        QtWidgets.QGraphicsScene.dropEvent(self, event)
        event.acceptProposedAction()


# -------------------------------- HELPER CLASES -------------------------------- #
class ConnectorLine(QtWidgets.QGraphicsPathItem):
    def __init__(self, graphic_attr_1=None, graphic_attr_2=None):
        QtWidgets.QGraphicsPathItem.__init__(self)

        # Attributes to connect
        self.graphic_attr_1 = None
        self.graphic_attr_2 = None

        # Start and end
        self.p1 = QtCore.QPointF(0.0, 0.0)
        self.p2 = QtCore.QPointF(0.0, 0.0)

        # Items
        self.glow = QtWidgets.QGraphicsPathItem(parent=self)
        self.arrow_glow = QtWidgets.QGraphicsPathItem(parent=self)
        self.white_line = QtWidgets.QGraphicsPathItem(parent=self)
        self.arrow = QtWidgets.QGraphicsPathItem(parent=self)

        # Main path ---------------------
        if graphic_attr_1 is not None and graphic_attr_2 is not None:
            if graphic_attr_1.connector_type == constants.OUTPUT:
                self.graphic_attr_1 = graphic_attr_1
                self.graphic_attr_2 = graphic_attr_2
            else:
                self.graphic_attr_1 = graphic_attr_2
                self.graphic_attr_2 = graphic_attr_1

        self.repath()

        # Glow
        if constants.GLOW_EFFECTS:
            self.glow.setPen(constants.LINE_GLOW_PEN)
            blur = QtWidgets.QGraphicsBlurEffect()
            blur.setBlurRadius(constants.LINE_GLOW_PEN.width() * 1.5)
            self.glow.setGraphicsEffect(blur)
        else:
            self.glow.hide()

        # White line
        self.white_line.setPen(constants.VALID_LINE_PEN)

        # Arrow ---------------------
        arrow_path = QtGui.QPainterPath()
        arrow_polygon = QtGui.QPolygon(
            [
                QtCore.QPoint(constants.PLUG_RADIUS * 1.3, 0),
                QtCore.QPoint(
                    -constants.PLUG_RADIUS * 1.3, constants.PLUG_RADIUS * 1.3
                ),
                QtCore.QPoint(-constants.PLUG_RADIUS * 0.9, 0),
                QtCore.QPoint(
                    -constants.PLUG_RADIUS * 1.3, -constants.PLUG_RADIUS * 1.3
                ),
            ]
        )
        arrow_path.addPolygon(arrow_polygon)
        arrow_path.closeSubpath()

        # Arrow glow
        if constants.GLOW_EFFECTS:
            self.arrow_glow.setPath(arrow_path)
            self.arrow_glow.setPen(constants.LINE_GLOW_PEN)
            blur = QtWidgets.QGraphicsBlurEffect()
            blur.setBlurRadius(constants.LINE_GLOW_PEN.width() * 1.5)
            self.arrow_glow.setGraphicsEffect(blur)
        else:
            self.arrow_glow.hide()

        # Arrow
        self.arrow.setPath(arrow_path)
        self.arrow.setPen(QtCore.Qt.NoPen)
        self.arrow.setBrush(QtGui.QBrush(constants.VALID_LINE_PEN.color()))

        self.rotate_arrows()

        # Data ---------------------
        self.setData(0, constants.CONNECTOR_LINE)
        # TODO split this data into attrs
        self.setData(1, graphic_attr_1)
        self.setData(2, graphic_attr_2)

    @staticmethod
    def calculate_path(p1, p2):
        new_path = QtGui.QPainterPath(p1)
        if constants.CONNECTOR_LINE_GEO == constants.STRAIGHT_LINES:
            new_path.lineTo(p2)
        elif constants.CONNECTOR_LINE_GEO == constants.STEPPED_LINES:
            s_p1 = QtCore.QPointF(((p2.x() + p1.x()) / 2), p1.y())
            s_p2 = QtCore.QPointF(((p2.x() + p1.x()) / 2), p2.y())
            new_path.lineTo(s_p1)
            new_path.lineTo(s_p2)
            new_path.lineTo(p2)
        elif constants.CONNECTOR_LINE_GEO == constants.SPLINE_LINES:
            c_p1 = QtCore.QPoint(((p2.x() + p1.x()) / 2) + 10, p1.y())
            c_p2 = QtCore.QPoint(((p2.x() + p1.x()) / 2) - 10, p2.y())
            new_path.cubicTo(c_p1, c_p2, p2)

        return new_path

    def repath(self):
        if self.graphic_attr_1 is None or self.graphic_attr_2 is None:
            return

        p1, p2 = (
            self.graphic_attr_1.plug_coords(),
            self.graphic_attr_2.plug_coords(),
        )

        self.set_new_path(self.calculate_path(p1, p2))
        self.rotate_arrows()

    def rotate_arrows(self):
        if self.graphic_attr_1 and self.graphic_attr_2:
            p1, p2 = self.path().pointAtPercent(0.0), self.path().pointAtPercent(1.0)
            self.arrow_glow.setPos((p2.x() + p1.x()) / 2, (p2.y() + p1.y()) / 2)
            self.arrow.setPos((p2.x() + p1.x()) / 2, (p2.y() + p1.y()) / 2)
            ref_1 = self.path().pointAtPercent(0.49)
            ref_2 = self.path().pointAtPercent(0.51)
            radians = math.atan2(ref_2.y() - ref_1.y(), ref_2.x() - ref_1.x())
            angle = math.degrees(radians)

            self.arrow_glow.setRotation(angle)
            self.arrow.setRotation(angle)

    def set_testing_appearance(self):
        self.white_line.setPen(constants.TEST_LINE_PEN)
        self.arrow_glow.hide()
        self.arrow.hide()

    def set_new_path(self, new_path):
        self.setPath(new_path)
        self.white_line.setPath(new_path)
        self.glow.setPath(new_path)
