# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class RegexMatch(GeneralLogicNode):
    INPUTS_DICT = {
        "in_str": {"type": str},
        "pattern": {"type": str},
    }

    OUTPUTS_DICT = {"match": {"type": bool}}

    def run(self):
        import re

        in_str = self.get_attribute_value("in_str")
        pattern = self.get_attribute_value("pattern")

        match = re.match(pattern, in_str)
        self.set_output("match", match is not None)
