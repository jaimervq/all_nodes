__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class BooleanOr(GeneralLogicNode):
    NICE_NAME = "Or"
    HELP = "Return True if at least one input is True"

    INPUTS_DICT = {
        "in_0": {"type": bool},
        "in_1": {"type": bool},
    }

    OUTPUTS_DICT = {"out": {"type": bool}}

    def run(self):
        in_0 = self.get_attribute_value("in_0")
        in_1 = self.get_attribute_value("in_1")
        self.set_output("out", in_0 or in_1)


class BooleanAnd(GeneralLogicNode):
    NICE_NAME = "And"
    HELP = "Return True if all inputs are True"

    INPUTS_DICT = {
        "in_0": {"type": bool},
        "in_1": {"type": bool},
    }

    OUTPUTS_DICT = {"out": {"type": bool}}

    def run(self):
        in_0 = self.get_attribute_value("in_0")
        in_1 = self.get_attribute_value("in_1")
        self.set_output("out", in_0 and in_1)


class BooleanXor(GeneralLogicNode):
    NICE_NAME = "Xor"
    HELP = "Return True if only one input is True"

    INPUTS_DICT = {
        "in_0": {"type": bool},
        "in_1": {"type": bool},
    }

    OUTPUTS_DICT = {"out": {"type": bool}}

    def run(self):
        in_0 = self.get_attribute_value("in_0")
        in_1 = self.get_attribute_value("in_1")
        self.set_output("out", in_0 != in_1)


class BooleanNot(GeneralLogicNode):
    NICE_NAME = "Not"
    HELP = "Return the opposite of the input"

    INPUTS_DICT = {
        "in_0": {"type": bool},
    }

    OUTPUTS_DICT = {"out": {"type": bool}}

    def run(self):
        in_0 = self.get_attribute_value("in_0")
        self.set_output("out", not in_0)


class BooleanNand(GeneralLogicNode):
    NICE_NAME = "Nand"
    HELP = "Return True if not all inputs are True"

    INPUTS_DICT = {
        "in_0": {"type": bool},
        "in_1": {"type": bool},
    }

    OUTPUTS_DICT = {"out": {"type": bool}}

    def run(self):
        in_0 = self.get_attribute_value("in_0")
        in_1 = self.get_attribute_value("in_1")
        self.set_output("out", not (in_0 and in_1))


class BooleanNXor(GeneralLogicNode):
    NICE_NAME = "NXor"
    HELP = "Return True if both inputs are the same"

    INPUTS_DICT = {
        "in_0": {"type": bool},
        "in_1": {"type": bool},
    }

    OUTPUTS_DICT = {"out": {"type": bool}}

    def run(self):
        in_0 = self.get_attribute_value("in_0")
        in_1 = self.get_attribute_value("in_1")
        self.set_output("out", in_0 == in_1)
