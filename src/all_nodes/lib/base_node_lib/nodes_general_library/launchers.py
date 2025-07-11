# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.constants import InputsGUI, PreviewsGUI
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
        elif platform_name in ["darwin"]:
            subprocess.call(["open", file_path])
        else:
            self.fail("Not sure how to open a file in {}...".format(platform_name))
            return


class LaunchSubprocess(GeneralLogicNode):
    INPUTS_DICT = {
        "subprocess_command": {"type": str},
        "subprocess_args": {"type": list},
    }

    def run(self):
        import subprocess
        import platform

        subprocess_command = self.get_attribute_value("subprocess_command")
        subprocess_args = self.get_attribute_value("subprocess_args")
        if platform.system() == "Windows":
            s = subprocess.run(["cmd", "/c"] + [subprocess_command] + subprocess_args)
        else:
            s = subprocess.run([subprocess_command] + subprocess_args)

        if s.returncode != 0:
            self.fail("Subprocess failed with return code {}".format(s.returncode))


class LaunchSubprocessWithConsole(GeneralLogicNode):
    INPUTS_DICT = {
        "subprocess_command": {"type": str},
        "subprocess_args": {"type": list},
    }

    OUTPUTS_DICT = {
        "stdout": {"type": str},
        "stderr": {"type": str},
    }

    INTERNALS_DICT = {
        "internal_python_str": {
            "type": str,
            "gui_type": PreviewsGUI.CONSOLE_PREVIEW,
        },
    }

    def run(self):
        import html
        import subprocess
        import platform

        subprocess_command = self.get_attribute_value("subprocess_command")
        subprocess_args = self.get_attribute_value("subprocess_args")
        if platform.system() == "Windows":
            s = subprocess.run(
                ["cmd", "/c"] + [subprocess_command] + subprocess_args,
                capture_output=True,
                text=True,
            )
        else:
            s = subprocess.run(
                [subprocess_command] + subprocess_args, capture_output=True, text=True
            )

        self.set_output("stdout", s.stdout.strip())
        self.set_output("stderr", s.stderr.strip())

        self.set_attribute_value(
            "internal_python_str",
            '<span style="font-family: Consolas; color: lime; white-space: pre-wrap;">---- STDOUT ----\n'
            + html.escape(s.stdout.strip())
            + '\n\n<span style="font-family: Consolas; color: red; white-space: pre-wrap;">---- STDERR ----\n'
            + html.escape(s.stderr.strip()),
        )
        if s.returncode != 0:
            self.fail("Subprocess failed with return code {}".format(s.returncode))


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
