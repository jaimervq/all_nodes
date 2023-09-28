# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class JsonToDict(GeneralLogicNode):
    NICE_NAME = "Json to dict"
    HELP = "Load a JSON file"

    INPUTS_DICT = {
        "in_json_filepath": {"type": str},
    }

    OUTPUTS_DICT = {"out_dict": {"type": dict}}

    def run(self):
        import os
        import json

        in_json_filepath = self.get_attribute_value("in_json_filepath")

        if not os.path.isfile(in_json_filepath):
            self.fail(
                "Json file {} does not exist! Cannot read it".format(in_json_filepath)
            )
            return

        with open(in_json_filepath, "r") as json_file:
            data = json.load(json_file)
            self.set_output("out_dict", data)


class TxtToList(GeneralLogicNode):
    INPUTS_DICT = {
        "in_txt": {"type": str},
    }
    OUTPUTS_DICT = {"out_list": {"type": list}}

    def run(self):
        in_txt = self.get_attribute_value("in_txt")
        with open(in_txt, "r") as file:
            self.set_output("out_list", file.readlines())


class YamlToDict(GeneralLogicNode):
    INPUTS_DICT = {
        "yaml_filepath": {"type": str},
    }

    OUTPUTS_DICT = {"out_dict": {"type": dict}}

    def run(self):
        import os
        import yaml

        yaml_filepath = self.get_attribute_value("yaml_filepath")

        if not os.path.isfile(yaml_filepath):
            self.fail(
                "Yaml file {} does not exist! Cannot read it".format(yaml_filepath)
            )
            return

        with open(yaml_filepath, "r") as y:
            self.set_output("out_dict", yaml.safe_load(y))
