# -*- coding: UTF-8 -*-
from __future__ import annotations

__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"

import ast
from copy import deepcopy
import datetime
import getpass
import os
from pathlib import Path
import pprint
import re
import time
import uuid

from PySide2 import QtCore

from all_nodes import constants
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


# -------------------------------- GENERAL NODE -------------------------------- #
class GeneralLogicNode:
    """
    General logic node implementation.

    Example of attribute setup:
    INPUTS_DICT = {"in_attribute_example_1": {"type": int},
                   "in_attribute_example_2": {"type": str, "optional": True},
                   "in_attribute_example_3": {"type": list, "optional": True},
                   "in_attribute_example_with_a_very_long_name": {"type": dict},
    }

    OUTPUTS_DICT = {"out_attribute_example_1": {"type": str},
                    "out_attribute_example_2": {"type": int},
    }

    The 'optional' parameter can be provided, but will always default to False unless specified,
    as we mostly want all inputs of nodes to be set.

    """

    FILEPATH = ""

    NICE_NAME = ""
    HELP = ""

    IS_CONTEXT = False
    CONTEXT_DEFINITION_FILE = ""

    INPUTS_DICT = {}
    OUTPUTS_DICT = {}

    INTERNALS_DICT = {}  # Internal attrs not exposed (for GUI input / preview mostly)

    VALID_NAMING_PATTERN = "^[A-Z]+[a-zA-Z0-9_]*$"

    def __init__(self):
        # General properties
        self.class_name = type(self).__name__
        self.node_name = self.class_name + "_1"
        self.uuid = str(uuid.uuid4())

        # Copy dicts
        self.INPUTS_DICT = deepcopy(self.INPUTS_DICT)
        self.OUTPUTS_DICT = deepcopy(self.OUTPUTS_DICT)

        # Attributes
        self.all_attributes = []
        self.check_attributes_validity()
        self.create_attributes()

        # Context it belongs to
        self.context = None

        # Specific for contexts
        self.internal_scene = None
        self.build_internal()

        # Execution
        self.active = True
        self.success = constants.NOT_RUN
        self.execution_counter = 0

        self.fail_log = []
        self.error_log = []

        self.run_date = None
        self.execution_time = 0
        self.user = getpass.getuser()

        # Signals
        self.signaler = LogicNodeSignaler()

        # Feedback
        LOGGER.debug("Initialized node! {}".format(self.class_name))

    # UTILITY ----------------------
    @staticmethod
    def name_is_valid(name) -> bool:
        """
        Check if the given name is valid according to a defined pattern.

        Parameters:
            name (str): The name to be checked.

        Returns:
            bool: True if the name is valid, False otherwise.
        """
        if re.match(GeneralLogicNode.VALID_NAMING_PATTERN, name):
            return True
        return False

    def rename(self, new_name: str) -> bool:
        """
        Rename the node to the given new name.

        Args:
            new_name (str): The new name for the node.

        Returns:
            bool: True if the node is successfully renamed, False otherwise.

        Example:
            node.rename("Node2")  # returns True
            node.rename("1Node")  # returns False
        """
        if self.node_name == new_name:
            return True

        if self.name_is_valid(new_name):
            LOGGER.debug("Renamed node '{}' to '{}'".format(self.node_name, new_name))
            self.node_name = new_name
            return True
        else:
            LOGGER.warning("Name proposed for node is not valid: {}".format(new_name))

        return False

    def force_rename(self, new_name: str) -> bool:
        """
        Rename the node to the given new name, ignoring any validation rules.

        Args:
            new_name (str): The new name for the node.

        Returns:
            bool: True always.
        """
        LOGGER.debug(
            "Forcing renaming of node '{}' to '{}'".format(self.node_name, new_name)
        )
        self.node_name = new_name
        return True

    def get_max_in_or_out_count(self) -> int:
        """
        Get the maximum number of input or output attributes.

        Returns:
            int: The maximum number of input or output attributes.
        """
        return max(len(self.get_input_attrs()), len(self.get_output_attrs()))

    def get_node_full_dict(self) -> dict:
        """
        Get a dictionary containing the full representation of the node,
        including class name, node name, attributes, connections, success, logs,
        execution info, and extra information.

        Returns:
            dict: A dictionary fully representing the node.
        """
        out_dict = dict()

        # Class name, node name...
        out_dict["class_name"] = self.class_name
        out_dict["node_name"] = self.node_name
        out_dict["full_name"] = self.full_name
        out_dict["uuid"] = self.uuid
        out_dict["origin_file"] = Path(self.FILEPATH).name

        # Attributes
        out_dict["node_attributes"] = dict()
        for attr in self.all_attributes:
            if self.INTERNALS_DICT.get(attr.attribute_name, {}).get("gui_type") in set(
                constants.PreviewsGUI
            ):
                continue  # No need to register preview attrs

            out_dict["node_attributes"][attr.dot_name] = dict()
            out_dict["node_attributes"][attr.dot_name]["attribute_name"] = (
                attr.attribute_name
            )
            out_dict["node_attributes"][attr.dot_name]["value"] = str(attr.value)
            out_dict["node_attributes"][attr.dot_name]["connector_type"] = (
                attr.connector_type
            )
            out_dict["node_attributes"][attr.dot_name]["is_optional"] = attr.is_optional
            out_dict["node_attributes"][attr.dot_name]["data_type"] = (
                attr.get_datatype_str()
            )
            out_dict["node_attributes"][attr.dot_name]["data_type_str"] = (
                attr.get_datatype_str()
            )
            out_dict["node_attributes"][attr.dot_name]["connected_to"] = [
                c_attr.dot_name for c_attr in attr.connected_attributes
            ]

        # Connections
        connections = list()
        for attr in self.all_attributes:
            connections += attr.get_connections_list()
        out_dict["connections"] = connections

        # Success and logs
        out_dict["success"] = self.success

        out_dict["error_log"] = self.error_log
        out_dict["fail_log"] = self.fail_log

        # Execution info
        out_dict["run_date"] = (
            self.run_date.strftime("%Y-%m-%d") if self.run_date else None
        )
        out_dict["execution_time"] = self.execution_time
        out_dict["user"] = self.user
        if not self.active:
            out_dict["active"] = self.active

        # Extra
        out_dict["IS_CONTEXT"] = self.IS_CONTEXT

        return out_dict

    def get_node_basic_dict(self) -> dict:
        """Get a dict that represents the main data needed to 'rebuild' a node.

        It is retrieved as dict so it can also be serialized

        Returns:
            dict: with node main data
        """
        out_dict = dict()

        out_dict[self.node_name] = dict()
        out_dict[self.node_name]["class_name"] = self.class_name
        if not self.active:
            out_dict[self.node_name]["active"] = self.active

        out_dict[self.node_name]["node_attributes"] = dict()
        for attr in self.all_attributes:
            if self.INTERNALS_DICT.get(attr.attribute_name, {}).get("gui_type") in set(
                constants.PreviewsGUI
            ):
                continue  # No need to register preview attrs

            if (
                attr.attribute_name not in [constants.START, constants.COMPLETED]
                and attr.value is not None
            ):
                out_dict[self.node_name]["node_attributes"][attr.attribute_name] = (
                    attr.value
                )

        # If no node attributes were registered, no need to keep this key
        if not out_dict[self.node_name]["node_attributes"]:
            out_dict[self.node_name].pop("node_attributes")

        return out_dict

    def get_out_connections(self):
        """
        Get a list of connections coming from output attributes of this node.

        Returns:
            list: of lists, where each list contains the dot names of two connected attributes.
        """
        connections_list = list()
        for attr in self.get_output_attrs():
            for connected in attr.connected_attributes:
                connections_list.append([attr.dot_name, connected.dot_name])

        return connections_list

    def out_connected_nodes(self):
        """
        Return a set of nodes that are connected to this node's output attributes.

        Returns:
            set: A set of nodes that are connected to this node's output attributes.
        """
        connected_nodes = set()
        for attr in self.get_output_attrs():
            for connected_attr in attr.connected_attributes:
                connected_nodes.add(connected_attr.parent_node)

        return connected_nodes

    def in_connected_nodes_recursive(self) -> list:
        """Recursively get the full 'chain' of all the nodes connected to this node's inputs

        Returns:
            list: list of nodes
        """
        in_connected_nodes = list()

        in_immediate_nodes = set()
        for attr in self.get_input_attrs():
            for connected_attr in attr.connected_attributes:
                in_immediate_nodes.add(connected_attr.parent_node)

        in_immediate_nodes_list = list(in_immediate_nodes)
        in_connected_nodes += in_immediate_nodes_list
        for node in in_immediate_nodes_list:
            in_connected_nodes += node.in_connected_nodes_recursive()

        return in_connected_nodes

    def check_cycles(self, node_to_check: GeneralLogicNode) -> bool:
        """
        Check if a given node is part of a cycle in the connected nodes of this node.

        Args:
            node_to_check (GeneralLogicNode): The node to check for cycles.

        Returns:
            bool: True if the given node is part of a cycle, False otherwise.
        """
        in_connected_nodes = self.in_connected_nodes_recursive()
        return node_to_check in in_connected_nodes

    def get_gui_internals_inputs(self) -> dict:
        """
        Return a dictionary of internal attributes that are used as GUI inputs.

        Returns:
            dict: A dictionary of internal attributes used as GUI inputs.
        """
        gui_internals_inputs = dict()
        for attr_name in self.INTERNALS_DICT:
            if self.INTERNALS_DICT[attr_name].get("gui_type") in list(
                constants.InputsGUI
            ):
                gui_internals_inputs[attr_name] = self.INTERNALS_DICT[attr_name]

        return gui_internals_inputs

    def get_gui_internals_previews(self) -> dict:
        """
        Returns a dictionary of internal attributes that are used as GUI previews.

        Returns:
            dict: A dictionary of internal attributes used as GUI previews.
        """
        gui_internals_previews = dict()
        for attr_name in self.INTERNALS_DICT:
            if self.INTERNALS_DICT[attr_name].get("gui_type") in set(
                constants.PreviewsGUI
            ):
                gui_internals_previews[attr_name] = self.INTERNALS_DICT[attr_name]

        return gui_internals_previews

    # PROPERTIES ----------------------
    @property
    def full_name(self):
        """
        Property method to get the full name of the node by combining the context full name and node name.
        Returns the full name as a string.
        """
        if self.context:
            return self.context.full_name + "/" + self.node_name
        else:
            return "/" + self.node_name

    @property
    def all_attribute_names(self):
        """
        Property method to get all attribute names by extracting attribute names from all attributes.
        Returns a list of attribute names.
        """
        return [a.attribute_name for a in self.all_attributes]

    # ATTRIBUTES ----------------------
    def check_attributes_validity(self):
        """
        Check the validity of the attributes in the node.

        Raises:
            RuntimeError: If an input attribute name is also present in the OUTPUTS_DICT.
        """
        for in_name in self.INPUTS_DICT.keys():
            if in_name in self.OUTPUTS_DICT.keys():
                raise RuntimeError(
                    "Input and output attributes cannot have same name! ({})".format(
                        in_name
                    )
                )

    def create_attributes(self):
        """
        Populate this node with the attributes that have been defined.
        """
        # -------------- INPUTS -------------- #
        # Add a special "Run control" START attribute that will be in all nodes
        start_attr = GeneralLogicAttribute(
            self, constants.START, constants.INPUT, Run, is_optional=True
        )
        self.all_attributes.append(start_attr)

        for input_attribute_name in self.INPUTS_DICT:
            in_attr = GeneralLogicAttribute(
                self,
                input_attribute_name,
                constants.INPUT,
                self.INPUTS_DICT[input_attribute_name]["type"],
                is_optional=self.INPUTS_DICT[input_attribute_name].get(
                    "optional", False
                ),
            )
            self.all_attributes.append(in_attr)

        # -------------- OUTPUTS -------------- #
        for output_attribute_name in self.OUTPUTS_DICT:
            out_attr = GeneralLogicAttribute(
                self,
                output_attribute_name,
                constants.OUTPUT,
                self.OUTPUTS_DICT[output_attribute_name]["type"],
                is_optional=self.OUTPUTS_DICT[output_attribute_name].get(
                    "optional", False
                ),
            )
            self.all_attributes.append(out_attr)

        # Add a special "Run control" COMPLETED attribute that will be in all nodes
        completed_attr = GeneralLogicAttribute(
            self, constants.COMPLETED, constants.OUTPUT, Run, is_optional=True
        )
        self.all_attributes.append(completed_attr)

        # -------------- INTERNAL -------------- #
        for internal_attribute_name in self.INTERNALS_DICT:
            internal_attr = GeneralLogicAttribute(
                self,
                internal_attribute_name,
                constants.INTERNAL,
                self.INTERNALS_DICT[internal_attribute_name]["type"],
                is_optional=self.INTERNALS_DICT[internal_attribute_name].get(
                    "optional", False
                ),
            )
            self.all_attributes.append(internal_attr)

    def add_attribute(
        self,
        attribute_name,
        connector_type,
        data_type,
        gui_type=None,
        is_optional=False,
        value=None,
    ):
        # Check name
        if attribute_name in self.all_attribute_names:
            LOGGER.error(
                "Attribute name '{}' is already used. Skipping.".format(attribute_name)
            )
            return

        # Create attribute
        new_attribute = GeneralLogicAttribute(
            self, attribute_name, connector_type, data_type, is_optional=is_optional
        )

        if value:
            new_attribute.set_value(value)

        self.all_attributes.append(new_attribute)

        # Registrer it to the dict of the instance
        if connector_type == constants.INPUT:
            self.INPUTS_DICT[attribute_name] = dict()
            self.INPUTS_DICT[attribute_name]["type"] = data_type
            self.INPUTS_DICT[attribute_name]["optional"] = is_optional
        elif connector_type == constants.OUTPUT:
            self.OUTPUTS_DICT[attribute_name] = dict()
            self.OUTPUTS_DICT[attribute_name]["type"] = data_type
            self.OUTPUTS_DICT[attribute_name]["optional"] = is_optional
        elif connector_type == constants.INTERNAL:
            self.INTERNALS_DICT[attribute_name] = dict()
            self.INTERNALS_DICT[attribute_name]["type"] = data_type
            self.INTERNALS_DICT[attribute_name]["gui_type"] = gui_type

        # Return new attribute
        return new_attribute

    def get_input_attrs(self):
        """
        Get all the input attributes of the node.

        Returns:
            list: with all the input attributesf
        """
        return [
            attr
            for attr in self.all_attributes
            if attr.connector_type == constants.INPUT
        ]

    def clear_input_attrs(self):
        for attr in self.get_input_attrs():
            attr.clear()

    def recursive_clear_connected_input_attrs(self):
        for attr in self.get_input_attrs():
            if attr.has_input_connected():
                attr.clear()

        for node in self.out_connected_nodes():
            node.recursive_clear_connected_input_attrs()

    def recursive_set_in_loop(self):
        self.success = constants.IN_LOOP

        for node in self.out_connected_nodes():
            if node.class_name == "ForEachEnd":  # TODO cleanup this
                continue
            node.recursive_set_in_loop()

    def get_output_attrs(self):
        """
        Get all the output attributes of the node.

        Returns:
            list: with all the output attributes
        """
        return [
            attr
            for attr in self.all_attributes
            if attr.connector_type == constants.OUTPUT
        ]

    def set_attribute_value(self, attribute_name: str, value):
        """
        Set an attribute to a new value.

        Args:
            attribute_name (str): name of the attribute to set
            value: new value to set the attribute to
        """
        if attribute_name not in self.all_attribute_names:
            raise RuntimeError(
                "Error! No valid attribute '{}' in the node {}".format(
                    attribute_name, self.node_name
                )
            )

        for attribute in self.all_attributes:
            if attribute.attribute_name == attribute_name:
                if isinstance(value, attribute.data_type):
                    attribute.set_value(value)
                else:
                    raise RuntimeError(
                        "Not a valid type! {} not valid for {} (needed: {})".format(
                            value,
                            attribute.dot_name,
                            attribute.get_datatype_str(),
                        )
                    )

    def set_input(self, attribute_name: str, value):
        """
        Set an input attribute to a new value.

        Args:
            attribute_name (str): name of the input attribute to set
            value: new value to set the attribute to
        """
        for attr in self.all_attributes:
            if (
                attr.attribute_name == attribute_name
                and attr.connector_type == constants.INPUT
            ):
                self.set_attribute_value(attribute_name, value)
                return

        LOGGER.error(
            "Error! No valid input attribute {} in the node".format(attribute_name)
        )

    def set_output(self, attribute_name: str, value):
        """
        Set an output attribute to a new value.

        Args:
            attribute_name (str): name of the output attribute to set
            value: new value to set the attribute to
        """
        for attr in self.all_attributes:
            if (
                attr.attribute_name == attribute_name
                and attr.connector_type == constants.OUTPUT
            ):
                self.set_attribute_value(attribute_name, value)
                return

        LOGGER.error(
            "Error! No valid output attribute {} in the node".format(attribute_name)
        )

    def set_attribute_from_str(self, attribute_name: str, value_str: str):
        """
        Set the value of an attribute from a string.

        Args:
            attribute_name (str): The name of the attribute to set.
            value_str (str): The string value to set the attribute to.

        Notes:
            - If the attribute name is not valid, an error message is logged and the function returns.
            - If the value string is empty, the attribute is cleared.
        """
        if attribute_name not in self.all_attribute_names:
            LOGGER.error(
                "Error! No valid attribute '{}' in the node {}".format(
                    attribute_name, self.node_name
                )
            )
            return

        if value_str == "":
            for attribute in self.all_attributes:
                if attribute.attribute_name == attribute_name:
                    attribute.clear()
                    return

        for attribute in self.all_attributes:
            if attribute.attribute_name == attribute_name:
                if attribute.data_type is str:
                    attribute.set_value(value_str)
                elif attribute.data_type is float:
                    attribute.set_value(float(value_str))
                elif attribute.data_type is int:
                    attribute.set_value(int(value_str))
                elif attribute.data_type is bool:
                    if value_str in ["0", "1"]:
                        attribute.set_value(bool(int(value_str)))
                    elif value_str.lower() in ["false", "true"]:
                        attribute.set_value(
                            {
                                "False": False,
                                "True": True,
                                "false": False,
                                "true": True,
                            }.get(value_str)
                        )
                elif attribute.data_type in (dict, list, object, tuple):
                    try:
                        attribute.set_value(ast.literal_eval(value_str))
                    except (SyntaxError, ValueError) as e:
                        attribute.clear()
                        LOGGER.debug(e)
                else:
                    LOGGER.error(
                        "Cannot set value {} to type {}, not defined how to cast from string".format(
                            value_str, attribute.data_type
                        )
                    )

    def get_attribute_value(self, attribute_name: str):
        """
        Get the value of an attribute with the given name.

        Args:
            attribute_name (str): The name of the attribute to retrieve the value of.

        Returns:
            The value of the attribute, or None if the attribute does not exist.
        """
        if attribute_name not in self.all_attribute_names:
            LOGGER.error(
                "Error! No valid attribute '{}' in the node {}".format(
                    attribute_name, self.node_name
                )
            )
            return

        return self[attribute_name].get_value()

    def connect_attribute(
        self,
        attribute_name: str,
        other_node: GeneralLogicNode,
        other_attribute_name: str,
    ):
        """
        Connect the given attribute of this node to the given attribute of another node.

        Args:
            attribute_name (str): The name of the attribute in this node.
            other_node (GeneralLogicNode): The other node to connect to.
            other_attribute_name (str): The name of the attribute in the other node.

        Returns:
            The result of the connection between the source attribute and the target attribute.
        """
        source_attr = self[attribute_name]
        target_attr = other_node[other_attribute_name]
        return source_attr.connect_to_other(target_attr)

    # CHECKS ----------------------
    def is_starting_node(self) -> bool:
        """
        Determine whether or not this node can be a starting point for execution.

        Returns:
            bool
        """
        # If the node has some inputs connected, it is not a starting point
        for attr in self.all_attributes:
            if attr.has_input_connected():
                return False

        # Then, count all non-optional inputs
        needed_input_attrs_count = 0
        for attr in self.all_attributes:
            if attr.connector_type == constants.INPUT and not attr.is_optional:
                if attr.is_empty():
                    needed_input_attrs_count += 1

        if needed_input_attrs_count == 0:
            return True

        return False

    def check_all_inputs_have_value(self) -> bool:
        """
        Check if all needed input attributes have a value.

        Returns:
            bool: True if all needed input attributes have a value, False otherwise.
        """
        not_set_attrs = []
        for attr in self.get_input_attrs():
            if attr.is_optional and attr.is_empty():
                if attr.has_input_connected():
                    not_set_attrs.append(attr.dot_name)
            elif attr.is_empty():
                not_set_attrs.append(attr.dot_name)

        if not_set_attrs:
            LOGGER.warning(
                "Some input attributes of node {} not set: {}".format(
                    self.full_name, not_set_attrs
                )
            )
            return False

        return True

    def check_all_outputs_have_value(self) -> bool:
        """
        Check if all needed output attributes have a value.

        Returns:
            bool: True if all output attributes have a value, False otherwise.
        """
        not_set_attrs = []
        for attr in self.get_output_attrs():
            if attr.is_empty() and not attr.is_optional:
                not_set_attrs.append(attr.dot_name)

        if not_set_attrs:
            LOGGER.warning(
                "Some output attributes of node {} not set: {}".format(
                    self.full_name, not_set_attrs
                )
            )
            return False

        return True

    # CONTEXT ----------------------
    def is_in_root(self):
        """
        Check if the node is in the root context.

        Returns:
            bool
        """
        return self.context is None

    def build_internal(self):
        """
        Build the internal scene for the context node.

        If the node is not a context node, the function returns without doing anything.
        """
        if not self.IS_CONTEXT:
            return

        from all_nodes.logic.logic_scene import LogicScene

        LOGGER.debug(
            "Building internal scene for context node {}".format(self.full_name)
        )

        self.internal_scene = LogicScene()
        self.internal_scene.context = self
        self.internal_scene.set_name(self.full_name)

        context_definition_file = os.path.join(
            os.path.dirname(os.path.abspath(self.FILEPATH)),
            self.class_name + ".ctx",
        )
        if os.path.isfile(context_definition_file):
            self.CONTEXT_DEFINITION_FILE = context_definition_file
            self.internal_scene.load_from_file(self.CONTEXT_DEFINITION_FILE)
            self.internal_scene.set_context_to_nodes()
        else:
            raise RuntimeError(
                "No context definition file found for {}. Expected at: {}".format(
                    self.class_name, context_definition_file
                )
            )

    def set_context(self, context: GeneralLogicNode):
        """
        Set the context for this node.

        Args:
            context (GeneralLogicNode): The context to set this node as part of
        """
        self.context = context

    # RUN ----------------------
    def _run(self, execute_connected=True):
        """
        Run the node.

        Parameters:
            execute_connected (bool): Whether to execute connected nodes. Default is True
        """
        # ------------------- PRE-CHECKS ------------------- #
        # --------------- Status
        if self.success not in [constants.NOT_RUN, constants.IN_LOOP]:
            LOGGER.warning(
                "Cannot execute node {} it has already been executed!".format(
                    self.full_name
                )
            )
            self.signaler.finished.emit()
            return

        # --------------- If inactive, lets just skip it
        if not self.active:
            LOGGER.warning(
                "Skipping execution of {}".format(
                    self.full_name,
                )
            )

            self.success = constants.NOT_RUN
            self.set_output(constants.COMPLETED, Run())
            self.propagate_results()

            self.signaler.finished.emit()

            # Execute connected, if they can (might be missing inputs from this one)
            if execute_connected:
                for node in self.out_connected_nodes():
                    LOGGER.info(
                        "From {} (skipped), launching execution of {}".format(
                            self.full_name, node.full_name
                        )
                    )
                    node._run()
                return

        # --------------- Check inputs
        if not self.check_all_inputs_have_value():
            LOGGER.debug(
                "Cannot execute node {} now, some input attributes are not set".format(
                    self.full_name
                )
            )
            self.signaler.finished.emit()
            return

        # ------------------- START EXECUTION ------------------- #
        LOGGER.info(
            "Starting execution of {} ({})".format(self.full_name, self.class_name)
        )
        self.execution_counter += 1

        t1 = time.time()
        self.run_date = datetime.datetime.now()
        self.signaler.is_executing.emit()

        # --------------- Clear any previous logging
        self.fail_log = []
        self.error_log = []

        # --------------- Run
        if self.IS_CONTEXT:
            self.internal_scene.run_all_nodes(
                spawn_thread=False
            )  # TODO maybe this can be improved? / recursive
            internal_failures = self.internal_scene.gather_failed_nodes_logs()
            if internal_failures:
                for f in internal_failures:
                    self.fail(f)
            internal_errors = self.internal_scene.gather_errored_nodes_logs()
            if internal_errors:
                for e in internal_errors:
                    self.error(e)

        else:
            try:
                self.run()
            except Exception as e:
                self.error(str(e))
                LOGGER.exception(e)
                self.signaler.finished.emit()
                self.execution_time = time.time() - t1
                return

        # --------------- Result of Run
        if self.success == constants.FAILED:
            LOGGER.error(
                "Execution of {} FAILED, cannot keep executing from this node".format(
                    self.full_name
                )
            )
            self.signaler.finished.emit()
            self.execution_time = time.time() - t1
            return

        elif self.success == constants.ERROR:
            LOGGER.error(
                "Execution of {} ERRORED, cannot keep executing from this node".format(
                    self.full_name
                )
            )
            self.signaler.finished.emit()
            self.execution_time = time.time() - t1
            return

        # --------------- Check outputs were all set during Run
        if not self.check_all_outputs_have_value():
            LOGGER.error(
                "Something went wrong, not all output attributes are set in {}, "
                "cannot keep executing from this node".format(self.full_name)
            )
            self.fail("Not all output attributes are set")
            self.execution_time = time.time() - t1
            return

        # --------------- Mark successful
        self.success = constants.SUCCESSFUL
        self.set_output(constants.COMPLETED, Run())

        # --------------- Propagate results
        LOGGER.debug(
            "From {}, propagating out attributes to connected nodes".format(
                self.full_name
            )
        )
        self.propagate_results()

        # --------------- Stop timer and emit signal
        self.execution_time = time.time() - t1
        self.signaler.finished.emit()

        # --------------- Execute connected
        if execute_connected:
            for node in self.out_connected_nodes():
                if node.success not in [constants.FAILED, constants.ERROR]:
                    LOGGER.info(
                        "From {}, launching execution of {}".format(
                            self.full_name, node.full_name
                        )
                    )
                    node._run()

    def run_single(self):
        """
        Run only this node.
        """
        self._run(execute_connected=False)

    def run_chain(self):
        """
        Run this node and then all the nodes connected to its outputs.
        """
        self._run(execute_connected=True)

    def run(self):
        """
        To be reimplemented in each subclass.
        """
        if self.IS_CONTEXT:
            LOGGER.debug("Contexts do not need to implement the 'run' method")
        else:
            self.fail(
                "Class '{}' does not have the 'run' method implemented!".format(
                    self.class_name
                )
            )

    def fail(self, message=None):
        """
        Mark this node as failed.

        Args:
            message (str): Optional message to display when failed
        """
        self.success = constants.FAILED
        if message:
            LOGGER.error(
                "{} FAILED: {}. Cannot keep executing from this node".format(
                    self.full_name, message
                )
            )
            self.fail_log.append(message)

    def error(self, message=None):
        """
        Mark this node as errored.

        Args:
            message (str): Optional message to display when errored
        """
        self.success = constants.ERROR
        if message:
            LOGGER.error(
                "{} ERRORED: {}. Cannot keep executing from this node".format(
                    self.full_name, message
                )
            )
            self.error_log.append(message)

    def mark_skipped(self):
        """
        Mark this node as skipped.
        """
        self.success = constants.SKIPPED
        self.signaler.finished.emit()

    def propagate_results(self):
        """
        Propagate the values of calculated output attrs to the other connected nodes input attrs.
        """
        for attr in self.get_output_attrs():
            attr.propagate_value()

    def reset(self):
        """
        Reset this node.

        Marks the node as not-executed, and all information that could have been left by a
        previous execution (input values, logs...).
        """
        LOGGER.info("Resetting node " + self.full_name)
        for attr in self.get_input_attrs():
            if attr.has_connections():
                attr.clear()
        for attr in self.get_output_attrs():
            attr.clear()

        self.success = constants.NOT_RUN
        self.fail_log = []
        self.error_log = []
        self.execution_time = 0

        if self.IS_CONTEXT:
            self.internal_scene.reset_all_nodes()

    def soft_reset(self):
        """
        Perform a 'soft reset'

        Mainly for debugging purposes. Will reset the status of the node so it can be run, but without
        deleting the input values of it.
        """
        LOGGER.info("Soft-resetting node " + self.full_name)

        self.success = constants.NOT_RUN
        self.fail_log = []
        self.error_log = []
        self.execution_time = 0

        if self.IS_CONTEXT:
            self.internal_scene.soft_reset_all_nodes()

    def toggle_activated(self):
        """Toggle the activated state of the node."""
        self.active = not self.active
        return self.active

    # SPECIAL METHODS ----------------------
    def __getitem__(self, item: str):
        for attr in self.all_attributes:
            if attr.attribute_name == item:
                return attr
        LOGGER.error(
            "Error, no attribute with that name {}.{}".format(self.full_name, item)
        )
        return None

    def __str__(self):
        return "<{} object>".format(
            self.full_name,
        )

    def __repr__(self):
        return "<{} object>".format(
            self.full_name,
        )

    def get_node_html_help(self):
        """
        Get the node's help documentation parsed into an html text.

        Returns:
            str: with the complete text of the help
        """
        help_text = f"<h1>{self.class_name}</h1>"
        help_text += (
            f"<p style='white-space:pre'>Class defined at:<br>{self.FILEPATH}</p>"
        )

        if self.HELP:
            help_text += f"<p style='white-space:pre'>HELP:<br>{self.HELP}"

        help_text += (
            "<h4><br>INPUTS_DICT:</h4><p style='white-space:pre; background-color:black'><code>"
            + pprint.pformat(self.INPUTS_DICT, indent=2)
            .replace(">", "&gt;")
            .replace("<", "&lt;")
            .replace("\n", "<br>")
            + "</code></p>"
        )

        help_text += (
            "<h4>OUTPUTS_DICT:</h4><p style='white-space:pre; background-color:black'><code>"
            + pprint.pformat(self.OUTPUTS_DICT, indent=2)
            .replace(">", "&gt;")
            .replace("<", "&lt;")
            .replace("\n", "<br>")
            + "</code></p>"
        )

        help_text += (
            "<h4>INTERNALS_DICT:</h4><p style='white-space:pre; background-color:black'><code>"
            + pprint.pformat(self.INTERNALS_DICT, indent=2)
            .replace(">", "&gt;")
            .replace("<", "&lt;")
            .replace("\n", "<br>")
            + "</code></p>"
        )

        return help_text


