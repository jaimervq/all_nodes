__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class MirrorFolders(GeneralLogicNode):
    NICE_NAME = "Mirror folders"

    INPUTS_DICT = {
        "src_folder": {"type": str},
        "dest_folder": {"type": str},
    }

    def run(self):
        import platform
        import subprocess

        src_folder = self.get_attribute_value("src_folder")
        dest_folder = self.get_attribute_value("dest_folder")

        if platform.system() == "Windows":
            s = subprocess.Popen(["robocopy", src_folder, dest_folder, "/E", "/MIR"])
            s.wait()
        else:
            self.fail("Not implemented!")


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
