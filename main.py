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


import argparse
import os
import sys

from PySide2.QtWidgets import QApplication

from all_nodes.graphic.widgets.main_window import AllNodesWindow
from all_nodes.logic.logic_scene import LogicScene
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


# LAUNCH MODES ---------------------------------------------------
def launch_gui():
    """
    Just launch the tool, with GUI to create/edit scenes.
    """
    app = QApplication(sys.argv)
    AllNodesWindow()
    app.exec_()


def launch_batch(scene_file: str):
    """
    Run a scene in batch mode, no GUI.

    Args:
        scene_file (str): Filepath or alias of the scene to run
    """
    scene = LogicScene()
    scene.load_from_file(scene_file)
    scene.run_all_nodes()


# MAIN ---------------------------------------------------
def main():
    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f", "--scene_file", type=str, help="file .yml to run in non-GUI mode"
    )
    args = parser.parse_args()

    if not os.getenv("IN_DEV"):
        LOGGER.info("For launching in DEBUG mode, set env variable 'IN_DEV'")

    # GUI mode
    if not args.scene_file:
        launch_gui()

    # Non-GUI batch mode
    else:
        launch_batch(args.scene_file)


if __name__ == "__main__":
    main()
