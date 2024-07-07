__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class StringSplit(GeneralLogicNode):
    NICE_NAME = "String split"

    INPUTS_DICT = {
        "in_str": {"type": str},
        "split_char": {"type": str, "optional": True},
    }

    OUTPUTS_DICT = {"out_list": {"type": list}}

    def run(self):
        in_str = self.get_attribute_value("in_str")
        split_char = self.get_attribute_value("split_char") or " "

        split_list = in_str.split(split_char)
        if split_char == "\\n":
            split_list = in_str.splitlines()

        self.set_output("out_list", split_list)


class StringFormat(GeneralLogicNode):
    INPUTS_DICT = {
        "in_str": {"type": str},
        "format_dict": {"type": dict},
    }

    OUTPUTS_DICT = {"out_str": {"type": str}}

    def run(self):
        in_str = self.get_attribute_value("in_str")
        format_dict = self.get_attribute_value("format_dict")

        self.set_output("out_str", in_str.format(**format_dict))
