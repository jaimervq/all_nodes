# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import concurrent.futures
import os
import logging
import importlib
import inspect
import sys

import yaml

from PySide2 import QtCore
from PySide2 import QtGui

from all_nodes import constants


# -------------------------------- LOGGING -------------------------------- #
def get_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(constants.LOGGING_LEVEL)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(constants.LOGGING_LEVEL)
    console_handler.setLevel(constants.LOGGING_LEVEL)
    console_handler.setFormatter(constants.CONSOLE_LOG_FORMATTER)
    logger.addHandler(console_handler)
    return logger


LOGGER = get_logger(__name__)


def print_separator(message):
    print("\n", end="")
    print(message.upper())
    print("-" * len(message))


# -------------------------------- CONFIGS -------------------------------- #
def get_config(config_name):
    """
    Get a config from an existing yaml file.

    Args:
        config_name (str): name of config to read from configs folder

    Returns:
        dict: with read config

    """
    root = os.path.abspath(__file__)
    root_dir_path = os.path.dirname(root)
    config_file = os.path.join(root_dir_path, "config", config_name + ".yml")
    with open(config_file, "r") as stream:
        LOGGER.debug("Reading config '{}' from {}".format(config_name, config_file))
        return yaml.safe_load(stream)


# -------------------------------- NODE CLASSES -------------------------------- #
NODE_STYLES = get_config("node_lib_styles")

CLASSES_TO_SKIP = [
    "GeneralLogicNode",
    "Run",
    "SpecialInputNode",
    "GrabInputFromCtx",
    "SetOutputToCtx",
]


def register_node_lib(full_path, all_classes_dict):
    icons_path = os.path.join(os.path.dirname(full_path), "icons")
    node_lib_path = os.path.dirname(full_path)
    node_lib_name = os.path.basename(node_lib_path)
    module_filename = os.path.basename(full_path)
    module_name = os.path.splitext(module_filename)[0]

    # CLASSES SCANNING
    loaded_spec = importlib.util.spec_from_file_location(
        module_name,
        full_path,
    )
    loaded_module = importlib.util.module_from_spec(loaded_spec)
    loaded_spec.loader.exec_module(loaded_module)
    class_memebers = inspect.getmembers(loaded_module, inspect.isclass)
    if not class_memebers:
        return

    all_classes_dict[module_name] = dict()
    module_classes = list()
    class_counter = 0
    for name, cls in class_memebers:
        if name in CLASSES_TO_SKIP:
            continue
        setattr(cls, "FILEPATH", full_path)  # TODO not ideal?
        module_classes.append((name, cls))
        class_counter += 1

    all_classes_dict[module_name]["node_lib_path"] = node_lib_path
    all_classes_dict[module_name]["node_lib_name"] = node_lib_name
    all_classes_dict[module_name]["module_filename"] = module_filename
    all_classes_dict[module_name]["classes"] = module_classes

    all_classes_dict[module_name]["color"] = constants.DEFAULT_NODE_COLOR
    for style in NODE_STYLES:
        if style in module_name:
            all_classes_dict[module_name]["color"] = NODE_STYLES[style].get(
                "color", constants.DEFAULT_NODE_COLOR
            )
            all_classes_dict[module_name]["default_icon"] = NODE_STYLES[style].get(
                "default_icon"
            )
    LOGGER.debug(
        "Scanned {} for classes: found {}".format(
            os.path.basename(full_path), class_counter
        )
    )

    # ICONS - registering the icons so they can be found
    if not os.path.isdir(icons_path):
        LOGGER.warning(
            "No icons folder available for {}, icons for this module should be saved at: {}".format(
                module_filename, icons_path
            )
        )
    elif icons_path not in QtCore.QDir.searchPaths("icons"):
        QtCore.QDir.addSearchPath("icons", icons_path)
        LOGGER.debug("Registered path {} to 'icons'".format(icons_path))


