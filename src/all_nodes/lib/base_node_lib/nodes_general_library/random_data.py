__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils
import random


LOGGER = utils.get_logger(__name__)


class RandomRGBA(GeneralLogicNode):
    NICE_NAME = "Random RGBA"
    HELP = "Generate a random RGBA color"

    OUTPUTS_DICT = {"out_rgba": {"type": tuple}}

    def run(self):
        rgba = (random.random(), random.random(), random.random(), random.random())
        self.set_output("out_rgba", rgba)


class RandomInt(GeneralLogicNode):
    NICE_NAME = "Random Int"
    HELP = "Generate a random integer"

    INPUTS_DICT = {
        "min": {"type": int, "optional": True},
        "max": {"type": int, "optional": True},
    }

    OUTPUTS_DICT = {"out_int": {"type": int}}

    def run(self):
        min_val = self.get_attribute_value("min") or 0
        max_val = self.get_attribute_value("max") or 100
        random_int = random.randint(min_val, max_val)
        self.set_output("out_int", random_int)


class RandomFloat(GeneralLogicNode):
    NICE_NAME = "Random Float"
    HELP = "Generate a random float"

    INPUTS_DICT = {
        "min": {"type": float, "optional": True},
        "max": {"type": float, "optional": True},
    }

    OUTPUTS_DICT = {"out_float": {"type": float}}

    def run(self):
        min_val = self.get_attribute_value("min") or 0.0
        max_val = self.get_attribute_value("max") or 1.0
        random_float = random.uniform(min_val, max_val)
        self.set_output("out_float", random_float)


class RandomBool(GeneralLogicNode):
    NICE_NAME = "Random Bool"
    HELP = "Generate a random boolean value"

    OUTPUTS_DICT = {"out_bool": {"type": bool}}

    def run(self):
        random_bool = random.choice([True, False])
        self.set_output("out_bool", random_bool)
