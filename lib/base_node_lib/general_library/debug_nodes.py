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
        i = 100 / 0


class FailNode(GeneralLogicNode):
    def run(self):
        self.fail("This node is supposed to fail")
        self.fail("Also, more than one fail message can be logged")


class FailAndErrorNode(GeneralLogicNode):
    def run(self):
        self.fail("This node has failed")
        a = [10][5]


class TimedNode(GeneralLogicNode):
    def run(self):
        time.sleep(1.5)
