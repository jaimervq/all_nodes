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


class StartFile(GeneralLogicNode):
    INPUTS_DICT = {
        "file_path": {"type": str},
    }

    def run(self):
        import os
        import platform
        import subprocess

        file_path = self.get_attribute_value("file_path")
        if not os.path.exists(file_path):
            self.fail("File {} does not exist!".format(file_path))
            return

        platform_name = platform.system().lower()
        if "windows" in platform_name:
            os.startfile(file_path)
        elif platform_name in ["linux", "ubuntu"]:
            subprocess.call(["xdg-open", file_path])
        elif platform_name in ["dawrin"]:
            subprocess.call(["open", file_path])
        else:
            self.fail("Not sure how to open a file in {}...".format(platform_name))
            return


class LaunchSubprocess(GeneralLogicNode):
    INPUTS_DICT = {
        "subprocess_str": {"type": str},
    }

    def run(self):
        import subprocess

        subprocess_str = self.get_attribute_value("subprocess_str")
        subprocess.run(subprocess_str, shell=True)
