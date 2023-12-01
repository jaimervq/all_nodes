__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes.logic.logic_node import Run
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class BasicIf(GeneralLogicNode):
    NICE_NAME = "Basic IF conditional"

    INPUTS_DICT = {
        "in_bool": {"type": bool},
    }

    OUTPUTS_DICT = {
        "path_1": {"type": Run, "optional": True},
        "path_2": {"type": Run, "optional": True},
    }

    def run(self):
        in_bool = self.get_attribute_value("in_bool")

        if in_bool:
            self.set_output("path_1", Run())
        else:
            self.set_output("path_2", Run())


class Basicbreaker(GeneralLogicNode):
    NICE_NAME = "Basic breaker"
    HELP = "If the input condition is met, break the whole execution after this node"

    INPUTS_DICT = {
        "in_bool": {"type": bool},
    }

    def run(self):
        in_bool = self.get_attribute_value("in_bool")

        if in_bool:
            self.error("BREAKING")
