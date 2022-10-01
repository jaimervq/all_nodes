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

from __future__ import annotations

__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import datetime
import getpass
import os
import yaml

from all_nodes import utils
from all_nodes.logic import ALL_CLASSES, ALL_SCENES
from all_nodes.logic.logic_node import GeneralLogicNode


LOGGER = utils.get_logger(__name__)


class LogicScene:
    def __init__(self):

        self.all_logic_nodes = set()
        self.class_counter = dict()

        self.pasted_count = 0

        LOGGER.debug("Initialized logic scene")

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
                    return new_logic_node

        raise RuntimeError("No class {} was found!".format(node_classname))

    def rename_node(self, node, new_name: str) -> bool:
        for n in self.all_logic_nodes:
            if n.uuid == node.uuid:
                continue
            if n.full_name == new_name:
                LOGGER.error("Node {} already exists!".format(new_name))
                return False

        return node.rename(new_name)

    def rename_node_with_namespace(self, node, new_name: str) -> None:
        for n in self.all_logic_nodes:
            if n.uuid == node.uuid:
                continue
            if n.full_name == new_name:
                raise LogicSceneError("Node {} already exists!".format(new_name))

        return node.force_rename(new_name)

    def all_nodes(self):
        return self.all_logic_nodes

    def node_count(self):
        return len(self.all_logic_nodes)

    def get_starting_nodes(self):
        starting_nodes = []
        for n in self.all_logic_nodes:
            if n.is_starting_node():
                LOGGER.info("Node {} to be used as starting node".format(n.full_name))
                starting_nodes.append(n)

        if not starting_nodes:
            LOGGER.warning("No starting nodes found in this logic scene")

        return starting_nodes

    def to_node(self, node_full_name):
        for node in self.all_logic_nodes:
            if node.full_name == node_full_name:
                return node

    def clear(self):
        self.all_logic_nodes = set()
        LOGGER.info("Cleared logic scene")

    def remove_node_by_name(self, node_fullname):
        for node in self.all_logic_nodes:
            if node.full_name == node_fullname:
                self.all_logic_nodes.remove(node)
                LOGGER.info("Removed logic node {}".format(node_fullname))
                return
        raise RuntimeError("No node matches name" + node_fullname)

    def convert_scene_to_dict(self):
        scene_dict = dict()

        scene_dict["nodes"] = list()
        all_node_names = sorted([n.full_name for n in self.all_logic_nodes])
        for name in all_node_names:
            for node in self.all_logic_nodes:
                if node.full_name == name:
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

        with open(filepath, "w") as file:
            header = "# SCENE {}".format(
                os.path.splitext(os.path.basename(filepath))[0]
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

            file.write("\n\n# Scene created at: {}".format(datetime.datetime.now()))
            file.write("\n# Created by: {}".format(getpass.getuser()))

        LOGGER.info("Wrote scene to file: {}".format(filepath))

    def get_namespace(self):
        self.pasted_count += 1
        return "pasted_{}::".format(self.pasted_count)

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
        found_by_alias = False
        if not os.path.isfile(scene_path):
            LOGGER.info(
                "Cannot find scene with path '{}', trying to find it as alias".format(
                    scene_path
                )
            )
            found_scene_path = utils.get_scene_from_alias(ALL_SCENES, scene_path)
            if not found_scene_path:
                raise LogicSceneError(
                    "Cannot find scene for alias'{}'".format(scene_path)
                )
            else:
                scene_path = found_scene_path

        # Filepath
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

    def connect_attrs_by_name(self, source_attr_name, target_attr_name):
        source_attr, target_attr = None, None
        for node in self.all_logic_nodes:
            for attr in node.all_attributes:
                if attr.full_name == source_attr_name:
                    source_attr = attr
                    break
                elif attr.full_name == target_attr_name:
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
                "Cannot connect! {} -> {}, source node '{}' does not exist"
                "".format(source_attr_name, target_attr_name, source_node_name)
            )
        elif self.to_node(target_node_name) is None:
            raise LogicSceneError(
                "Cannot connect! {} -> {}, target node '{}' does not exist"
                "".format(source_attr_name, target_attr_name, target_node_name)
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

    def reset_all_nodes(self):
        utils.print_separator("Resetting all logic nodes")
        for node in self.all_logic_nodes:
            node.reset()

    def run_all_nodes(self):
        utils.print_separator("Running logic scene")
        for node in self.get_starting_nodes():
            node._run()
        LOGGER.info("Finished running logic scene")
        print("\n", end="")


class LogicSceneError(Exception):
    pass
