# -*- coding: UTF-8 -*-
from __future__ import annotations

__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import datetime
import getpass
import os
import yaml

from PySide2 import QtCore

from all_nodes import constants
from all_nodes import utils
from all_nodes.analytics import analytics
from all_nodes.graphic.widgets.global_signaler import GLOBAL_SIGNALER as GS
from all_nodes.logic import ALL_CLASSES, ALL_SCENES
from all_nodes.logic.logic_node import GeneralLogicNode


LOGGER = utils.get_logger(__name__)


# -------------------------------- LOGIC SCENE -------------------------------- #
class LogicScene:
    def __init__(self):
        self.scene_name = None

        self.context = None

        self.all_logic_nodes = set()
        self.class_counter = dict()

        self.pasted_count = 0

        self.thread_manager = QtCore.QThreadPool()

        LOGGER.debug("Initialized logic scene")

    # NODE ADDITION AND DELETION ----------------------
    def add_node_by_name(
        self, node_classname: str, rename_on_create=True
    ) -> GeneralLogicNode:
        for m in sorted(ALL_CLASSES):
            for name, cls in ALL_CLASSES[m]["classes"]:
                if node_classname == name:
                    new_logic_node = cls()
                    self.all_logic_nodes.add(new_logic_node)
                    if node_classname not in self.class_counter:
                        self.class_counter[node_classname] = 1
                    else:
                        self.class_counter[node_classname] += 1
                        if rename_on_create:
                            self.rename_node(
                                new_logic_node,
                                node_classname
                                + "_"
                                + str(self.class_counter[node_classname]),
                            )

                    if self.context:
                        new_logic_node.set_context(self.context)
                    return new_logic_node

        raise LogicSceneError("No class {} was found!".format(node_classname))

    def clear(self):
        self.all_logic_nodes = set()
        LOGGER.info("Cleared logic scene")

    def remove_node_by_name(self, node_fullname):
        for node in self.all_logic_nodes:
            if node.node_name == node_fullname:
                self.all_logic_nodes.remove(node)
                LOGGER.info("Removed logic node {}".format(node_fullname))
                return
        raise RuntimeError("No node matches name" + node_fullname)

    # NODE RETRIEVAL ----------------------
    def all_nodes(self):
        return self.all_logic_nodes

    def node_count(self):
        return len(self.all_logic_nodes)

    def get_starting_nodes(self):
        starting_nodes = []
        for n in self.all_logic_nodes:
            if n.is_starting_node():
                LOGGER.info("Node {} to be used as starting node".format(n.node_name))
                starting_nodes.append(n)

        if not starting_nodes:
            LOGGER.warning("No starting nodes found in this logic scene")

        return starting_nodes

    def to_node(self, node_full_name):
        for node in self.all_logic_nodes:
            if node.node_name == node_full_name:
                return node

    def to_attr(self, attr_full_name):
        for node in self.all_logic_nodes:
            for attr in node.all_attributes:
                if attr.full_name == attr_full_name:
                    return attr

    # NODE MANIPULATION ----------------------
    def rename_node(self, node, new_name: str) -> bool:
        for n in self.all_logic_nodes:
            if n.uuid == node.uuid:
                continue
            if n.node_name == new_name:
                LOGGER.error("Node {} already exists!".format(new_name))
                return False

        return node.rename(new_name)

    def rename_node_with_namespace(self, node, new_name: str) -> None:
        for n in self.all_logic_nodes:
            if n.uuid == node.uuid:
                continue
            if n.node_name == new_name:
                raise LogicSceneError("Node {} already exists!".format(new_name))

        return node.force_rename(new_name)

    def set_context_to_nodes(self):
        for node in self.all_logic_nodes:
            node.set_context(self.context)

    def connect_attrs_by_name(self, source_attr_name, target_attr_name):
        source_attr, target_attr = None, None
        for node in self.all_logic_nodes:
            for attr in node.all_attributes:
                if attr.dot_name == source_attr_name:
                    source_attr = attr
                    break
                elif attr.dot_name == target_attr_name:
                    target_attr = attr
                    break
            if source_attr and target_attr:
                source_attr.connect_to_other(target_attr)  # TODO check for result
                return

        # Errors
        source_node_name = source_attr_name.rsplit(".", 1)[0]
        target_node_name = target_attr_name.rsplit(".", 1)[0]
        if self.to_node(source_node_name) is None:
            raise LogicSceneError(
                "Cannot connect! {} -> {}, source node '{}' does not exist".format(
                    source_attr_name, target_attr_name, source_node_name
                )
            )
        elif self.to_node(target_node_name) is None:
            raise LogicSceneError(
                "Cannot connect! {} -> {}, target node '{}' does not exist".format(
                    source_attr_name, target_attr_name, target_node_name
                )
            )
        elif source_attr is None:
            raise LogicSceneError(
                "Cannot connect! {} -> {}, source attribute '{}' does not exist"
                "".format(source_attr_name, target_attr_name, source_attr_name)
            )
        elif target_attr is None:
            raise LogicSceneError(
                "Cannot connect! {} -> {}, target attribute '{}' does not exist"
                "".format(source_attr_name, target_attr_name, target_attr_name)
            )

    # SAVE AND LOAD ----------------------
    def convert_scene_to_dict(self):
        scene_dict = dict()

        scene_dict["nodes"] = list()
        all_node_names = sorted([n.node_name for n in self.all_logic_nodes])
        for name in all_node_names:
            for node in self.all_logic_nodes:
                if node.node_name == name:
                    node_dict = node.get_node_basic_dict()
                    scene_dict["nodes"].append(node_dict)
                    break

        connections = set()
        for node in self.all_logic_nodes:
            out_conns = node.get_out_connections()
            if out_conns:
                for c in out_conns:
                    connections.add(" -> ".join(c))
        scene_dict["connections"] = sorted(list(connections))

        return scene_dict

    def save_to_file(self, filepath: str, scene_dict: dict = None) -> None:
        LOGGER.debug("Writing to file")

        if scene_dict is None:
            scene_dict = self.convert_scene_to_dict()

        save_type = "scene"
        _, ext = os.path.splitext(filepath)
        if ext == ".ctx":
            save_type = "context"
        with open(filepath, "w") as file:
            header = "# {} {}".format(
                save_type.upper(), os.path.splitext(os.path.basename(filepath))[0]
            )
            file.write(header)
            file.write("\n# " + "-" * (len(header) - 2))
            file.write("\n# Description: ")

            file.write(
                "\n\n# Nodes section: overall list of nodes to be created\n" "nodes:\n"
            )
            yaml.dump(scene_dict["nodes"], file, sort_keys=True)

            if scene_dict["connections"]:
                file.write(
                    "\n# Connections section: connections to be done between nodes\n"
                    "connections:\n"
                )
                yaml.dump(scene_dict["connections"], file)

            file.write(
                "\n\n# {} created at: {}".format(
                    save_type.capitalize(), datetime.datetime.now()
                )
            )
            file.write("\n# Created by: {}".format(getpass.getuser()))

        LOGGER.info("Wrote scene to file: {}".format(filepath))

    def load_from_file(self, scene_path: str, namespace: str = None) -> list:
        # See if we need namespace
        if self.all_nodes():
            if namespace is None:
                namespace = self.get_namespace()
            else:
                namespace += "::"
        else:
            namespace = ""

        if namespace:
            LOGGER.debug("Using namespace: {}".format(namespace))

        # Alias
        if not os.path.isfile(scene_path):
            LOGGER.info(
                "Cannot find scene with path '{}', trying to find it as alias".format(
                    scene_path
                )
            )
            found_scene_path = utils.get_scene_from_alias(ALL_SCENES, scene_path)
            if not found_scene_path:
                raise LogicSceneError(
                    "Cannot find scene for alias '{}'".format(scene_path)
                )
            else:
                scene_path = found_scene_path

        # Filepath
        if self.context:
            utils.print_separator("Loading context " + scene_path)
        else:
            utils.print_separator("Loading scene " + scene_path)
        scene_dict = dict()
        with open(scene_path, "r") as file:
            scene_dict = yaml.safe_load(file)

        if not scene_dict:
            return  # TODO raise error

        # Create nodes
        new_nodes = []
        for node in scene_dict.get("nodes", []):
            node_name = next(iter(node))
            n = self.add_node_by_name(node[node_name]["class_name"], False)
            new_nodes.append(n)
            if namespace:
                if not self.rename_node_with_namespace(n, namespace + node_name):
                    raise LogicSceneError(
                        "Node cannot be renamed to: {}".format(namespace + node_name)
                    )
            else:
                if not self.rename_node(n, node_name):
                    raise LogicSceneError(
                        "Node cannot be renamed to: {}".format(namespace + node_name)
                    )
            attrs_to_set = node[node_name].get("node_attributes")
            if attrs_to_set:
                for attr in attrs_to_set:
                    n.set_attribute_value(attr, attrs_to_set[attr])

        # Create connections
        for connection in scene_dict.get("connections", []):
            attrs_to_connect = connection.split("->")
            source_attr_name, target_attr_name = (
                namespace + attrs_to_connect[0].strip(),
                namespace + attrs_to_connect[1].strip(),
            )
            self.connect_attrs_by_name(source_attr_name, target_attr_name)

        return new_nodes

    # SCENE PROPERTIES ----------------------
    def set_name(self, new_name):
        self.scene_name = new_name

    def get_namespace(self):
        self.pasted_count += 1
        return "pasted_{}::".format(self.pasted_count)

    # EXECUTION ----------------------
    def reset_all_nodes(self):
        LOGGER.debug("Resetting all logic nodes of scene {}".format(self.scene_name))
        for node in self.all_logic_nodes:
            node.reset()

    def soft_reset_all_nodes(self):
        LOGGER.debug(
            "Soft-resetting all logic nodes of scene {}".format(self.scene_name)
        )
        for node in self.all_logic_nodes:
            node.soft_reset()

    def run_all_nodes(self, spawn_thread=True):
        if spawn_thread:
            worker = Worker(self._run_all_nodes)
            self.thread_manager.start(worker)
        else:
            self._run_all_nodes()

    def run_all_nodes_batch(self):
        """For non-GUI, we cannot spawn threads"""
        # TODO investigate why this happens
        self._run_all_nodes()

    def _run_all_nodes(self):
        # Feedback
        if self.scene_name:
            utils.print_separator("Running {}".format(self.scene_name))
        else:
            utils.print_separator("Running logic scene")

        # Execution
        for node in self.get_starting_nodes():
            node._run()
        LOGGER.info("Finished running logic scene")
        print("\n", end="")

        # Mark nodes that were skipped
        for node in self.all_nodes():
            if node.success == constants.NOT_RUN:
                node.mark_skipped()

        # Analytics
        # TODO separate into own method in case analytics crash
        LOGGER.info("Gathering analytics")
        node_properties_list = []
        for node in self.all_logic_nodes:
            node_properties_list.append(node.get_node_full_dict())
            if node.IS_CONTEXT:
                for i_node in (
                    node.internal_scene.all_logic_nodes
                ):  # TODO make this properly recursive
                    node_properties_list.append(i_node.get_node_full_dict())
        analytics.submit_bulk_analytics(node_properties_list)

    def run_list_of_nodes(self, nodes_to_execute, spawn_thread=True):
        if spawn_thread:
            worker = Worker(self._run_list_of_nodes, nodes_to_execute)
            self.thread_manager.start(worker)
        else:
            self._run_list_of_nodes(nodes_to_execute)

    def _run_list_of_nodes(self, nodes_to_execute):
        for node in nodes_to_execute:
            node.run_single()

    # FEEDBACK GATHERING ----------------------
    def gather_failed_nodes(self):
        failed_log = []
        for node in self.all_logic_nodes:
            if node.success in [constants.FAILED, constants.ERROR]:
                for line in node.fail_log:
                    failed_log.append(node.full_name + ": " + line)
        return failed_log

    def gather_errored_nodes(self):
        errored_log = []
        for node in self.all_logic_nodes:
            if node.success in [constants.FAILED, constants.ERROR]:
                for line in node.error_log:
                    errored_log.append(node.full_name + ": " + line)
        return errored_log


# -------------------------------- UTILITY -------------------------------- #
class LogicSceneError(Exception):
    pass


# -------------------------------- WORKER -------------------------------- #
class Worker(QtCore.QRunnable):
    """
    Worker thread.
    """

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """
        self.fn(*self.args, **self.kwargs)
        GS.execution_finished.emit()
        GS.attribute_editor_global_refresh_requested.emit()
