__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import datetime

from all_nodes.constants import InputsGUI
from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


DATE_FORMATS = sorted(
    [
        "%d/%m/%Y,  %H:%M:%S",  # European
        "%m/%d/%Y, %H:%M:%S",  # American
        "%Y.%m.%d_%H.%M.%S",  # Technical
    ]
)


class StrfDatetime(GeneralLogicNode):
    HELP = "Format a datetime object into a string"

    INPUTS_DICT = {
        "datetime_object": {"type": datetime.datetime},
        "datetime_formatting": {"type": str},
    }
    OUTPUTS_DICT = {"datetime_formatted": {"type": str}}

    def run(self):
        datetime_object = self.get_attribute_value("datetime_object")
        datetime_formatting = self.get_attribute_value("datetime_formatting")
        self.set_output(
            "datetime_formatted", datetime_object.strftime(datetime_formatting)
        )


class DatetimeFormatsSelect(GeneralLogicNode):
    NICE_NAME = "Datetime formats"

    INTERNALS_DICT = {
        "internal_datetime_format_str": {
            "type": str,
            "gui_type": InputsGUI.OPTION_INPUT,
            "options": DATE_FORMATS,
        },
    }

    OUTPUTS_DICT = {"out_datetime_format_str": {"type": str}}

    def run(self):
        self.set_output(
            "out_datetime_format_str",
            self.get_attribute_value("internal_datetime_format_str"),
        )


class DatetimeNow(GeneralLogicNode):
    NICE_NAME = "Datetime now"
    HELP = "Get a datetime object as of right now, as well as a formatted string"

    INTERNALS_DICT = {
        "internal_datetime_str": {
            "type": str,
            "gui_type": InputsGUI.OPTION_INPUT,
            "options": DATE_FORMATS,
        },
    }

    OUTPUTS_DICT = {
        "datetime_object": {"type": datetime.datetime},
        "out_datetime_str": {"type": str},
    }

    def run(self):
        datetime_object = datetime.datetime.now()
        datetime_formatting = self.get_attribute_value("internal_datetime_str")
        self.set_output(
            "out_datetime_str", datetime_object.strftime(datetime_formatting)
        )
        self.set_output("datetime_object", datetime_object)
