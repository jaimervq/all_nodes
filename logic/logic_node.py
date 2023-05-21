# -*- coding: UTF-8 -*-
from __future__ import annotations

__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"

import ast
import datetime
import inspect
import os
import pprint
import re
import time
import uuid

from all_nodes import constants
from all_nodes import utils

LOGGER = utils.get_logger(__name__)


# -------------------------------- NODES -------------------------------- #
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

    NICE_NAME = None
    HELP = ""

    INPUTS_DICT = {}
    OUTPUTS_DICT = {}

    IS_CONTEXT = False
    CONTEXT_DEFINITION_FILE = None

    VALID_NAMING_PATTERN = "^[A-Z]+[a-zA-Z0-9_]*$"

    def __init__(self):

        # General properties
        self.class_name = type(self).__name__
        self.node_name = self.class_name + "_1"
        self.uuid = str(uuid.uuid4())

        # Attributes
        self.all_attributes = []
        self.check_attributes_validity()
        self.create_attributes()

        # Context it belongs to
        self.context = None

        # Is context
        self.internal_scene = None
        self.build_internal()

        # Run
        self.success = constants.NOT_RUN

        self.fail_log = []
        self.error_log = []

        self.run_date = None
        self.execution_time = 0

        # Feedback
        LOGGER.debug("Initialized node! {}".format(self.class_name))

    # UTILITY ----------------------
    @staticmethod
    def name_is_valid(name):
        if re.match(GeneralLogicNode.VALID_NAMING_PATTERN, name):
            return True
        return False

    def rename(self, new_name):
        if self.node_name == new_name:
            return True

        if self.name_is_valid(new_name):
            LOGGER.debug("Renamed node '{}' to '{}'".format(self.node_name, new_name))
            self.node_name = new_name
            return True
        else:
            LOGGER.warning("Name proposed for node is not valid: {}".format(new_name))

        return False

    def force_rename(self, new_name):
        LOGGER.debug(
            "Forcing renaming of node '{}' to '{}'".format(self.node_name, new_name)
        )
        self.node_name = new_name
        return True

    def get_max_in_or_out_count(self):
        return max(len(self.get_input_attrs()), len(self.get_output_attrs()))

    def get_node_full_dict(self):
        out_dict = dict()

        out_dict["class_name"] = self.class_name
        out_dict["node_name"] = self.node_name
        out_dict["full_name"] = self.full_name
        out_dict["uuid"] = self.uuid

        out_dict["node_attributes"] = dict()
        for attr in self.all_attributes:
            out_dict["node_attributes"][attr.dot_name] = dict()
            out_dict["node_attributes"][attr.dot_name][
                "attribute_name"
            ] = attr.attribute_name
            out_dict["node_attributes"][attr.dot_name]["value"] = str(attr.value)
            out_dict["node_attributes"][attr.dot_name][
                "connector_type"
            ] = attr.connector_type
            out_dict["node_attributes"][attr.dot_name]["is_optional"] = attr.is_optional
            out_dict["node_attributes"][attr.dot_name]["data_type"] = attr.get_datatype_str()
            out_dict["node_attributes"][attr.dot_name][
                "data_type_str"
            ] = attr.get_datatype_str()
            out_dict["node_attributes"][attr.dot_name]["connected_to"] = [
                c_attr.dot_name for c_attr in attr.connected_attributes
            ]

        out_dict["success"] = self.success

        out_dict["error_log"] = self.error_log
        out_dict["fail_log"] = self.fail_log

        out_dict["run_date"] = self.run_date
        out_dict["execution_time"] = self.execution_time

        out_dict["IS_CONTEXT"] = self.IS_CONTEXT

        connections = list()
        for attr in self.all_attributes:
            connections += attr.get_connections_list()
        out_dict["connections"] = connections

        return out_dict

    def get_node_basic_dict(self):
        out_dict = dict()

        out_dict[self.node_name] = dict()
        out_dict[self.node_name]["class_name"] = self.class_name

        out_dict[self.node_name]["node_attributes"] = dict()
        for attr in self.all_attributes:
            if (
                attr.attribute_name not in [constants.START, constants.COMPLETED]
                and attr.value is not None
            ):
                out_dict[self.node_name]["node_attributes"][
                    attr.attribute_name
                ] = attr.value
        if not out_dict[self.node_name]["node_attributes"]:
            out_dict[self.node_name].pop("node_attributes")

        return out_dict

    def get_out_connections(self):
        connections_list = list()
        for attr in self.get_output_attrs():
            for connected in attr.connected_attributes:
                connections_list.append([attr.dot_name, connected.dot_name])
        return connections_list

    def out_connected_nodes(self):
        connected_nodes = set()
        for attr in self.get_output_attrs():
            for connected_attr in attr.connected_attributes:
                connected_nodes.add(connected_attr.parent_node)
        return connected_nodes

    # PROPERTIES ----------------------
    @property
    def full_name(self):
        if self.context:
            return self.context.full_name + "." + self.node_name
        else:
            return self.node_name

    @property
    def all_attribute_names(self):
        return [a.attribute_name for a in self.all_attributes]

    # ATTRIBUTES ----------------------
    def check_attributes_validity(self):
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
        # Add a special "Run control" START attribute that will be in all nodes
        start_attr = GeneralLogicAttribute(
            self, constants.START, constants.INPUT, Run, is_optional=True
        )
        self.all_attributes.append(start_attr)

        # Add all in and out attributes that have been defined
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

    def get_input_attrs(self):
        """
        Get all the input attributes of the node.

        Returns:
            list: with all the input attributes
        """
        return [
            attr
            for attr in self.all_attributes
            if attr.connector_type == constants.INPUT
        ]

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
                "Error! No valid attribute {} in the node".format(attribute_name)
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
        if attribute_name not in self.all_attribute_names:
            LOGGER.error(
                "Error! No valid attribute {} in the node".format(attribute_name)
            )
            return

        if value_str == "":
            for attribute in self.all_attributes:
                if attribute.attribute_name == attribute_name:
                    attribute.clear()
                    return

        for attribute in self.all_attributes:
            if attribute.attribute_name == attribute_name:
                if attribute.data_type == str:
                    attribute.set_value(value_str)
                elif attribute.data_type == float:
                    attribute.set_value(float(value_str))
                elif attribute.data_type == int:
                    attribute.set_value(int(value_str))
                elif attribute.data_type == bool:
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
                elif attribute.data_type in (dict, list, object):
                    attribute.set_value(
                        ast.literal_eval(value_str)
                    )  # TODO revisit this for malformed lists, dicts, etc
                else:
                    LOGGER.error(
                        "Cannot set value {} to type {}, not defined how to cast from string".format(
                            value_str, attribute.data_type
                        )
                    )

    def get_attribute_value(self, attribute_name: str):
        if attribute_name not in self.all_attribute_names:
            LOGGER.error(
                "Error! No valid attribute {} in the node".format(attribute_name)
            )
            return

        return self[attribute_name].get_value()

    def connect_attribute(
        self,
        attribute_name: str,
        other_node: GeneralLogicNode,
        other_attribute_name: str,
    ):
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
    def build_internal(self):
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

    def set_context(self, context):
        self.context = context

    # RUN ----------------------
    def _run(self, execute_connected=True):

        # Start timer
        t1 = time.time()
        self.run_date = str(datetime.datetime.now())

        # Check inputs
        if not self.check_all_inputs_have_value():
            LOGGER.warning(
                "Cannot execute node {} now, some input attributes are not set".format(
                    self.full_name
                )
            )
            return

        # Feedback
        LOGGER.info(
            "Starting execution of {} ({})".format(self.full_name, self.class_name)
        )

        # Clear any previous logging
        self.fail_log = []
        self.error_log = []

        # Run
        if self.IS_CONTEXT:
            self.internal_scene.run_all_nodes()
            internal_failures = self.internal_scene.gather_failed_nodes()
            if internal_failures:
                for f in internal_failures:
                    self.fail(f)
            internal_errors = self.internal_scene.gather_errored_nodes()
            if internal_errors:
                for e in internal_errors:
                    self.error(e)

        else:
            try:
                self.run()
            except Exception as e:
                self.error(str(e))
                LOGGER.exception(e)
                return

        # Result of Run
        if self.success == constants.FAILED:
            LOGGER.error(
                "Execution of {} FAILED, cannot keep executing from this node".format(
                    self.full_name
                )
            )
            return
        elif self.success == constants.ERROR:
            LOGGER.error(
                "Execution of {} ERRORED, cannot keep executing from this node".format(
                    self.full_name
                )
            )
            return

        # Check outputs were all set during Run
        if not self.check_all_outputs_have_value():
            LOGGER.error(
                "Something went wrong, not all output attributes are set in {}, "
                "cannot keep executing from this node".format(self.full_name)
            )
            self.fail("Not all output attributes are set")
            return

        # Mark successful
        self.success = constants.SUCCESSFUL
        self.set_output(constants.COMPLETED, Run())

        # Propagate results
        LOGGER.debug(
            "From {}, propagating out attributes to connected nodes".format(
                self.full_name
            )
        )
        self.propagate_results()

        # Stop timer
        self.execution_time = time.time() - t1

        # Execute connected
        if execute_connected:
            for node in self.out_connected_nodes():
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

    def propagate_results(self):
        for attr in self.get_output_attrs():
            attr.propagate_value()

    def reset(self):
        """
        Reset this node.

        Clearing as much information as possible that could have been left by a previous execution.
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
        return "<{} object>".format(self.full_name, self.class_name)

    def __repr__(self):
        return "<{} object>".format(self.full_name, self.class_name)

    def get_node_html_help(self):
        """
        Get the node's help documentation parsed into an html text.

        Returns:
            str: with the complete text of the help
        """
        help_text = " <b><font size = 5>{0}</b>".format(self.class_name)
        help_text += "<br><font size = 2>" + self.__module__

        if self.HELP:
            help_text += "<br><br><font size = 3>HELP: " + self.HELP

        help_text += "<br><br><br><font size=3>INPUTS_DICT:<br>" + pprint.pformat(
            self.INPUTS_DICT
        ).replace(">", ")").replace("<", "(")

        help_text += "<br><br><font size=3>OUTPUTS_DICT:<br>" + pprint.pformat(
            self.OUTPUTS_DICT
        ).replace(">", ")").replace("<", "(")

        return help_text


class SpecialInputNode(GeneralLogicNode):
    """
    Special type of node. When represented graphically, will accept direct input though a widget.
    """

    INPUT_TYPE = None

    def run(self):
        pass

    def set_special_attr_value(self, attribute_name: str, value):
        for attribute in self.all_attributes:
            if attribute.attribute_name == attribute_name:
                LOGGER.debug(
                    "Setting special attribute {} to {}".format(
                        attribute.dot_name, value
                    )
                )
                self.set_attribute_value(attribute_name, value)
                return

    def get_node_full_dict(self):
        node_dict = super().get_node_full_dict()
        for attr in self.all_attributes:
            if (
                "out_" in attr.attribute_name
                and attr.get_datatype_str() in attr.attribute_name
            ):
                node_dict["special_attr_value"] = attr.value
                return node_dict

    def reset(self):
        """
        Reset attributes of the node.

        These nodes are special, we cannot reset their out attributes directly, as they are mainly established
        and manipulated through the GUI.
        """
        LOGGER.info(
            "Not resetting all of special node {} attrs, some are supposed to be modified through GUI".format(
                self.full_name
            )
        )
        for attr in self.all_attributes:
            if attr.attribute_name in [constants.START, constants.COMPLETED]:
                attr.clear()

        self.success = constants.NOT_RUN

        self.fail_log = []
        self.error_log = []


# -------------------------------- ATTRIBUTES -------------------------------- #
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
        return self.value is None

    def set_value(self, new_value):
        self.value = new_value
        LOGGER.debug("Setting {} to new value {}".format(self.full_name, self.value))

    def clear(self):
        self.value = None

    # CONNECTIONS ----------------------
    def get_connections_list(self):
        connections = []
        if self.has_connections():
            for connected_attr in self.connected_attributes:
                if self.connector_type == constants.INPUT:
                    connections.append([connected_attr.dot_name, self.dot_name])
                else:
                    connections.append([self.dot_name, connected_attr.dot_name])

        return connections

    def has_input_connected(self) -> bool:
        return (
            self.connector_type == constants.INPUT
            and len(self.connected_attributes) > 0
        )

    def has_connections(self) -> bool:
        return len(self.connected_attributes) > 0

    def connect_to_other(self, other_attribute: GeneralLogicAttribute) -> bool:
        """
        Connect this attribute to another.

        Args:
            other_attribute (GeneralLogicAttribute)

        Returns:
            bool: whether or not the connection could be done
        """
        if not self.parent_node != other_attribute.parent_node:
            LOGGER.warning(
                "Cannot connect {} and {}, both same node {}".format(
                    self.dot_name,
                    other_attribute.dot_name,
                    self.parent_node.full_name,
                )
            )
            return False

        if not self.connector_type != other_attribute.connector_type:
            LOGGER.warning(
                "Cannot connect {} and {}, both are {}".format(
                    self.dot_name, other_attribute.dot_name, self.connector_type
                )
            )
            return False

        connection_direction = "->"
        if self.connector_type == constants.INPUT:
            connection_direction = "<-"
        if not self.data_type == other_attribute.data_type:
            if object not in [self.data_type, other_attribute.data_type]:
                LOGGER.warning(
                    "Cannot connect {} {} {}, different datatypes {}{}{}".format(
                        self.dot_name,
                        connection_direction,
                        other_attribute.dot_name,
                        self.get_datatype_str(),
                        connection_direction,
                        other_attribute.get_datatype_str(),
                    )
                )
                return False

        if self.connector_type == constants.OUTPUT:
            self.connected_attributes.add(other_attribute)
            other_attribute.connected_attributes = {self}
        else:
            self.connected_attributes = {other_attribute}
            other_attribute.connected_attributes.add(self)

        LOGGER.info(
            "Connected {} {} {}".format(
                self.dot_name, connection_direction, other_attribute.dot_name
            )
        )

        return True

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
        type = str(self.data_type)
        if "." in str(self.data_type):
            return re.search("'.+\.(.+)'", type).group(1)
        return re.search("'(.+)'", type).group(1)

    def propagate_value(self):
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
