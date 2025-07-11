# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class GetDictKey(GeneralLogicNode):
    NICE_NAME = "Get dict key"
    HELP = "Get given key from a dictionary"

    INPUTS_DICT = {
        "in_dict": {"type": dict},
        "key": {"type": str},
    }

    OUTPUTS_DICT = {"out": {"type": object}}

    def run(self):
        in_dict = self.get_attribute_value("in_dict")
        key = self.get_attribute_value("key")
        if key not in in_dict:
            self.fail("Key '{}' not present in input dict {}".format(key, in_dict))
            return
        self.set_output("out", in_dict[key])


class SetDictKey(GeneralLogicNode):
    NICE_NAME = "Set dict key"
    HELP = "Set a key in a dictionary"

    INPUTS_DICT = {
        "in_dict": {"type": dict},
        "key": {"type": str},
        "new_value": {"type": object},
    }

    OUTPUTS_DICT = {"out_dict": {"type": dict}}

    def run(self):
        in_dict = self.get_attribute_value("in_dict")
        key = self.get_attribute_value("key")
        new_value = self.get_attribute_value("new_value")

        in_dict[key] = new_value
        self.set_output("out_dict", in_dict)


class CreateDictFromScratch(GeneralLogicNode):
    NICE_NAME = "Dict from scratch"
    HELP = "Create a dictionary from scratch, given keys and values"

    INPUTS_DICT = {
        "key_0": {"type": object},
        "value_0": {"type": object},
        "key_1": {"type": object},
        "value_1": {"type": object},
        "key_2": {"type": object, "optional": True},
        "value_2": {"type": object, "optional": True},
        "key_3": {"type": object, "optional": True},
        "value_3": {"type": object, "optional": True},
        "key_4": {"type": object, "optional": True},
        "value_4": {"type": object, "optional": True},
    }

    OUTPUTS_DICT = {"out_dict": {"type": dict}}

    def run(self):
        out_dict = {}
        for i in range(5):
            key = self.get_attribute_value("key_{}".format(i))
            value = self.get_attribute_value("value_{}".format(i))
            if key is not None and value is not None:
                out_dict[key] = value
        self.set_output("out_dict", out_dict)
