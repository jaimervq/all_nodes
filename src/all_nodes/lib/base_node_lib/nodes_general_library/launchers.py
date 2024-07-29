# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.constants import InputsGUI
from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


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


class RunPython(GeneralLogicNode):
    INTERNALS_DICT = {
        "internal_python_str": {
            "type": str,
            "gui_type": InputsGUI.MULTILINE_STR_INPUT,
        },
    }

    def run(self):
        python_str = self.get_attribute_value("internal_python_str")
        exec(python_str)
