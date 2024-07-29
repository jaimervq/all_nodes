# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class DictToJson(GeneralLogicNode):
    NICE_NAME = "Dict to json"
    HELP = "Write dict to JSON file"

    INPUTS_DICT = {
        "in_dict": {"type": dict},
        "json_filepath_to_write": {"type": str},
    }

    def run(self):
        import json

        in_dict = self.get_attribute_value("in_dict")
        json_filepath_to_write = self.get_attribute_value("json_filepath_to_write")

        with open(json_filepath_to_write, "w") as f:
            json.dump(in_dict, f, indent=4)


class DictToYaml(GeneralLogicNode):
    NICE_NAME = "Dict to yaml"
    HELP = "Write dict to YAML file"

    INPUTS_DICT = {
        "in_dict": {"type": dict},
        "yaml_filepath_to_write": {"type": str},
    }

    def run(self):
        import yaml

        in_dict = self.get_attribute_value("in_dict")
        path = self.get_attribute_value("yaml_filepath_to_write")
        with open(path, "w") as file:
            yaml.dump(in_dict, file, indent=4)


class ListToTxt(GeneralLogicNode):
    INPUTS_DICT = {
        "in_list": {"type": list},
        "txt_filepath_to_write": {"type": str},
    }

    def run(self):
        in_list = self.get_attribute_value("in_list")
        path = self.get_attribute_value("txt_filepath_to_write")
        with open(path, "w") as file:
            for elem in in_list:
                file.write(str(elem) + "\n")


class TableToCsv(GeneralLogicNode):
    INPUTS_DICT = {
        "in_table": {"type": list},
        "csv_filepath_to_write": {"type": str},
    }

    def run(self):
        import csv

        in_table = self.get_attribute_value("in_table")
        csv_filepath_to_write = self.get_attribute_value("csv_filepath_to_write")
        with open(csv_filepath_to_write, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(in_table)


class CreateTempFile(GeneralLogicNode):
    NICE_NAME = "Create temp file"

    INPUTS_DICT = {"suffix": {"type": str, "optional": True}}
    OUTPUTS_DICT = {"tempfile_path": {"type": str}}

    def run(self):
        import tempfile

        out_tempfile = ""

        suffix = self.get_attribute_value("suffix")
        if suffix:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_file.close()
            out_tempfile = temp_file.name
        else:
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.close()
            out_tempfile = temp_file.name

        self.set_output("tempfile_path", out_tempfile)
        LOGGER.debug("Created tempfile: {}".format(out_tempfile))
