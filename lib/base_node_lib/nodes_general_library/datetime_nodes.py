__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import datetime

from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes.logic.logic_node import OptionInput
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class DatetimeNow(GeneralLogicNode):
    NICE_NAME = "Datetime now"
    HELP = "Get a datetime object as of right now"

    OUTPUTS_DICT = {"datetime_object": {"type": datetime.datetime}}

    def run(self):
        self.set_output("datetime_object", datetime.datetime.now())


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


class DatetimeFormatsSelect(OptionInput):
    INPUT_OPTIONS = [
        "%d/%m/%Y,  %H:%M:%S",  # European
        "%m/%d/%Y, %H:%M:%S",  # American
    ]
    NICE_NAME = "Datetime formats"
