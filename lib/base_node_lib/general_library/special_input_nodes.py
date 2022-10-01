# -*- coding: UTF-8 -*-
"""
Author: Jaime Rivera
Date: November 2022
Copyright: MIT License

           Copyright (c) 2022 Jaime Rivera

           Permission is hereby granted, free of charge, to any person obtaining a copy
           of this software and associated documentation files (the "Software"), to deal
           in the Software without restriction, including without limitation the rights
           to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
           copies of the Software, and to permit persons to whom the Software is
           furnished to do so, subject to the following conditions:

           The above copyright notice and this permission notice shall be included in all
           copies or substantial portions of the Software.

           THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
           IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
           FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
           AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
           LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
           OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
           SOFTWARE.

Brief:
"""

__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import SpecialInputNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class StrInput(SpecialInputNode):
    INPUT_TYPE = str

    NICE_NAME = "String input"
    HELP = ""

    OUTPUTS_DICT = {"out_str": {"type": str}}


class BoolInput(SpecialInputNode):
    INPUT_TYPE = bool

    NICE_NAME = "Boolean input"
    HELP = ""

    OUTPUTS_DICT = {"out_bool": {"type": bool}}


class DictInput(SpecialInputNode):
    INPUT_TYPE = dict

    NICE_NAME = "Dictionary input"
    HELP = ""

    OUTPUTS_DICT = {"out_dict": {"type": dict}}


class ListInput(SpecialInputNode):
    INPUT_TYPE = list

    NICE_NAME = "List input"
    HELP = ""

    OUTPUTS_DICT = {"out_list": {"type": list}}


class IntInput(SpecialInputNode):
    INPUT_TYPE = int

    NICE_NAME = "Integer input"
    HELP = ""

    OUTPUTS_DICT = {"out_int": {"type": int}}


class FloatInput(SpecialInputNode):
    INPUT_TYPE = float

    NICE_NAME = "Float input"
    HELP = ""

    OUTPUTS_DICT = {"out_float": {"type": float}, "out_int": {"type": int}}
