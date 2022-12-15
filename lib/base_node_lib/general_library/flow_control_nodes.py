__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes import constants
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

        if in_bool == True:
            self.set_output("path_1", Run())
        else:
            self.set_output("path_2", Run())


class BasicFor(GeneralLogicNode):

    NICE_NAME = "Basic FOR loop"
    HELP = (
        "Iterates through the provided list, returning one element at a "
        "time as output and executing connected nodes"
    )

    INPUTS_DICT = {
        "in_list": {"type": list},
    }

    OUTPUTS_DICT = {
        "element": {"type": object},
        "iterations": {"type": int},
    }

    def _run(self, execute_connected=True):
        in_list = self.get_attribute_value("in_list")

        iterations = 0
        for element in in_list:

            for node in self.out_connected_nodes():
                if node.success in [constants.FAILED, constants.ERROR]:
                    self.fail(
                        "Something is wrong in connected node {}, cannot keep iterating".format(
                            node.full_name
                        )
                    )
                    return

            iterations += 1
            self.set_output("element", element)
            self.set_output("iterations", iterations)
            LOGGER.info(
                "Iteration of FOR node {}: Element {}, Iteration {}".format(
                    self.full_name, element, iterations
                )
            )
            super()._run(execute_connected=execute_connected)

    def run(self):
        pass
