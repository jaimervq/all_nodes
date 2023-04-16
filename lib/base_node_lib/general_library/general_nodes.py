# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class GetDictKey(GeneralLogicNode):

    NICE_NAME = "Get dict key"
    HELP = "Get given key from a dictionary"

    INPUTS_DICT = {
        "in_dict": {"type": dict},
        "key": {"type": str},
    }

    OUTPUTS_DICT = {"out": {"type": object}}

    def run(self):
        in_dict = self.get_attribute_value("in_dict")
        key = self.get_attribute_value("key")
        if key not in in_dict:
            self.fail("Key '{}' not present in input dict {}".format(key, in_dict))
            return
        self.set_output("out", in_dict[key])


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


class SetDictKey(GeneralLogicNode):

    NICE_NAME = "Set dict key"
    HELP = "Set a key in a dictionary"

    INPUTS_DICT = {
        "in_dict": {"type": dict},
        "key": {"type": str},
        "new_value": {"type": object},
    }

    OUTPUTS_DICT = {"out_dict": {"type": dict}}

    def run(self):
        in_dict = self.get_attribute_value("in_dict")
        key = self.get_attribute_value("key")
        new_value = self.get_attribute_value("new_value")

        in_dict[key] = new_value
        self.set_output("out_dict", in_dict)


class GetFolderFromFilepath(GeneralLogicNode):

    INPUTS_DICT = {
        "filepath": {"type": str},
    }

    OUTPUTS_DICT = {"folder_path": {"type": str}}

    def run(self):
        import os

        filepath = self.get_attribute_value("filepath")
        if not filepath:
            self.fail("No filepath provided!")
            return

        self.set_output("folder_path", os.path.dirname(filepath))


class PathJoin(GeneralLogicNode):

    INPUTS_DICT = {
        "token_0": {"type": str},
        "token_1": {"type": str},
    }

    OUTPUTS_DICT = {"joined_path": {"type": str}}

    def run(self):
        import os

        token_0 = self.get_attribute_value("token_0")
        token_1 = self.get_attribute_value("token_1")
        self.set_output("joined_path", os.path.join(token_0, token_1))


class CopyFile(GeneralLogicNode):

    INPUTS_DICT = {
        "source_file": {"type": str},
        "destination_file": {"type": str},
        "make_dirs": {"type": bool, "optional": True},
    }

    def run(self):
        import os
        import shutil

        source_file = self.get_attribute_value("source_file")
        destination_file = self.get_attribute_value("destination_file")
        make_dirs = self.get_attribute_value("make_dirs")
        if make_dirs:
            os.makedirs(os.path.dirname(destination_file), exist_ok=True)
        shutil.copy(source_file, destination_file)


class CopyFoldersRecursive(GeneralLogicNode):

    NICE_NAME = "Copy folders recursive"

    INPUTS_DICT = {
        "source_folder_path": {"type": str},
        "destination_folder_path": {"type": str},
    }


class PrintToConsole(GeneralLogicNode):

    NICE_NAME = "Print to console"
    HELP = "Print something to console"

    INPUTS_DICT = {
        "in_object_0": {"type": object, "optional": True},
        "in_object_1": {"type": object, "optional": True},
        "in_object_2": {"type": object, "optional": True},
        "in_object_3": {"type": object, "optional": True},
        "in_object_4": {"type": object, "optional": True},
    }

    def run(self):
        for i in range(5):
            attr_name = "in_object_{}".format(i)
            val = self.get_attribute_value(attr_name)
            if val is not None:
                LOGGER.info("[{}] {}:{}".format(self.node_name, attr_name, val))


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


class TxtToList(GeneralLogicNode):

    INPUTS_DICT = {
        "in_txt": {"type": str},
    }
    OUTPUTS_DICT = {"out_list": {"type": list}}

    def run(self):
        in_txt = self.get_attribute_value("in_txt")
        with open(in_txt, "r") as file:
            self.set_output("out_list", file.readlines())


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


class StartFile(GeneralLogicNode):

    INPUTS_DICT = {
        "file_path": {"type": str},
    }

    def run(self):
        import os

        file_path = self.get_attribute_value("file_path")
        if not os.path.exists(file_path):
            self.fail("File {} does not exist!".format(file_path))
            return

        os.startfile(file_path)


class LaunchSubprocess(GeneralLogicNode):

    INPUTS_DICT = {
        "subprocess_str": {"type": str},
    }

    def run(self):
        import subprocess

        subprocess_str = self.get_attribute_value("subprocess_str")
        subprocess.run(subprocess_str, shell=True)


class GetEntireEnviron(GeneralLogicNode):

    NICE_NAME = "Get entire environment"

    OUTPUTS_DICT = {"environ_dict": {"type": dict}}

    def run(self):
        import os

        self.set_output("environ_dict", dict(os.environ))


class GetEnvVariable(GeneralLogicNode):

    NICE_NAME = "Get env variable"
    HELP = (
        "Get the value of an environment variable, with possibility of a fallback"
        "value if the variable is not defined"
    )

    INPUTS_DICT = {
        "env_variable_name": {"type": str},
        "fallback_value": {"type": str, "optional": True},
    }

    OUTPUTS_DICT = {"env_variable_value": {"type": str}}

    def run(self):
        import os

        env_variable_name = self.get_attribute_value("env_variable_name")
        fallback_value = self.get_attribute_value("fallback_value")
        env_var_value = os.getenv(env_variable_name)
        if env_var_value is None:
            if fallback_value:
                env_var_value = fallback_value
            else:
                self.fail(
                    "No environment variable '{}' found".format(env_variable_name)
                )
                return

        self.set_output("env_variable_value", env_var_value)


class SetEnvVariable(GeneralLogicNode):

    INPUTS_DICT = {
        "env_variable_name": {"type": str},
        "new_value": {"type": str},
    }

    def run(self):
        import os

        env_variable_name = self.get_attribute_value("env_variable_name")
        new_value = self.get_attribute_value("new_value")

        os.environ[env_variable_name] = new_value