class LogicNodeSignaler(QtCore.QObject):
    """
    Defines the signals available from a logic node.
    """

    status_changed = QtCore.Signal()
    is_executing = QtCore.Signal()
    finished = QtCore.Signal()


# -------------------------------- ATTRIBUTE -------------------------------- #
class GeneralLogicAttribute:
    def __init__(
        self,
        parent_node: GeneralLogicNode,
        attribute_name: str,
        connector_type: str,
        data_type,
        value=None,
        is_optional=False,
    ):
        self.parent_node = parent_node

        self.attribute_name = attribute_name
        self.connector_type = connector_type  # IN or OUT
        self.data_type = data_type
        self.value = value
        self.is_optional = is_optional

        self.connected_attributes = set()

    # PROPERTIES ----------------------
    @property
    def dot_name(self):
        return self.parent_node.node_name + "." + self.attribute_name

    @property
    def full_name(self):
        return self.parent_node.full_name + "." + self.attribute_name

    # GET AND SET ----------------------
    def get_value(self):
        return self.value

    def is_empty(self) -> bool:
        """
        Check if the value of the attribute is None.

        Returns:
            bool
        """
        return self.value is None

    def set_value(self, new_value):
        """
        Set the value of the attribute to the given new value.

        Args:
            new_value (Any): The new value to set the object to.
        """
        self.value = new_value
        LOGGER.debug("Setting {} to new value {}".format(self.full_name, self.value))

    def clear(self):
        """
        Clear the value of the attribute.

        This method sets the value of the attribute to None, effectively clearing its current value.
        """
        self.value = None

    # CONNECTIONS ----------------------
    def get_connections_list(self):
        """
        Get a list of connections where this attribute is involved.

        Returns:
            list: A list of lists, where each list contains the dot names of two connected attributes.
        """
        connections = []
        if self.has_connections():
            for connected_attr in self.connected_attributes:
                if self.connector_type == constants.INPUT:
                    connections.append([connected_attr.dot_name, self.dot_name])
                else:
                    connections.append([self.dot_name, connected_attr.dot_name])

        return connections

    def has_input_connected(self) -> bool:
        """Determine whether or not this attribute has incoming connections.

        Returns:
            bool: whether or not the attribute has any incoming connection
        """
        return (
            self.connector_type == constants.INPUT
            and len(self.connected_attributes) > 0
        )

    def has_connections(self) -> bool:
        """Determine whether or not this attribute is connected to another.

        Returns:
            bool: whether or not the attribute has any connection
        """
        return len(self.connected_attributes) > 0

    def connect_to_other(self, other_attribute: GeneralLogicAttribute) -> tuple:
        """
        Connect this attribute to another.

        Args:
            other_attribute (GeneralLogicAttribute)

        Returns:
            tuple(bool, str): whether or not the connection could be done, log of the reason
        """
        # Checks -------------------------
        # Cycles check
        if self.connector_type == constants.INPUT:
            if other_attribute.parent_node.check_cycles(self.parent_node):
                connection_warning = "Cannot connect, cycle detected!"
                LOGGER.warning(connection_warning)
                return (False, connection_warning)
        elif self.connector_type == constants.OUTPUT:
            if self.parent_node.check_cycles(other_attribute.parent_node):
                connection_warning = "Cannot connect, cycle detected!"
                LOGGER.warning(connection_warning)
                return (False, connection_warning)

        # Different nodes check
        if not self.parent_node != other_attribute.parent_node:
            connection_warning = "Cannot connect {} and {}, both same node {}".format(
                self.dot_name,
                other_attribute.dot_name,
                self.parent_node.full_name,
            )
            LOGGER.warning(connection_warning)
            return (False, connection_warning)

        # IN - OUT check
        if not self.connector_type != other_attribute.connector_type:
            connection_warning = "Cannot connect {} and {}, both are {}".format(
                self.dot_name, other_attribute.dot_name, self.connector_type
            )
            LOGGER.warning(connection_warning)
            return (False, "Cannot connect both are {}".format(self.connector_type))

        # Datatype check
        connection_direction = "->"
        if self.connector_type == constants.INPUT:
            connection_direction = "<-"
        if self.data_type != other_attribute.data_type:
            if object not in [self.data_type, other_attribute.data_type]:
                connection_warning = (
                    "Cannot connect {} {} {}, different datatypes {}{}{}".format(
                        self.dot_name,
                        connection_direction,
                        other_attribute.dot_name,
                        self.get_datatype_str(),
                        connection_direction,
                        other_attribute.get_datatype_str(),
                    )
                )
                LOGGER.warning(connection_warning)
                return (
                    False,
                    "Cannot connect, different datatypes {}{}{}".format(
                        self.get_datatype_str(),
                        connection_direction,
                        other_attribute.get_datatype_str(),
                    ),
                )

        # Connection -------------------------
        if self.connector_type == constants.OUTPUT:
            self.connected_attributes.add(other_attribute)
            other_attribute.connected_attributes = {self}
        else:
            self.connected_attributes = {other_attribute}
            other_attribute.connected_attributes.add(self)

        connection_log = "Connected {} {} {}".format(
            self.dot_name, connection_direction, other_attribute.dot_name
        )
        LOGGER.info(connection_log)

        return (True, connection_log)

    def disconnect_from_other(self, other_attribute: GeneralLogicAttribute):
        """
        Disconnect this attribute from another.

        Args:
            other_attribute (GeneralLogicAttribute)
        """
        self.connected_attributes.remove(other_attribute)
        other_attribute.connected_attributes.remove(self)
        if self.connector_type == constants.OUTPUT:
            LOGGER.info(
                "Disconnected {} -/- {}".format(self.dot_name, other_attribute.dot_name)
            )
        else:
            LOGGER.info(
                "Disconnected {} -/- {}".format(other_attribute.dot_name, self.dot_name)
            )

    def disconnect_input(self):
        """
        Disconnect incoming inputs to this attribute.
        """
        if self.connector_type == constants.INPUT and self.connected_attributes:
            self.disconnect_from_other(next(iter(self.connected_attributes)))

    # UTILITY ----------------------
    def get_datatype_str(self) -> str:
        """
        Get a string representation of the datatype that this attribute can hold.

        Returns:
            str: with a representation fo the datatype
        """
        return utils.parse_datatype(str(self.data_type))

    def propagate_value(self):
        """
        Propagate the value of this attribute to all its connected attributes.
        """
        for connected_attr in self.connected_attributes:
            connected_attr.set_value(self.value)

    # SPECIAL METHODS ----------------------
    def __str__(self):
        return "GeneralLogicAttribute: {}, value:{}".format(self.dot_name, self.value)


# -------------------------------- UTILITY -------------------------------- #
class Run:
    """
    Utility class with no functionality
    """

    def __str__(self):
        return "Run"


class RunLoop:
    """
    Utility class with no functionality
    """

    def __str__(self):
        return "RunLoop"
