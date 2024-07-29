__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class ListToStr(GeneralLogicNode):
    INPUTS_DICT = {
        "in_list": {"type": list},
        "join_character": {"type": str, "optional": True},
    }

    OUTPUTS_DICT = {"out_str": {"type": str}}

    def run(self):
        in_list = [str(elem) for elem in self.get_attribute_value("in_list")]
        join_character = self.get_attribute_value("join_character") or " "
        self.set_output("out_str", join_character.join(in_list))


class IntToStr(GeneralLogicNode):
    INPUTS_DICT = {
        "in_int": {"type": int},
    }

    OUTPUTS_DICT = {"out_str": {"type": str}}

    def run(self):
        in_int = self.get_attribute_value("in_int")
        self.set_output("out_str", str(in_int))


class ConcatStr(GeneralLogicNode):
    INPUTS_DICT = {
        "in_str_0": {"type": str},
        "in_str_1": {"type": str},
        "in_str_2": {"type": str, "optional": True},
        "in_str_3": {"type": str, "optional": True},
        "in_str_4": {"type": str, "optional": True},
    }

    OUTPUTS_DICT = {"out_str": {"type": str}}

    def run(self):
        out_str = ""
        for i in range(5):
            attr_name = "in_str_{}".format(i)
            val = self.get_attribute_value(attr_name)
            if val is not None:
                out_str += val
        self.set_output("out_str", out_str)


class MultiToStr(GeneralLogicNode):
    INPUTS_DICT = {
        "in_int": {"type": int, "optional": True},
        "in_float": {"type": float, "optional": True},
        "in_bool": {"type": bool, "optional": True},
        "in_dict": {"type": dict, "optional": True},
        "in_object": {"type": object, "optional": True},
    }

    OUTPUTS_DICT = {
        "[NOTHING]": {"type": object, "optional": True},
        "out_int_to_str": {"type": str, "optional": True},
        "out_float_to_str": {"type": str, "optional": True},
        "out_bool_to_str": {"type": str, "optional": True},
        "out_dict_to_str": {"type": str, "optional": True},
        "out_object_to_str": {"type": str, "optional": True},
    }

    def run(self):
        in_int = self.get_attribute_value("in_int")
        if in_int is not None:
            self.set_output("out_int_to_str", str(in_int))

        in_float = self.get_attribute_value("in_float")
        if in_float is not None:
            self.set_output("out_float_to_str", str(in_float))

        in_bool = self.get_attribute_value("in_bool")
        if in_bool is not None:
            self.set_output("out_bool_to_str", str(in_bool))

        in_dict = self.get_attribute_value("in_dict")
        if in_dict is not None:
            self.set_output("out_dict_to_str", str(in_dict))

        in_object = self.get_attribute_value("in_object")
        if in_object is not None:
            self.set_output("out_object_to_str", str(in_object))