def get_all_node_classes():
    libraries_path = os.getenv("ALL_NODES_LIB_PATH", "").split(";")
    if not os.getenv("ALL_NODES_LIB_PATH"):
        root = os.path.abspath(__file__)
        root_dir_path = os.path.dirname(root)
        default_lib_path = os.path.join(root_dir_path, "lib/base_node_lib")
        libraries_path = [default_lib_path]
        LOGGER.warning(
            "Env variable 'ALL_NODES_LIB_PATH' is not defined, "
            "will just scan for node libraries at default location: " + default_lib_path
        )

    all_py = list()
    for path in libraries_path:
        if not path:
            continue
        elif not os.path.isdir(path):
            LOGGER.warning("Folder {} does not exist".format(path))
        for (root, dirs, files) in os.walk(path, topdown=True):
            for file in files:
                p = os.path.join(root, file)
                if p.endswith(".py") and "__init__" not in p:
                    all_py.append(p)

    executor = concurrent.futures.ThreadPoolExecutor()
    all_classes_dict = dict()
    for full_path in all_py:
        executor.submit(register_node_lib, full_path, all_classes_dict)

    # TODO examine classes to make sure there are no repeated names?
    return all_classes_dict


# -------------------------------- SCENES -------------------------------- #
def get_all_scenes_recursive(libraries_path=None, scenes_dict=None):
    if libraries_path is None:
        libraries_path = []
        if not os.getenv("ALL_NODES_LIB_PATH"):
            root = os.path.abspath(__file__)
            root_dir_path = os.path.dirname(root)
            default_lib_path = os.path.join(root_dir_path, "lib/example_scene_lib")
            libraries_path.append(default_lib_path)
            LOGGER.warning(
                "Env variable 'ALL_NODES_LIB_PATH' is not defined, "
                "will just scan for node libraries at default location: "
                + default_lib_path
            )
        else:
            all_paths = os.getenv("ALL_NODES_LIB_PATH").split(";")
            for path in all_paths:
                if path:
                    for elem in os.listdir(path):
                        full_path = os.path.join(path, elem)
                        if os.path.isdir(full_path) and "scene_lib" in full_path:
                            libraries_path.append(full_path)

    if scenes_dict is None:
        scenes_dict = dict()

    for path in libraries_path:
        folder_name = os.path.basename(os.path.normpath(path))
        if not os.path.exists(path):
            LOGGER.error(
                "Path {} registered to ALL_NODES_LIB_PATH does not exist!".format(path)
            )
        if not os.listdir(path):
            continue
        scenes_dict[folder_name] = list()
        for elem in os.listdir(path):
            full_path = os.path.join(path, elem)
            scene_name = os.path.splitext(elem)[0]
            if os.path.isfile(full_path) and full_path.endswith(".yml"):
                scenes_dict[folder_name].append((scene_name, full_path))
            elif os.path.isdir(full_path):
                new_dict = dict()
                scenes_dict[folder_name].append(new_dict)
                get_all_scenes_recursive([full_path], new_dict)

    return scenes_dict


def get_scene_from_alias(scenes_dict, alias):
    """
    Given just an alias (or more specifically filename) find full path to the yml file.
    Scans recursively.

    Args:
        scenes_dict (dict): dict with all the scenes and their paths
        alias (str): alias/filename to search for

    Returns: str, full path to the yml scene found

    """
    scene_path = None

    for key in scenes_dict:
        list_value = scenes_dict[key]
        for elem in list_value:
            if isinstance(elem, dict):
                scene_path = get_scene_from_alias(elem, alias)
                if scene_path is not None:
                    return scene_path
            else:
                for elem in list_value:
                    if isinstance(elem, dict):
                        scene_path = get_scene_from_alias(elem, alias)
                        if scene_path is not None:
                            return scene_path
                    elif isinstance(elem, tuple):
                        scene_name, full_path = elem
                        if scene_name == alias:
                            scene_path = full_path

    return scene_path


# -------------------------------- UTILITY -------------------------------- #
def get_bright_color(color_name):
    base_color = QtGui.QColor(color_name)
    h, s, v = (
        base_color.hue(),
        base_color.saturation(),
        base_color.value(),
    )
    bright_color = QtGui.QColor.fromHsv(h, 255, 255)
    return bright_color.name()
