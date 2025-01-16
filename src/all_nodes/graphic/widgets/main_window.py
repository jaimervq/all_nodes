# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import os
from functools import partial
from pathlib import Path


from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtUiTools
from PySide2 import QtWidgets

from all_nodes import constants
from all_nodes.graphic import graphic_scene
from all_nodes.graphic.widgets.attribute_editor import AttributeEditor
from all_nodes.graphic.widgets.global_signaler import GlobalSignaler
from all_nodes.graphic.widgets.shortcuts_help import ShortcutsHelp
from all_nodes.logic.class_registry import CLASS_REGISTRY as CR
from all_nodes import utils


GS = GlobalSignaler()

LOGGER = utils.get_logger(__name__)


class AllNodesWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        # CLASSES SCANNING
        self.libraries_added = set()

        # Add search paths
        root_dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        QtCore.QDir.addSearchPath("icons", os.path.join(root_dir_path, "general_icons"))
        QtCore.QDir.addSearchPath(
            "graphics", os.path.join(root_dir_path, "general_graphics")
        )
        QtCore.QDir.addSearchPath("ui", os.path.join(root_dir_path, "ui"))
        QtCore.QDir.addSearchPath(
            "resources", os.path.join(root_dir_path, "../logic/resources")
        )

        # Load UI
        file = QtCore.QFile(r"ui:all_nodes.ui")
        file.open(QtCore.QFile.ReadOnly)
        loader = QtUiTools.QUiLoader()
        self.ui = loader.load(file, self)
        self.setCentralWidget(self.ui)

        # Dock
        self.attr_editr_dock = QtWidgets.QDockWidget()
        self.attr_editr_dock.setWindowTitle("Attribute Editor")
        self.attr_editor = AttributeEditor()
        self.attr_editr_dock.setWidget(self.attr_editor)

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

        # ELEMENTS OF THE UI
        self.ui.nodes_tree.setMinimumWidth(300)
        self.ui.nodes_tree.setDragEnabled(True)
        self.ui.annotations_tree.setDragEnabled(True)

        self.ui.splitter_libs.setStretchFactor(0, 8)
        self.ui.splitter_libs.setStretchFactor(1, 2)

        self.add_scene()
        self.create_dock_windows()

        # STYLESHEET
        f = QtCore.QFile(r"ui:stylesheet.qss")
        with open(f.fileName(), "r") as s:
            self.setStyleSheet(s.read())

        # SET CONNECTIONS
        self.make_connections()

        # INITIALIZE
        self.show()
        LOGGER.debug("all_nodes main window created")

        # MENUS
        self.create_menus()

        # INITIAL STATE OF WIDGETS (while scanning for classes)
        # We dont want the user to load any scene until the scanning is done, so we deactivate the menubar
        self.menuBar().setDisabled(True)

    def make_connections(self):
        """
        Establish all connections between widget signals and methods.
        """
        # UI elements
        self.ui.filter_le.textChanged.connect(self.filter_nodes_by_name)

        self.ui.tabWidget.currentChanged.connect(self.show_scene_results)

        self.ui.nodes_tree.itemEntered.connect(self.ui.annotations_tree.clearSelection)
        self.ui.annotations_tree.itemEntered.connect(self.ui.nodes_tree.clearSelection)

        # Classes scanning / populating
        for worker in CR.get_workers():
            worker.signaler.finished.connect(self.populate_tree)

        GS.signals.class_scanning_finished.connect(
            lambda: self.menuBar().setEnabled(True)
        )

        GS.signals.class_scanning_finished.connect(self.populate_annotations)

        # Global signaler
        GS.signals.dropped_node.connect(self.add_node_to_current)
        GS.signals.node_creation_requested.connect(self.add_node_to_current)

        GS.signals.tab_names_refresh_requested.connect(self.refresh_tab_names)

        GS.signals.attribute_editor_node_addition_requested.connect(
            self.add_node_to_attribute_editor_by_uuid
        )
        GS.signals.attribute_editor_refresh_node_requested.connect(
            self.refresh_node_in_attribute_editor_by_uuid
        )
        GS.signals.attribute_editor_remove_node_requested.connect(
            self.remove_node_in_attribute_editor_by_uuid
        )

        GS.signals.context_expansion_requested.connect(self.expand_context)

        GS.signals.attribute_editor_global_refresh_requested.connect(
            self.attr_editor.refresh
        )

    # UI SETUP ----------------------
    def create_menus(self):
        """
        Create and populate menu bar.
        """
        all_scenes = CR.get_all_scenes()

        def add_scenes_recursive(entries_dict: dict, menu: QtWidgets.QMenu):
            """
            Navigate a dict with multiple levels and add scenes to the menu accordingly.

            Args:
                entries_dict (dict): containing the scenes to be added
                menu (QtWidgets.QMenu): menu to add entries to
            """
            menu.setToolTipsVisible(True)
            for key in entries_dict:
                nice_name = key.replace("scene_lib", "").title().replace("_", " ")
                libs_menu = menu.addMenu(nice_name)
                libs_menu.setIcon(QtGui.QIcon("icons:folder.svg"))
                libs_menu.setToolTipsVisible(True)
                scenes_list = entries_dict[key]
                for elem in scenes_list:
                    if isinstance(elem, dict):
                        add_scenes_recursive(elem, libs_menu)
                for elem in scenes_list:
                    if isinstance(elem, tuple):
                        scene_name, full_path = elem
                        nice_name = scene_name.title().replace("_", " ")
                        ac = QtWidgets.QAction(nice_name, parent=menu)
                        ac.setToolTip(full_path)
                        ac.triggered.connect(partial(self.load_scene, full_path))
                        ac.setIcon(QtGui.QIcon("icons:scene.png"))
                        libs_menu.addAction(ac)

        menu = self.menuBar()

        file_menu = menu.addMenu("&File")
        new_scene_action = QtWidgets.QAction("Clear workspace", self)
        new_scene_action.setIcon(
            QtGui.QIcon("icons:clear.png")
        )  # TODO investigate if extensions can be removed
        new_scene_action.triggered.connect(self.clear_workspace)
        file_menu.addAction(new_scene_action)
        save_scene_action = QtWidgets.QAction("Save current scene as", self)
        save_scene_action.setIcon(QtGui.QIcon("icons:save_as.svg"))
        save_scene_action.triggered.connect(self.save_scene_as)
        file_menu.addAction(save_scene_action)
        save_scene_changes_action = QtWidgets.QAction("Save changes", self)
        save_scene_changes_action.setIcon(QtGui.QIcon("icons:save.svg"))
        save_scene_changes_action.triggered.connect(self.save_scene)
        file_menu.addAction(save_scene_changes_action)
        load_scene_action = QtWidgets.QAction("Load scene from file", self)
        load_scene_action.setIcon(QtGui.QIcon("icons:load.png"))
        load_scene_action.triggered.connect(self.load_scene)
        file_menu.addAction(load_scene_action)

        node_menu = menu.addMenu("&Node library")
        re_scan_classes_action = QtWidgets.QAction("Re-scan classes", self)
        re_scan_classes_action.setIcon(QtGui.QIcon("icons:examine.png"))
        re_scan_classes_action.triggered.connect(self.reload_classes)
        node_menu.addAction(re_scan_classes_action)

        scene_menu = menu.addMenu("&Scene library")
        add_scenes_recursive(all_scenes, scene_menu)

        window_menu = menu.addMenu("&Window")
        show_attr_editor = QtWidgets.QAction("Show attribute editor", self)
        show_attr_editor.setIcon(QtGui.QIcon("icons:eye.svg"))
        show_attr_editor.triggered.connect(self.attr_editr_dock.show)
        window_menu.addAction(show_attr_editor)

        help_menu = menu.addMenu("&Help")
        shortcuts_action = QtWidgets.QWidgetAction(help_menu)
        shortcuts_action.setDefaultWidget(ShortcutsHelp())
        help_menu.addAction(shortcuts_action)

    def create_dock_windows(self):
        self.attr_editr_dock.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
        )
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.attr_editr_dock)
        self.attr_editr_dock.hide()

    def populate_annotations(self):
        annotation_items_folder = QtCore.QDir.searchPaths("graphics")[0]

        for note_type_elem in os.listdir(annotation_items_folder):
            note_type = Path(note_type_elem).stem
            annotation_item = QtWidgets.QTreeWidgetItem()
            annotation_item.setIcon(0, QtGui.QIcon(f"graphics:{note_type}.svg"))
            annotation_item.setText(0, note_type.replace("_", " ").title())
            annotation_item.setData(0, QtCore.Qt.UserRole, note_type)
            annotation_item.setData(
                0, QtCore.Qt.UserRole + 1, constants.GRAPHIC_ANNOTATION
            )
            annotation_item.setFont(0, QtGui.QFont("arial", 14))
            self.ui.annotations_tree.addTopLevelItem(annotation_item)

        self.ui.annotations_tree.sortByColumn(0, QtCore.Qt.AscendingOrder)

    def populate_tree(self):
        """
        Populate the tree where all nodes are displayed.
        """
        lib_names = CR.get_all_classes().keys()
        for lib_name in lib_names:
            if lib_name in self.libraries_added:
                continue
            self.libraries_added.add(lib_name)

            all_classes = CR.get_all_classes().get(lib_name)
            if not all_classes:
                return

            top_level_items = {}
            for lib in sorted(all_classes):
                node_lib_path = all_classes[lib]["node_lib_path"]
                node_lib_name = all_classes[lib]["node_lib_name"]
                node_lib_nice_name = node_lib_name.title().replace("_", " ")
                module_filename = all_classes[lib]["module_filename"]
                module_full_path = all_classes[lib]["module_full_path"]
                module_nice_name = lib.title().replace("_", " ")
                color = all_classes[lib].get("color", constants.DEFAULT_NODE_COLOR)

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

                for name, cls in all_classes[lib]["classes"]:
                    class_item = QtWidgets.QTreeWidgetItem()
                    class_item.setText(0, name)
                    class_item.setToolTip(
                        0,
                        "<h2>Class:&nbsp;<b>{}</b></h2><p style='white-space:pre'>{}".format(
                            name, module_full_path
                        ),
                    )
                    class_item.setData(0, QtCore.Qt.UserRole, name)
                    class_item.setData(
                        0, QtCore.Qt.UserRole + 1, constants.GRAPHIC_NODE
                    )
                    if (
                        hasattr(cls, "NICE_NAME") and cls.NICE_NAME
                    ):  # TODO inheritance not working here?
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

            self.ui.nodes_tree.sortByColumn(0, QtCore.Qt.AscendingOrder)

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

    def reload_classes(self):
        """
        Reload the classes displayed in the nodes tree widget.

        This function clears the nodes tree widget and the libraries added list.
        It then flushes the class registry and starts the classes scanning.
        """
        # Clear the UI
        self.menuBar().setEnabled(False)
        self.ui.nodes_tree.clear()
        self.ui.annotations_tree.clear()
        self.libraries_added.clear()

        # Re-scan classes
        CR.flush()
        CR.scan_for_classes_GUI()

        for worker in CR.get_workers():
            worker.signaler.finished.connect(self.populate_tree)

    # TABS ----------------------
    def clear_workspace(self):
        """
        Clear the workspace by displaying a confirmation dialog to the user.

        If the user confirms, all unsaved progress will be lost. It clears the tabs and adds a new scene to the workspace.
        """
        dlg = QtWidgets.QMessageBox(parent=None)
        dlg.setWindowTitle("Clear workspace")
        dlg.setText(
            "<p style='white-space:pre'>Are you sure?<br>All unsaved progress will be lost!"
        )
        dlg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        dlg.setIcon(QtWidgets.QMessageBox.Question)
        button = dlg.exec_()

        if button == QtWidgets.QMessageBox.No:
            return

        self.clear_tabs()
        self.add_scene()

    def clear_tabs(self):
        """
        Remove all tabs / scenes
        """
        self.ui.tabWidget.clear()

    def add_scene(self, context=None):
        """
        Add a new graphic scene to the widget (in a new tab).

        If a context is supplied, build its internals onto the new scene.

        Args:
            context (GeneralLogicNode): optional, context node from which to build the scene
        """
        scene_name = "/"
        icon = QtGui.QIcon()
        if context:
            scene_name = context.full_name
            icon = QtGui.QIcon(CR.get_icon_path(context.class_name))

        graphics_view = graphic_scene.CustomGraphicsView()
        graphics_scene = graphic_scene.CustomScene(context)
        graphics_view.setScene(graphics_scene)

        graphics_scene.setSceneRect(-20000, -20000, 40000, 40000)
        graphics_scene.setParent(graphics_view)
        GS.signals.main_screen_feedback.connect(graphics_view.show_feedback)

        if context:
            graphics_scene.load_from_file(context.CONTEXT_DEFINITION_FILE, False)

        self.ui.tabWidget.addTab(graphics_view, icon, scene_name)
        self.ui.tabWidget.setCurrentIndex(self.ui.tabWidget.count() - 1)

    def expand_context(self, uuid):
        """
        Expand the contents of a context node into a new tab.

        Args:
            uuid (str): of the node to try to expand
        """
        n = self.get_node_by_uuid(uuid)

        # See if it is a context
        if not n.IS_CONTEXT:
            return

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
        for i in range(self.ui.tabWidget.count()):
            current_gw = self.ui.tabWidget.widget(i)
            current_logic_scene = current_gw.scene().logic_scene
            for n in current_logic_scene.all_nodes():
                if n.uuid == uuid:
                    return n

    def add_node_to_current(self, pos, class_name=None):
        """
        Add a new node to the current graphic scene.

        Args:
            x (int): horizontal coord t (in view coords) add the node to
            y (int): vertical coord t (in view coords) add the node to
            class_name (str, optional): class name of the node to instantiate
        """
        current_gw = self.ui.tabWidget.widget(self.ui.tabWidget.currentIndex())
        current_scene = current_gw.scene()
        node_class_name = class_name
        item_type = constants.GRAPHIC_NODE

        if class_name is None:
            selected_item = (
                self.ui.nodes_tree.selectedItems()
                or self.ui.annotations_tree.selectedItems()
            )
            if not selected_item:
                return
            selected = selected_item[0]
            node_class_name = str(selected.data(0, QtCore.Qt.UserRole)).strip()
            item_type = str(selected.data(0, QtCore.Qt.UserRole + 1)).strip()

        if item_type == constants.GRAPHIC_NODE:
            current_scene.add_graphic_node_by_class_name(
                node_class_name,
                current_gw.mapToScene(pos).x() - 50,
                current_gw.mapToScene(pos).y() - 20,
            )

        elif item_type == constants.GRAPHIC_ANNOTATION:
            current_scene.add_annotation_by_type(
                node_class_name,
                current_gw.mapToScene(pos).x() - 50,
                current_gw.mapToScene(pos).y() - 50,
            )

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
        self.attr_editr_dock.show()

    # SAVE AND LOAD ----------------------
    def save_scene(self):
        """
        Launch process of saving changes of current scene to a file, or just save as.
        """
        current_gw = self.ui.tabWidget.widget(self.ui.tabWidget.currentIndex())
        current_scene = current_gw.scene()
        if current_scene.filepath:
            current_scene.save_to_file(current_scene.filepath)
        else:
            current_scene.save_to_file()

    def save_scene_as(self):
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

        # Clear scenes
        self.clear_tabs()

        # Clear attr editor
        self.attr_editor.clear_all()

        # Add scene and load
        self.add_scene()
        current_gw = self.ui.tabWidget.widget(self.ui.tabWidget.currentIndex())
        current_scene = current_gw.scene()
        current_scene.load_from_file(source_file)
        current_scene.fit_in_view()
        self.ui.tabWidget.setTabText(
            self.ui.tabWidget.currentIndex(),
            os.path.basename(source_file),
        )
        self.ui.tabWidget.setTabIcon(
            self.ui.tabWidget.currentIndex(), QtGui.QIcon("icons:scene.png")
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
        current_index = self.ui.tabWidget.currentIndex()
        if current_index < 0:
            return
        current_gw = self.ui.tabWidget.widget(current_index)
        current_scene = current_gw.scene()
        current_scene.show_result_on_nodes()
