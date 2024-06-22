# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import argparse
import os
import sys

from PySide2.QtWidgets import QApplication

from all_nodes.analytics import analytics
from all_nodes.graphic.widgets.main_window import AllNodesWindow
from all_nodes.logic.class_registry import CLASS_REGISTRY as CR
from all_nodes.logic.logic_scene import LogicScene
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


# LAUNCH MODES ---------------------------------------------------
def launch_gui():
    """
    Just launch the tool, with GUI to create/edit scenes.
    """
    # Start classes scannig first thing
    CR.scan_for_classes_GUI()

    # App
    app = QApplication(sys.argv)

    # Launch
    AllNodesWindow()
    app.exec_()


def launch_batch(scene_file: str, set_parameters: list):
    """
    Run a scene in batch mode, no GUI.

    Args:
        scene_file (str): Filepath or alias of the scene to run
        scene_file (list): List eith parameters and values to be set
    """
    # Start classes scannig first thing
    CR.scan_for_classes()

    # Scene
    scene = LogicScene()
    scene.load_from_file(scene_file)
    if set_parameters:
        for i in range(0, len(set_parameters) - 1, 2):
            node_name = set_parameters[i].rsplit(".", 1)[0]
            attr_name = set_parameters[i].rsplit(".", 1)[1]
            attr_str_value = set_parameters[i + 1]

            node = scene.to_node(node_name)
            if node:
                node.set_attribute_from_str(attr_name, attr_str_value)

    # Run!
    scene.run_all_nodes(spawn_thread=False)


# MAIN ---------------------------------------------------
def main():
    # Startup logging
    LOGGER.info("STARTED all_nodes")

    # Arguments ----------------------
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f", "--scene_file", type=str, help="file .yml to run in non-GUI mode"
    )
    parser.add_argument(
        "-s",
        "--set_parameters",
        help="Arguments to set in batch execution of scene",
        type=str,
        nargs="+",
    )
    parser.add_argument(
        "-a",
        "--analytics",
        help="Perform analytics and generate graphs",
        action="store_true",
    )
    args = parser.parse_args()

    if not os.getenv("IN_DEV"):
        LOGGER.info("For launching in DEBUG mode, set env variable 'IN_DEV'")

    # Analytics ----------------------
    if args.analytics:
        analytics.process_analytics()
        sys.exit(0)

    # GUI mode ----------------------
    if not args.scene_file:
        launch_gui()

    # Non-GUI batch mode ----------------------
    else:
        launch_batch(args.scene_file, args.set_parameters)


if __name__ == "__main__":
    main()
