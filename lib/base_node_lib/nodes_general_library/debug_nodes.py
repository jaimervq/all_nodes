__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import time

from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class EmptyNode(GeneralLogicNode):
    NICE_NAME = "Empty node"
    HELP = "Does not do anything (just debugging purposes)"

    def run(self):
        LOGGER.info("All good! Nothing to be done :)")


class ErrorNode(GeneralLogicNode):
    def run(self):
        100 / 0


class FailNode(GeneralLogicNode):
    def run(self):
        self.fail("This node is supposed to fail")
        self.fail("Also, more than one fail message can be logged")


class FailAndErrorNode(GeneralLogicNode):
    def run(self):
        self.fail("This node has failed")
        [10][5]


class TimedNode(GeneralLogicNode):
    def run(self):
        time.sleep(1.5)


class PrintToConsole(GeneralLogicNode):
    NICE_NAME = "Print to console"
    HELP = "Print something to console"

    INPUTS_DICT = {
        "in_object_0": {"type": object, "optional": True},
        "in_object_1": {"type": object, "optional": True},
        "in_object_2": {"type": object, "optional": True},
        "in_object_3": {"type": object, "optional": True},
        "in_object_4": {"type": object, "optional": True},
    }

    def run(self):
        from colorama import Fore, Style

        for i in range(5):
            attr_name = "in_object_{}".format(i)
            val = self.get_attribute_value(attr_name)
            if val is not None:
                LOGGER.info(
                    f"{Fore.MAGENTA}[{self.node_name}] {attr_name}:{Fore.YELLOW}{val}{Style.RESET_ALL}"
                )
