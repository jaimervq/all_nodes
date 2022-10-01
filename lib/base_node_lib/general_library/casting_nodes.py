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


from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class ListToStr(GeneralLogicNode):

    INPUTS_DICT = {
        "in_list": {"type": list},
        "join_character": {"type": str, "optional": True},
    }

    OUTPUTS_DICT = {"out_str": {"type": str}}

    def run(self):
        in_list = [str(elem) for elem in self.get_attribute_value("in_list")]
        join_character = self.get_attribute_value("join_character") or " "
        self.set_output("out_str", join_character.join(in_list))


class IntToStr(GeneralLogicNode):

    INPUTS_DICT = {
        "in_int": {"type": int},
    }

    OUTPUTS_DICT = {"out_str": {"type": str}}

    def run(self):
        in_int = self.get_attribute_value("in_int")
        self.set_output("out_str", str(in_int))


class ConcatStr(GeneralLogicNode):

    INPUTS_DICT = {
        "in_str_0": {"type": str},
        "in_str_1": {"type": str},
        "in_str_2": {"type": str, "optional": True},
        "in_str_3": {"type": str, "optional": True},
        "in_str_4": {"type": str, "optional": True},
    }

    OUTPUTS_DICT = {"out_str": {"type": str}}

    def run(self):
        out_str = ""
        for i in range(5):
            attr_name = "in_str_{}".format(i)
            val = self.get_attribute_value(attr_name)
            if val is not None:
                out_str += val
        self.set_output("out_str", out_str)
