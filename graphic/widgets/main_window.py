# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import os
from functools import partial

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtUiTools
from PySide2 import QtWidgets

from all_nodes import constants
from all_nodes.graphic import graphic_scene
from all_nodes.graphic.widgets.attribute_editor import AttributeEditor
from all_nodes.graphic.widgets.global_signaler import GLOBAL_SIGNALER as GS
from all_nodes.logic import ALL_CLASSES, ALL_SCENES
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class AllNodesWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        # Load UI
        root = os.path.abspath(__file__)
        root_dir_path = os.path.dirname(os.path.dirname(os.path.dirname(root)))
        file = QtCore.QFile(os.path.join(root_dir_path, "graphic/ui/all_nodes.ui"))
        file.open(QtCore.QFile.ReadOnly)
        loader = QtUiTools.QUiLoader()
        self.ui = loader.load(file, self)
        self.setCentralWidget(self.ui)

        # Dock
        self.dock = QtWidgets.QDockWidget()
        self.dock.setWindowTitle("Attribute Editor")
        self.attr_editor = AttributeEditor()
        self.dock.setWidget(self.attr_editor)

        # STYLE
        self.setMinimumWidth(850)
        self.setMinimumHeight(500)
        self.resize(1550, 850)
        self.setWindowTitle("ALL NODES")
        self.setWindowIcon(QtGui.QIcon("icons:nodes_2.png"))

        # FEEDBACK
        self.the_process_window = QtWidgets.QTextEdit()
        self.the_process_window.setReadOnly(True)
        self.the_process_window.setWindowTitle("Execution feedback")

        # MENU
        self.create_menus()

        # ELEMENTS OF THE UI
        self.ui.nodes_tree.setMinimumWidth(260)
        self.ui.nodes_tree.setDragEnabled(True)

        self.add_scene()

        self.ui.reset_current_btn.setIcon(QtGui.QIcon("icons:reset.png"))
        self.ui.run_current_btn.setIcon(QtGui.QIcon("icons:brain.png"))

        # STYLESHEET
        f = QtCore.QFile(r"ui:stylesheet.qss")
        with open(f.fileName(), "r") as s:
            self.setStyleSheet(s.read())

        # SET CONNECTIONS
        self.make_connections()

        # INITIALIZE
        self.populate_tree()
        self.create_dock_windows()
        self.show()

    def make_connections(self):
        """
        Establish all connections between widget signals and methods.
        """
        # UI elements
        self.ui.reset_current_btn.clicked.connect(self.reset_current_scene)
        self.ui.run_current_btn.clicked.connect(self.run_current_scene)
        self.ui.filter_le.textChanged.connect(self.filter_nodes_by_name)
        self.ui.tabWidget.currentChanged.connect(self.attr_editor.clear_all)
        self.ui.tabWidget.currentChanged.connect(self.show_scene_results)

        # Global signaler
        GS.tab_names_refresh_requested.connect(self.refresh_tab_names)

        GS.attribute_editor_node_addition_requested.connect(
            self.add_node_to_attribute_editor_by_uuid
        )
        GS.attribute_editor_refresh_node_requested.connect(
            self.refresh_node_in_attribute_editor_by_uuid
        )
        GS.attribute_editor_remove_node_requested.connect(
            self.remove_node_in_attribute_editor_by_uuid
        )

        GS.context_expansion_requested.connect(self.expand_context)

        GS.attribute_editor_global_refresh_requested.connect(self.attr_editor.refresh)

    # UI SETUP ----------------------
    def create_menus(self):
        """
        Create and populate menu bar.
        """

        def add_scenes_recursive(entries_dict: dict, menu: QtWidgets.QMenu):
            """
            Navigate a dict with multiple levels and add scenes to the menu accordingly.

            Args:
                entries_dict (dict): containing the scenes to be added
                menu (QtWidgets.QMenu): menu to add entries to
            """
            menu.setToolTipsVisible(True)
            for key in entries_dict:
                nice_name = key.capitalize().replace("_", " ")
                libs_menu = menu.addMenu(nice_name)
                libs_menu.setIcon(QtGui.QIcon("icons:folder.png"))
                scenes_list = entries_dict[key]
                for elem in scenes_list:
                    if isinstance(elem, dict):
                        add_scenes_recursive(elem, libs_menu)
                for elem in scenes_list:
                    if isinstance(elem, tuple):
                        scene_name, full_path = elem
                        nice_name = scene_name.capitalize().replace("_", " ")
                        ac = QtWidgets.QAction(nice_name, parent=menu)
                        ac.setToolTip(full_path)
                        ac.triggered.connect(partial(self.load_scene, full_path))
                        ac.setIcon(QtGui.QIcon("icons:scene.png"))
                        libs_menu.addAction(ac)

        menu = self.menuBar()

        file_menu = menu.addMenu("&File")
        save_scene_action = QtWidgets.QAction("Save current scene", self)
        save_scene_action.setIcon(QtGui.QIcon("icons:save.png"))
        save_scene_action.triggered.connect(self.save_scene)
        file_menu.addAction(save_scene_action)
        load_scene_action = QtWidgets.QAction("Load scene from file", self)
        load_scene_action.setIcon(QtGui.QIcon("icons:load.png"))
        load_scene_action.triggered.connect(self.load_scene)
        file_menu.addAction(load_scene_action)

        scene_menu = menu.addMenu("&Scene")
        add_scenes_recursive(ALL_SCENES, scene_menu)

        window_menu = menu.addMenu("&Window")
        show_attr_editor = QtWidgets.QAction("Show attribute editor", self)
        show_attr_editor.setIcon(QtGui.QIcon("icons:eye.png"))
        show_attr_editor.triggered.connect(self.dock.show)
        window_menu.addAction(show_attr_editor)

    def create_dock_windows(self):
        self.dock.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
        )
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock)

    def populate_tree(self):
        """
        Populate the tree where all nodes are displayed.
        """
        top_level_items = {}
        for m in sorted(ALL_CLASSES):
            node_lib_path = ALL_CLASSES[m]["node_lib_path"]
            node_lib_name = ALL_CLASSES[m]["node_lib_name"]
            node_lib_nice_name = node_lib_name.capitalize().replace("_", " ")
            module_filename = ALL_CLASSES[m]["module_filename"]
            module_nice_name = m.capitalize().replace("_", " ")
            color = ALL_CLASSES[m].get("color", constants.DEFAULT_NODE_COLOR)

            if node_lib_name not in top_level_items:
                lib_item = QtWidgets.QTreeWidgetItem()
                lib_item.setText(0, node_lib_nice_name)
                lib_item.setToolTip(0, "Lib: {}".format(node_lib_path))
                top_level_items[node_lib_name] = lib_item
            else:
                lib_item = top_level_items[node_lib_name]

            module_item = QtWidgets.QTreeWidgetItem()
            module_item.setText(0, module_nice_name)
            module_item.setToolTip(0, "Module: {}".format(module_filename))

            for name, cls in ALL_CLASSES[m]["classes"]:
                class_item = QtWidgets.QTreeWidgetItem()
                class_item.setText(0, name)
                class_item.setToolTip(
                    0, "Class: {}, from {}".format(name, module_filename)
                )
                class_item.setData(0, QtCore.Qt.UserRole, name)
                if cls.NICE_NAME:
                    class_item.setText(0, cls.NICE_NAME)

                icon = QtGui.QIcon(cls.ICON_PATH)
                class_item.setIcon(0, icon)
                item_color = QtGui.QColor(color)
                item_color.setAlphaF(0.25)
                class_item.setBackgroundColor(0, item_color)
                module_item.addChild(class_item)

            module_item_color = QtGui.QColor(color)
            module_item_color.setAlphaF(0.4)
            module_item.setBackgroundColor(0, module_item_color)

            lib_item.addChild(module_item)

        for t in top_level_items:
            lib_item = top_level_items[t]
            self.ui.nodes_tree.addTopLevelItem(lib_item)
            lib_item.setExpanded(True)
            lib_item.setFont(0, QtGui.QFont("arial", 16))
            for i in range(lib_item.childCount()):
                node_file_item = lib_item.child(i)
                node_file_item.setExpanded(True)
                node_file_item.setFont(0, QtGui.QFont("arial", 14))
                for i in range(node_file_item.childCount()):
                    node_class = node_file_item.child(i)
                    node_class.setFont(0, QtGui.QFont("arial", 14))

    def filter_nodes_by_name(self):
        """
        Set node classes as hidden/visible based on user input.
        """
        filter = self.ui.filter_le.text().lower()
        for i in range(self.ui.nodes_tree.topLevelItemCount()):
            lib_item = self.ui.nodes_tree.topLevelItem(i)
            lib_visible_count = 0
            lib_item.setHidden(False)
            for m_i in range(lib_item.childCount()):
                module_item = lib_item.child(m_i)
                module_visible_count = 0
                module_item.setHidden(False)
                for c_i in range(module_item.childCount()):
                    class_item = module_item.child(c_i)
                    if filter and filter not in class_item.text(0).lower():
                        class_item.setHidden(True)
                    else:
                        class_item.setHidden(False)
                        lib_visible_count += 1
                        module_visible_count += 1
                if not module_visible_count:
                    module_item.setHidden(True)
            if not lib_visible_count:
                lib_item.setHidden(True)

    # TABS ----------------------
    def add_scene(self, context=None):
        """
        Add a new graphic scene to the widget (in a new tab).

        If a context is supplied, build its internals onto the new scene.

        Args:
            context (GeneralLogicNode): optional, context node from which to build the scene
        """
        scene_name = "ROOT"
        if context:
            scene_name = context.full_name

        graphics_view = graphic_scene.CustomGraphicsView()
        graphics_scene = graphic_scene.CustomScene(context)
        graphics_view.setScene(graphics_scene)

        graphics_scene.setSceneRect(-20000, -20000, 40000, 40000)
        graphics_scene.setParent(graphics_view)
        graphics_scene.dropped_node.connect(self.add_node_to_current)
        graphics_scene.in_screen_feedback.connect(graphics_view.show_feedback)

        if context:
            graphics_scene.load_from_file(context.CONTEXT_DEFINITION_FILE, False)

        self.ui.tabWidget.addTab(graphics_view, scene_name)
        self.ui.tabWidget.setCurrentIndex(self.ui.tabWidget.count() - 1)

    def expand_context(self, uuid):
        """
        Expand the contents of a context node into a new tab.

        Args:
            uuid (str): of the node to try to expand
        """
        n = self.get_node_by_uuid(uuid)

        # See if the context is already expanded
        for i in range(self.ui.tabWidget.count()):
            gw = self.ui.tabWidget.widget(i)
            logic_scene = gw.scene().logic_scene
            if logic_scene.context and logic_scene.context == n:
                self.ui.tabWidget.setCurrentIndex(i)
                return

        # Otherwise, expand it
        self.add_scene(n)
        current_gw = self.ui.tabWidget.widget(self.ui.tabWidget.currentIndex())
        current_scene = current_gw.scene()
        current_scene.fit_in_view()

    def refresh_tab_names(self):
        """
        Refresh the names of all tabs, to make sure they show the names they have to.
        """
        for i in range(self.ui.tabWidget.count()):
            gw = self.ui.tabWidget.widget(i)
            logic_scene = gw.scene().logic_scene
            if logic_scene.context:
                self.ui.tabWidget.setTabText(i, logic_scene.context.full_name)
                return

    # NODE UTILITY ----------------------
    def get_node_by_uuid(self, uuid):
        """
        Given a uuid, find a logic node.

        Args:
            uuid (str): of the node to find

        Returns:
            GeneralLogicNode: logic node associated to the uuid

        """
        current_gw = self.ui.tabWidget.widget(self.ui.tabWidget.currentIndex())
        current_logic_scene = current_gw.scene().logic_scene
        for n in current_logic_scene.all_nodes():
            if n.uuid == uuid:
                return n

    def add_node_to_current(self, x, y):
        """
        Add a new node to the current graphic scene.

        Args:
            x (int): horizontal coord t add the node to
            y (int): vertical coord t add the node to
        """
        current_gw = self.ui.tabWidget.widget(self.ui.tabWidget.currentIndex())
        current_scene = current_gw.scene()
        selected = self.ui.nodes_tree.selectedItems()[0]
        node_type = str(selected.data(0, QtCore.Qt.UserRole)).strip()
        current_scene.add_graphic_node_by_name(node_type, x, y)

    # ATTRIBUTE EDITOR ----------------------
    def refresh_node_in_attribute_editor_by_uuid(self, uuid):
        """
        Refresh a given node's representation in the attribute editor panel.

        Args:
            uuid (str): of the node to be refreshed
        """
        n = self.get_node_by_uuid(uuid)
        self.attr_editor.refresh_node_panel(n)

    def remove_node_in_attribute_editor_by_uuid(self, uuid):
        """
        Remove a given node's representation from the attribute editor panel.

        Args:
            uuid (str): of the node to be removed
        """
        n = self.get_node_by_uuid(uuid)
        self.attr_editor.remove_node_panel(n)

    def add_node_to_attribute_editor_by_uuid(self, uuid):
        """
        Add a given node's representation to the attribute editor panel.

        Args:
            uuid (str): of the node to be added
        """
        n = self.get_node_by_uuid(uuid)
        self.attr_editor.add_node_panel(n)

    # SAVE AND LOAD ----------------------
    def save_scene(self):
        """
        Launch process of saving current scene to a file.
        """
        current_gw = self.ui.tabWidget.widget(self.ui.tabWidget.currentIndex())
        current_scene = current_gw.scene()
        current_scene.save_to_file()

    def load_scene(self, source_file):
        """
        Launch the process of loading a file onto a new tab.

        Args:
            source_file (str): path of the scene to load
        """
        # Filepath
        if not source_file:
            dialog = QtWidgets.QFileDialog()
            result = dialog.getOpenFileName(
                caption="Specify source file", filter="*.yml"
            )
            if not result[0] or not result[1]:
                return
            source_file = result[0]

        # Add scene and load
        self.add_scene()
        current_gw = self.ui.tabWidget.widget(self.ui.tabWidget.currentIndex())
        current_scene = current_gw.scene()
        current_scene.load_from_file(source_file)
        current_scene.fit_in_view()
        self.ui.tabWidget.setTabText(
            self.ui.tabWidget.currentIndex(),
            os.path.splitext(os.path.basename(source_file))[0],
        )

    # SCENE EXECUTION ----------------------
    def run_current_scene(self):
        """
        Execute the graphic scene currently selected.
        """
        current_gw = self.ui.tabWidget.widget(self.ui.tabWidget.currentIndex())
        current_scene = current_gw.scene()
        current_scene.run_graphic_scene()
        self.attr_editor.refresh()

    def reset_current_scene(self):
        """
        Reset the graphic scene currently selected.
        """
        current_gw = self.ui.tabWidget.widget(self.ui.tabWidget.currentIndex())
        current_scene = current_gw.scene()
        current_scene.reset_graphic_scene()
        self.attr_editor.refresh()

    def show_scene_results(self):
        """
        Display execution results on the nodes of the graphic scene currently selected.
        """
        current_gw = self.ui.tabWidget.widget(self.ui.tabWidget.currentIndex())
        current_scene = current_gw.scene()
        current_scene.show_result_on_nodes()
