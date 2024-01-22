# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import logging
import math
import os
import pprint
import subprocess

from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui
import yaml

from all_nodes import constants
from all_nodes.graphic.graphic_node import GeneralGraphicNode, GeneralGraphicAttribute
from all_nodes.logic.class_registry import CLASS_REGISTRY as CR
from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes.logic.logic_scene import LogicScene
from all_nodes import utils
from all_nodes.graphic.widgets.class_searcher import ClassSearcher
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

        self.drag_pos = None
        self.middle_pressed = False
        self.left_pressed = False

        self.feedback_line = QtWidgets.QLineEdit(parent=self)
        self.feedback_line.setReadOnly(True)
        self.feedback_line.setFont(QtGui.QFont("arial", 12))
        self.feedback_line.hide()

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
        GS.class_searcher_move.connect(self.move_search_bar)

        self.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)

        # Signals connection
        GS.execution_started.connect(self.hourglass_animation.show)
        GS.execution_finished.connect(self.hourglass_animation.hide)

    # UTILITY ----------------------
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
        QtWidgets.QGraphicsView.resizeEvent(self, event)
        self.feedback_line.move(25, self.height() - 50)
        self.feedback_line.setFixedSize(self.width(), 30)

        self.hourglass_animation.move(self.width() - 200, self.height() - 200)
        self.hourglass_animation.setFixedSize(200, 200)
        self.movie.setScaledSize(QtCore.QSize(200, 200))

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
    # TODO rethink if these could go in the GLOBAL_SIGNALER
    dropped_node = QtCore.Signal(QtCore.QPoint)
    in_screen_feedback = QtCore.Signal(str, int)

    def __init__(self, context=None):
        QtWidgets.QGraphicsScene.__init__(self)

        # Logic scene
        self.logic_scene = context.internal_scene if context else LogicScene()
        self.filepath = context.CONTEXT_DEFINITION_FILE if context else None

        # Nodes
        self.all_graphic_nodes = set()

        # PATH TESTS
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
            GeneralGraphicNode: newly create node
        """
        all_classes = CR.get_all_classes()
        for m in sorted(all_classes):
            color = all_classes[m]["color"]
            for name, _ in all_classes[m]["classes"]:
                if node_classname == name:
                    new_logic_node = self.logic_scene.add_node_by_name(node_classname)
                    new_graph_node = GeneralGraphicNode(new_logic_node, color)
                    self.addItem(new_graph_node)
                    self.all_graphic_nodes.add(new_graph_node)
                    new_graph_node.setPos(x, y)
                    self.in_screen_feedback.emit(
                        "Created graphic node {}".format(node_classname), logging.INFO
                    )
                    return new_graph_node

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
        for m in sorted(all_classes):
            color = all_classes[m]["color"]
            for name, cls in all_classes[m]["classes"]:
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
            if c.data(0) == "GRAPHIC_ATTRIBUTE" and c.parent_node == node
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
        GS.attribute_editor_global_refresh_requested.emit()

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
        )
        if ok and new_name:
            if self.logic_scene.rename_node(logic_node, new_name):
                graphic_node.update_name()
                GS.attribute_editor_refresh_node_requested.emit(logic_node.uuid)
                GS.tab_names_refresh_requested.emit()
            else:
                if logic_node.node_name == new_name:
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

        If the node is a context, show its .yml definition file as well.

        Args:
            graphic_node (GeneralGraphicNode): node to examine code from
        """
        logic_node = graphic_node.logic_node
        try:
            subprocess.Popen(["notepad", logic_node.FILEPATH])
            if logic_node.IS_CONTEXT:
                subprocess.Popen(["notepad", logic_node.CONTEXT_DEFINITION_FILE])
        except Exception as e:
            msg = "Could not open the code in editor: {}".format(e)
            LOGGER.error(msg)
            self.in_screen_feedback.emit(msg, logging.ERROR)

    def expand_context(self, graphic_node: GeneralGraphicNode):
        """
        Launch signal to expand a selected context node.

        Args:
            graphic_node (GeneralGraphicNode): node to be expanded
        """
        GS.context_expansion_requested.emit(graphic_node.logic_node.uuid)

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

    def run_single_node(self, graphic_node: GeneralGraphicNode):
        """
        Execute a graphic node.

        Args:
            graphic_node (GeneralGraphicNode): node to execute
        """
        logic_node = graphic_node.logic_node
        self.in_screen_feedback.emit("Running only selected node(s)", logging.INFO)
        GS.execution_started.emit()
        self.logic_scene.run_list_of_nodes([logic_node])

    def reset_single_node(self, graphic_node: GeneralGraphicNode):
        """
        Reset appearance of a graphic node and then also reset its
        internal logic node.

        Args:
            graphic_node (GeneralGraphicNode): node to reset
        """
        graphic_node.reset()
        graphic_node.logic_node.reset()
        self.in_screen_feedback.emit("Resetting selected node(s)", logging.INFO)
        GS.attribute_editor_global_refresh_requested.emit()

    def soft_reset_single_node(self, graphic_node: GeneralGraphicNode):
        """
        Reset appearance of a graphic node and then also soft-reset its
        internal logic node.

        Args:
            graphic_node (GeneralGraphicNode): node to soft-reset
        """
        graphic_node.reset()
        graphic_node.logic_node.soft_reset()
        self.in_screen_feedback.emit("Soft-resetting selected node(s)", logging.INFO)
        GS.attribute_editor_global_refresh_requested.emit()

    def deselect_all(self):
        """
        Deselect all graphic nodes.
        """
        for n in self.all_graphic_nodes:
            n.setSelected(False)

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
        GS.attribute_editor_global_refresh_requested.emit()

    def run_graphic_scene(self):
        """
        Run all the nodes in this graphic scene.
        """
        GS.execution_started.emit()
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

    def fit_in_view(self):
        """
        If selected nodes, fit all of them in the view. Otherwise, fit all nodes.
        """
        self.parent().resetMatrix()
        nodes = list(self.all_graphic_nodes)
        if self.selected_nodes():
            nodes = self.selected_nodes()
        if not nodes:
            return
        rect = nodes[0].sceneBoundingRect()
        for n in nodes:
            rect = rect.united(n.sceneBoundingRect())

        self.parent().fitInView(rect, QtCore.Qt.KeepAspectRatio)

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
        else:
            self.menu_scene(event)

        QtWidgets.QGraphicsScene.contextMenuEvent(self, event)

    def menu_node(self, event, node):
        menu = QtWidgets.QMenu()  # TODO add tooltips

        # Common actions
        rename_action = menu.addAction(" Rename this node")
        rename_action.setIcon(QtGui.QIcon("icons:rename.png"))
        rename_action.triggered.connect(lambda: self.rename_graphic_node(node))
        examine_code_action = menu.addAction(" Examine code (E)")
        examine_code_action.setIcon(QtGui.QIcon("icons:examine.png"))
        examine_code_action.triggered.connect(lambda: self.examine_code(node))
        run_single_node_action = menu.addAction(" Run only this node (Return ⏎)")
        run_single_node_action.setIcon(QtGui.QIcon("icons:run_one.svg"))
        run_single_node_action.triggered.connect(lambda: self.run_single_node(node))
        reset_single_node_action = menu.addAction(" Reset only this node (R)")
        reset_single_node_action.setIcon(QtGui.QIcon("icons:reset.png"))
        reset_single_node_action.triggered.connect(lambda: self.reset_single_node(node))

        # Context-specific
        if node.logic_node.IS_CONTEXT:
            menu.addSeparator()
            expand_context_action = menu.addAction(" Expand context (Ctrl + Return ⏎)")
            expand_context_action.setIcon(QtGui.QIcon("icons:cube.png"))
            expand_context_action.triggered.connect(lambda: self.expand_context(node))

        # Debug
        menu.addSeparator()
        soft_reset_single_node_action = menu.addAction(
            " [DEBUG] Soft-reset only this node (S)"
        )
        soft_reset_single_node_action.setIcon(QtGui.QIcon("icons:reset.png"))
        soft_reset_single_node_action.triggered.connect(
            lambda: self.soft_reset_single_node(node)
        )

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
            save_action.setIcon(QtGui.QIcon("icons:save.png"))
            save_action.triggered.connect(lambda: self.save_to_file(self.filepath))
        else:
            save_action = menu.addAction(" Save scene as")
            save_action.setIcon(QtGui.QIcon("icons:save.png"))
            save_action.triggered.connect(self.save_to_file)

        # Style
        f = QtCore.QFile(r"ui:stylesheet.qss")  # TODO not ideal, maybe a reduced qss?
        with open(f.fileName(), "r") as s:
            menu.setStyleSheet(s.read())

        # Exec
        menu.exec_(event.screenPos(), parent=self)

    # KEYBOARD EVENTS ----------------------
    def keyPressEvent(self, event: QtWidgets.QGraphicsScene.event):
        QtWidgets.QGraphicsScene.keyPressEvent(self, event)

        modifiers = QtWidgets.QApplication.keyboardModifiers()

        if self.focusItem():  # Means we are editing a widget in some input node
            return

        if event.key() == QtCore.Qt.Key_Delete:
            for n in self.selected_nodes():
                GS.attribute_editor_remove_node_requested.emit(n.logic_node.uuid)
                self.delete_node(n)
        elif event.key() == QtCore.Qt.Key_F:
            self.fit_in_view()
        elif event.key() == QtCore.Qt.Key_Return and not modifiers:
            for n in self.selected_nodes():
                self.run_single_node(n)
        elif event.key() == QtCore.Qt.Key_R:
            for n in self.selected_nodes():
                self.reset_single_node(n)
        elif event.key() == QtCore.Qt.Key_S:
            for n in self.selected_nodes():
                self.soft_reset_single_node(n)
        elif event.key() == QtCore.Qt.Key_E:
            for n in self.selected_nodes():
                self.examine_code(n)
        elif (
            event.key() == QtCore.Qt.Key_Return
            and modifiers == QtCore.Qt.ControlModifier
        ):
            for n in self.selected_nodes():
                self.expand_context(n)
        elif event.key() == QtCore.Qt.Key_Slash and not modifiers:
            GS.class_searcher_move.emit(
                QtGui.QCursor.pos().x(), QtGui.QCursor.pos().y()
            )

    # MOUSE EVENTS ----------------------
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
                self.in_screen_feedback.emit(
                    "Those two attributes belong to the same node!",
                    logging.WARNING,
                )
        elif self.testing_graphic_attr and test_item is None:
            graphic_attr_1 = self.testing_graphic_attr
            if graphic_attr_1.connector_type == constants.INPUT:
                new_g_node = None
                if graphic_attr_1.logic_attribute.data_type == str:
                    new_g_node = self.add_graphic_node_by_class_name(
                        "StrInput", event_x, event_y
                    )
                    graphic_attr_2 = new_g_node["out_str"]
                    self.connect_graphic_attrs(graphic_attr_1, graphic_attr_2)
                elif graphic_attr_1.logic_attribute.data_type == list:
                    new_g_node = self.add_graphic_node_by_class_name(
                        "ListInput", event_x, event_y
                    )
                    graphic_attr_2 = new_g_node["out_list"]
                    self.connect_graphic_attrs(graphic_attr_1, graphic_attr_2)
                elif graphic_attr_1.logic_attribute.data_type == dict:
                    new_g_node = self.add_graphic_node_by_class_name(
                        "DictInput", event_x, event_y
                    )
                    graphic_attr_2 = new_g_node["out_dict"]
                    self.connect_graphic_attrs(graphic_attr_1, graphic_attr_2)
                elif graphic_attr_1.logic_attribute.data_type == int:
                    new_g_node = self.add_graphic_node_by_class_name(
                        "IntInput", event_x, event_y
                    )
                    graphic_attr_2 = new_g_node["out_int"]
                    self.connect_graphic_attrs(graphic_attr_1, graphic_attr_2)
                elif graphic_attr_1.logic_attribute.data_type == float:
                    new_g_node = self.add_graphic_node_by_class_name(
                        "FloatInput", event_x, event_y
                    )
                    graphic_attr_2 = new_g_node["out_float"]
                    self.connect_graphic_attrs(graphic_attr_1, graphic_attr_2)
                elif graphic_attr_1.logic_attribute.data_type == bool:
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

        GS.attribute_editor_global_refresh_requested.emit()

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
        event_data = event.mimeData()
        if event_data.hasUrls():
            event_urls = event_data.urls()
            for url in event_urls:
                if os.path.isfile(url.toLocalFile()):
                    self.load_from_file(url.toLocalFile())
        else:
            self.dropped_node.emit(
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
