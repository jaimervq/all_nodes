# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import SpecialInputNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class StrInput(SpecialInputNode):
    INPUT_TYPE = "str"

    NICE_NAME = "String input"
    HELP = ""

    OUTPUTS_DICT = {"out_str": {"type": str}}


class BoolInput(SpecialInputNode):
    INPUT_TYPE = "bool"

    NICE_NAME = "Boolean input"
    HELP = ""

    OUTPUTS_DICT = {"out_bool": {"type": bool}}


class DictInput(SpecialInputNode):
    INPUT_TYPE = "dict"

    NICE_NAME = "Dictionary input"
    HELP = ""

    OUTPUTS_DICT = {"out_dict": {"type": dict}}


class ListInput(SpecialInputNode):
    INPUT_TYPE = "list"

    NICE_NAME = "List input"
    HELP = ""

    OUTPUTS_DICT = {"out_list": {"type": list}}


class TupleInput(SpecialInputNode):
    INPUT_TYPE = "tuple"

    NICE_NAME = "Tuple input"
    HELP = ""

    OUTPUTS_DICT = {"out_tuple": {"type": tuple}}


class IntInput(SpecialInputNode):
    INPUT_TYPE = "int"

    NICE_NAME = "Integer input"
    HELP = ""

    OUTPUTS_DICT = {"out_int": {"type": int}}


class FloatInput(SpecialInputNode):
    INPUT_TYPE = "float"

    NICE_NAME = "Float input"
    HELP = ""

    OUTPUTS_DICT = {"out_float": {"type": float}, "out_int": {"type": int}}
