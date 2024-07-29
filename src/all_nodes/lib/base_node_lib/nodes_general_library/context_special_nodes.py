# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


# Nodes to grab input values from context ------------------------------------------
class GrabInputFromCtx(GeneralLogicNode):
    NICE_NAME = "CTX Input"
    HELP = "Get the value from an attribute that belongs to the parent node"

    INPUTS_DICT = {"in_parent_attr_name": {"type": str}}
    OUTPUTS_DICT = {"in_parent_attr_value": {"type": object}}

    def run(self):
        parent_attr_name = self.get_attribute_value("in_parent_attr_name")

        # Analize parent node
        parent_node = self.context
        if parent_node is None:
            self.error("This node has to be inside a context node!")
            return
        parent_attr = parent_node[parent_attr_name]
        parent_attr_value = parent_node.get_attribute_value(parent_attr_name)
        if not parent_attr:
            self.fail("Parent node has no attribute {}".format(parent_attr_name))
            return

        # Analize compatibility
        out_attr = self["in_parent_attr_value"]
        if parent_attr.data_type != out_attr.data_type:
            self.fail(
                "Parent attribute {0} ({1}) is different to output of this node {2} ({3}) : {1} != {3}".format(
                    parent_attr.dot_name,
                    parent_attr.get_datatype_str(),
                    out_attr.dot_name,
                    out_attr.get_datatype_str(),
                )
            )
            return

        # Analize connections
        for connected_attr in out_attr.connected_attributes:
            if parent_attr.data_type != connected_attr.data_type:
                self.fail(
                    "Parent attribute {0} ({1}) cannot be propagated to internal {2} ({3}) : {1} != {3}".format(
                        parent_attr.dot_name,
                        parent_attr.get_datatype_str(),
                        connected_attr.dot_name,
                        connected_attr.get_datatype_str(),
                    )
                )
                return

        self.set_output("in_parent_attr_value", parent_attr_value)


class GrabStrInputFromCtx(GrabInputFromCtx):
    NICE_NAME = "CTX Input (Str)"

    INPUTS_DICT = {"in_parent_attr_name": {"type": str}}
    OUTPUTS_DICT = {"in_parent_attr_value": {"type": str}}


class GrabDictInputFromCtx(GrabInputFromCtx):
    NICE_NAME = "CTX Input (Dict)"

    INPUTS_DICT = {"in_parent_attr_name": {"type": str}}
    OUTPUTS_DICT = {"in_parent_attr_value": {"type": dict}}


class GrabIntInputFromCtx(GrabInputFromCtx):
    NICE_NAME = "CTX Input (Int)"

    INPUTS_DICT = {"in_parent_attr_name": {"type": str}}
    OUTPUTS_DICT = {"in_parent_attr_value": {"type": int}}


class GrabBoolInputFromCtx(GrabInputFromCtx):
    NICE_NAME = "CTX Input (Bool)"

    INPUTS_DICT = {"in_parent_attr_name": {"type": str}}
    OUTPUTS_DICT = {"in_parent_attr_value": {"type": bool}}


# Nodes to set output values to context ------------------------------------------
class SetOutputToCtx(GeneralLogicNode):
    NICE_NAME = "CTX Output"

    INPUTS_DICT = {
        "out_parent_attr_name": {"type": str},
        "out_parent_attr_value": {"type": object},
    }

    def run(self):
        parent_attr_name = self.get_attribute_value("out_parent_attr_name")

        parent_node = self.context
        if parent_node is None:
            self.error("This node has to be inside a context node!")
            return
        parent_attr = parent_node[parent_attr_name]
        if not parent_attr:
            self.fail("Parent node has no attribute {}".format(parent_attr_name))
            return

        out_attr = self["out_parent_attr_value"]
        out_attr_value = self.get_attribute_value("out_parent_attr_value")
        if out_attr.data_type is not parent_attr.data_type:
            self.fail(
                "Value of {0} ({1}) cannot be propagated to parent {2} ({3}): {1} != {3}".format(
                    out_attr.dot_name,
                    out_attr.get_datatype_str(),
                    parent_attr.dot_name,
                    parent_attr.get_datatype_str(),
                )
            )
            return

        parent_node.set_output(parent_attr_name, out_attr_value)


class SetStrOutputToCtx(SetOutputToCtx):
    NICE_NAME = "CTX Output (Str)"

    INPUTS_DICT = {
        "out_parent_attr_name": {"type": str},
        "out_parent_attr_value": {"type": str},
    }


class SetDictOutputToCtx(SetOutputToCtx):
    NICE_NAME = "CTX Output (Dict)"

    INPUTS_DICT = {
        "out_parent_attr_name": {"type": str},
        "out_parent_attr_value": {"type": dict},
    }


class SetIntOutputToCtx(SetOutputToCtx):
    NICE_NAME = "CTX Output (Int)"

    INPUTS_DICT = {
        "out_parent_attr_name": {"type": str},
        "out_parent_attr_value": {"type": int},
    }


class SetBoolOutputToCtx(SetOutputToCtx):
    NICE_NAME = "CTX Output (Bool)"

    INPUTS_DICT = {
        "out_parent_attr_name": {"type": str},
        "out_parent_attr_value": {"type": bool},
    }
