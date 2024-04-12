# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.constants import InputsGUI
from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class StrInput(GeneralLogicNode):
    NICE_NAME = "String input"

    OUTPUTS_DICT = {"out_str": {"type": str}}

    INTERNALS_DICT = {
        "internal_str": {"type": str, "gui_type": InputsGUI.STR_INPUT},
    }

    def run(self):
        self.set_output("out_str", self.get_attribute_value("internal_str"))


class MultilineStrInput(GeneralLogicNode):
    NICE_NAME = "Multiline string input"
    HELP = ""

    OUTPUTS_DICT = {"out_str": {"type": str}}

    INTERNALS_DICT = {
        "internal_str": {"type": str, "gui_type": InputsGUI.MULTILINE_STR_INPUT},
    }

    def run(self):
        self.set_output("out_str", self.get_attribute_value("internal_str"))


class BoolInput(GeneralLogicNode):
    NICE_NAME = "Boolean input"
    HELP = ""

    OUTPUTS_DICT = {"out_bool": {"type": bool}}

    INTERNALS_DICT = {
        "internal_bool": {"type": bool, "gui_type": InputsGUI.BOOL_INPUT},
    }

    def run(self):
        self.set_output("out_bool", self.get_attribute_value("internal_bool"))


class DictInput(GeneralLogicNode):
    NICE_NAME = "Dictionary input"
    HELP = ""

    OUTPUTS_DICT = {"out_dict": {"type": dict}}

    INTERNALS_DICT = {
        "internal_dict": {"type": dict, "gui_type": InputsGUI.DICT_INPUT},
    }

    def run(self):
        internal_dict = self.get_attribute_value("internal_dict")
        if internal_dict is None:
            self.fail(
                "Looks like the dictionary was not properly formed! (Check the syntax)"
            )
        self.set_output("out_dict", self.get_attribute_value("internal_dict"))


class ListInput(GeneralLogicNode):
    NICE_NAME = "List input"
    HELP = ""

    OUTPUTS_DICT = {"out_list": {"type": list}}

    INTERNALS_DICT = {
        "internal_list": {"type": list, "gui_type": InputsGUI.LIST_INPUT},
    }

    def run(self):
        internal_list = self.get_attribute_value("internal_list")
        if internal_list is None:
            self.fail("Looks like the list was not properly formed! (Check the syntax)")
        self.set_output("out_list", self.get_attribute_value("internal_list"))


class TupleInput(GeneralLogicNode):
    NICE_NAME = "Tuple input"
    HELP = ""

    OUTPUTS_DICT = {"out_tuple": {"type": tuple}}

    INTERNALS_DICT = {
        "internal_tuple": {"type": tuple, "gui_type": InputsGUI.TUPLE_INPUT},
    }

    def run(self):
        internal_tuple = self.get_attribute_value("internal_tuple")
        if internal_tuple is None:
            self.fail(
                "Looks like the tuple was not properly formed! (Check the syntax)"
            )
        self.set_output("out_tuple", self.get_attribute_value("internal_tuple"))


class IntInput(GeneralLogicNode):
    NICE_NAME = "Integer input"
    HELP = ""

    OUTPUTS_DICT = {"out_int": {"type": int}}

    INTERNALS_DICT = {
        "internal_int": {"type": int, "gui_type": InputsGUI.INT_INPUT},
    }

    def run(self):
        self.set_output("out_int", self.get_attribute_value("internal_int"))


class FloatInput(GeneralLogicNode):
    NICE_NAME = "Float input"
    HELP = ""

    OUTPUTS_DICT = {"out_float": {"type": float}}

    INTERNALS_DICT = {
        "internal_float": {"type": float, "gui_type": InputsGUI.FLOAT_INPUT},
    }

    def run(self):
        self.set_output("out_float", self.get_attribute_value("internal_float"))


class OptionInput(GeneralLogicNode):
    OUTPUTS_DICT = {"out_str": {"type": str}}

    INTERNALS_DICT = {
        "internal_str": {
            "type": str,
            "gui_type": InputsGUI.OPTION_INPUT,
            "options": ["1", "2", "3"],
        },
    }

    def run(self):
        self.set_output("out_str", self.get_attribute_value("internal_str"))
