__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.constants import PreviewsGUI
from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class StringPreview(GeneralLogicNode):
    INPUTS_DICT = {
        "in_str": {"type": str},
    }

    INTERNALS_DICT = {
        "internal_str": {"type": str, "gui_type": PreviewsGUI.STR_PREVIEW},
    }

    def run(self):
        self.set_attribute_value("internal_str", self.get_attribute_value("in_str"))


class MultilineStringPreview(GeneralLogicNode):
    INPUTS_DICT = {
        "in_str": {"type": str},
    }

    INTERNALS_DICT = {
        "internal_multiline_str": {
            "type": str,
            "gui_type": PreviewsGUI.MULTILINE_STR_PREVIEW,
        },
    }

    def run(self):
        self.set_attribute_value(
            "internal_multiline_str", self.get_attribute_value("in_str")
        )


class DictPreview(GeneralLogicNode):
    INPUTS_DICT = {
        "in_dict": {"type": dict},
    }

    INTERNALS_DICT = {
        "internal_multiline_dict": {
            "type": dict,
            "gui_type": PreviewsGUI.DICT_PREVIEW,
        },
    }

    def run(self):
        self.set_attribute_value(
            "internal_multiline_dict", self.get_attribute_value("in_dict")
        )
