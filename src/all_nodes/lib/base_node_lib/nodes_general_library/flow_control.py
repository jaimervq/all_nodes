__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes import constants
from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes.logic.logic_node import Run, RunLoop
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


class ForEachBegin(GeneralLogicNode):
    NICE_NAME = "For each begin"

    INPUTS_DICT = {
        "iterable": {"type": list},
    }

    OUTPUTS_DICT = {
        "element": {"type": object},
        "foreach_end": {"type": RunLoop},
    }

    def _run(self, execute_connected=True):
        if not self.active:
            self.fail("Cannot start loop from an inactive loop node!")
            self.signaler.finished.emit()
            return

        from colorama import Fore, Style

        LOGGER.info(f"{Fore.CYAN}[{self.node_name}] Loop begins!{Style.RESET_ALL}")
        self.execution_counter += 1

        iterable = self.get_attribute_value("iterable")
        num_iterations = len(iterable)

        self.success = constants.IN_LOOP

        for i in range(num_iterations):
            LOGGER.info(f"{Fore.CYAN}{self.node_name}, iteration {i}{Style.RESET_ALL}")

            if execute_connected:
                for node in self.out_connected_nodes():
                    node.recursive_clear_connected_input_attrs()
                    node.recursive_set_in_loop()

            element = iterable[i]
            self.set_attribute_value("element", element)
            self.set_output(constants.COMPLETED, Run())

            self.propagate_results()
            if execute_connected:
                for node in self.out_connected_nodes():
                    if node.success in [constants.NOT_RUN, constants.IN_LOOP]:
                        LOGGER.info(
                            "[LOOP] From {}, launching execution of {}".format(
                                self.full_name, node.full_name
                            )
                        )
                        node._run()

        # Launch execution of ForEachEnd
        self.success = constants.SUCCESSFUL
        self.set_output("foreach_end", RunLoop())
        self.propagate_results()
        if execute_connected:
            for node in self.out_connected_nodes():
                if node.success == constants.IN_LOOP:
                    LOGGER.info(
                        "[LOOP END] From {}, launching execution of {}".format(
                            self.full_name, node.full_name
                        )
                    )
                    node._run()

        self.signaler.finished.emit()


class ForEachEnd(GeneralLogicNode):
    NICE_NAME = "For each end"

    INPUTS_DICT = {
        "foreach_end": {"type": RunLoop},
    }

    def run(self):
        from colorama import Fore, Style

        LOGGER.info(f"{Fore.CYAN}[{self.node_name}] Loop ended!{Style.RESET_ALL}")
