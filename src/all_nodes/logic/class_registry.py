# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import concurrent.futures
import importlib
import inspect
import os
from pathlib import Path
import time

from PySide2 import QtCore
import yaml

from all_nodes import constants
from all_nodes import utils
from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes.graphic.widgets.global_signaler import GlobalSignaler


GS = GlobalSignaler()

LOGGER = utils.get_logger(__name__)


# -------------------------------- NODE CLASSES -------------------------------- #
CLASSES_TO_SKIP = [
    "InputsGUI",
    "PreviewsGUI",
    "GeneralLogicNode",
    "Run",
    "RunLoop",
    "GrabInputFromCtx",
    "SetOutputToCtx",
]  # Classes to skip when gathering all usable clases, populating widgets...


def register_node_lib(lib_path):
    classes_dict = dict()

    all_py = []
    for root, _, files in os.walk(lib_path, topdown=True):
        for file in files:
            p = os.path.join(root, file)
            if p.endswith(".py") and "__init__" not in p:
                all_py.append(p)

    for py_path in all_py:
        node_library_path = os.path.dirname(py_path)
        node_library_name = os.path.basename(node_library_path)
        module_filename = os.path.basename(py_path)
        module_name = os.path.splitext(module_filename)[0]
        icons_path = os.path.join(node_library_path, "icons")
        styles_path = os.path.join(node_library_path, "styles.yml")

        if classes_dict.get(node_library_name) is None:
            classes_dict[node_library_name] = dict()

        # ICONS - registering the icons so they can be found
        if not os.path.isdir(icons_path):
            LOGGER.warning(
                f"No icons folder available for {node_library_name}, icons for this library should be saved at: {icons_path}"
            )
        if os.path.isdir(icons_path) and icons_path not in QtCore.QDir.searchPaths(
            "icons"
        ):
            QtCore.QDir.addSearchPath("icons", icons_path)
            LOGGER.debug("Registered path {} to 'icons'".format(icons_path))

        # STYLES
        node_styles = dict()
        if not os.path.isfile(styles_path):
            LOGGER.warning(
                f"No styles file available for {node_library_name}, styles for this library should be saved at: {styles_path}"
            )
        else:
            with open(styles_path, "r") as stream:
                node_styles = yaml.safe_load(stream)

        # CLASSES SCANNING
        loaded_spec = importlib.util.spec_from_file_location(
            module_name,
            py_path,
        )
        loaded_module = importlib.util.module_from_spec(loaded_spec)
        loaded_spec.loader.exec_module(loaded_module)
        class_members = inspect.getmembers(loaded_module, inspect.isclass)
        if not class_members:
            return

        classes_dict[node_library_name][module_name] = dict()
        module_classes = list()
        class_counter = 0
        for name, cls_object in class_members:
            if (
                not issubclass(cls_object, GeneralLogicNode)
                or cls_object == GeneralLogicNode
            ):
                continue

            # Icon for this class  # TODO Refactor this out
            default_icon = node_styles.get(module_name, dict()).get("default_icon")
            icon_path = "icons:nodes.svg"
            if (
                hasattr(cls_object, "IS_CONTEXT") and cls_object.IS_CONTEXT
            ):  # TODO inheritance not working here?
                icon_path = "icons:cubes.svg"
            if QtCore.QFile.exists(f"icons:{name}.png"):
                icon_path = f"icons:{name}.png"
            elif QtCore.QFile.exists(f"icons:{name}.svg"):
                icon_path = f"icons:{name}.svg"
            elif default_icon:
                if QtCore.QFile.exists("icons:" + default_icon + ".png"):
                    icon_path = f"icons:{default_icon}.png"
                elif QtCore.QFile.exists("icons:" + default_icon + ".svg"):
                    icon_path = f"icons:{default_icon}.svg"
            setattr(cls_object, "ICON_PATH", icon_path)

            # Class name and object
            setattr(cls_object, "FILEPATH", py_path)  # TODO not ideal?
            module_classes.append((name, cls_object))
            class_counter += 1

        classes_dict[node_library_name][module_name]["node_lib_path"] = (
            node_library_path
        )
        classes_dict[node_library_name][module_name]["node_lib_name"] = (
            node_library_name
        )
        classes_dict[node_library_name][module_name]["module_filename"] = (
            module_filename
        )
        classes_dict[node_library_name][module_name]["module_full_path"] = py_path
        classes_dict[node_library_name][module_name]["classes"] = module_classes

        classes_dict[node_library_name][module_name]["color"] = (
            constants.DEFAULT_NODE_COLOR
        )
        for module_style in node_styles:
            if module_style in module_name:
                classes_dict[node_library_name][module_name]["color"] = node_styles[
                    module_style
                ].get("color", constants.DEFAULT_NODE_COLOR)
        LOGGER.debug(
            "Scanned {} for classes: found {}".format(
                os.path.basename(py_path), class_counter
            )
        )

    return classes_dict


def get_all_node_libs():
    # TODO clarify this naming better (maybe project->lib->module?)
    # Paths to be examined
    libraries_path = [
        lib_path
        for lib_path in os.getenv("ALL_NODES_LIB_PATH", "").split(os.pathsep)
        if lib_path
    ]
    if not os.getenv("ALL_NODES_LIB_PATH"):
        root = os.path.abspath(__file__)
        root_dir_path = os.path.dirname(os.path.dirname(root))
        default_lib_path = os.path.join(root_dir_path, "lib", "base_node_lib")
        libraries_path = [default_lib_path]
        LOGGER.warning(
            "Env variable 'ALL_NODES_LIB_PATH' is not defined, "
            "will just scan for node libraries at default location: " + default_lib_path
        )

    return libraries_path


# -------------------------------- SCENES -------------------------------- #
def get_all_scenes_recursive(libraries_path=None, scenes_dict=None):
    if libraries_path is None:
        libraries_path = []
        if not os.getenv("ALL_NODES_LIB_PATH"):
            root = os.path.abspath(__file__)
            root_dir_path = os.path.dirname(os.path.dirname(root))
            default_lib_path = os.path.join(
                root_dir_path, "lib", "basic_examples_scene_lib"
            )
            libraries_path.append(default_lib_path)
            LOGGER.warning(
                "Env variable 'ALL_NODES_LIB_PATH' is not defined, "
                "will just scan for scene libraries at default location: "
                + default_lib_path
            )
        else:
            all_paths = os.getenv("ALL_NODES_LIB_PATH").split(os.pathsep)
            for path in all_paths:
                path = path.strip()
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
    return scene_path


# -------------------------------- Class Registry -------------------------------- #
class ClassRegistry:
    # Instance
    _instance = None

    # Attributes
    _all_classes = None
    _all_scenes = None

    _all_classes_simplified = None

    # Workers
    _lib_workers = []
    _time_start = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClassRegistry, cls).__new__(cls)
        return cls._instance

    def get_workers(cls):
        return cls._lib_workers

    def scan_for_classes_GUI(cls):
        """
        Scan for classes in GUI mode.

        In this approach, all the node libraries are scanned in parallel by using worker threads. The signals of these
        will tell the UI when to populate its elements, so the main UI thread is not blocked while scanning.
        """
        LOGGER.info("Gathering all classes (GUI mode)...")
        cls._time_start = time.time()
        cls._all_classes = dict()

        node_libs = get_all_node_libs()
        cls._lib_workers = [LibWorker(node_lib) for node_lib in node_libs]
        for worker in cls._lib_workers:
            QtCore.QThreadPool.globalInstance().start(worker)
            worker.signaler.finished.connect(cls.update_classes_dict)

    def scan_for_classes(cls):
        LOGGER.info("Gathering all classes...")
        t1 = time.time()  # TODO find something more precise
        cls._all_classes = dict()

        with concurrent.futures.ThreadPoolExecutor(10) as executor:
            futures = [
                executor.submit(register_node_lib, full_path)
                for full_path in get_all_node_libs()
            ]
            for future in concurrent.futures.as_completed(futures):
                cls._all_classes.update(future.result())

        LOGGER.info(f"Total time scanning classes: {time.time() - t1}s.")
        GS.signals.class_scanning_finished.emit()

    def get_all_classes(cls):
        if cls._all_classes is None:
            cls.scan_for_classes()
        return cls._all_classes

    def get_all_scenes(cls):
        if cls._all_scenes is None:
            cls._all_scenes = get_all_scenes_recursive()

        return cls._all_scenes

    def get_all_classes_simplified(cls):
        """
        Get a simplified list of all classes and their corresponding icon paths.

        Returns:
            list: A list of tuples containing the class name and its icon path.
        """
        if cls._all_classes_simplified is None:
            cls._all_classes_simplified = list()
            all_classes = cls.get_all_classes()
            for lib in sorted(all_classes):
                for m in all_classes[lib]:
                    for name, class_object in all_classes[lib][m]["classes"]:
                        cls._all_classes_simplified.append(
                            (name, class_object.ICON_PATH)
                        )

        return cls._all_classes_simplified

    def get_icon_path(cls, class_name_to_search: str):
        """
        Get the icon path for a given class name.

        Args:
            class_name_to_search (str): The name of the class to search for.

        Returns:
            str: The icon path of the class if found, None otherwise.
        """
        for class_name, icon_path in cls.get_all_classes_simplified():
            if class_name_to_search == class_name:
                return icon_path

    def update_classes_dict(cls):
        for worker in cls._lib_workers:
            if worker.finished:
                cls._all_classes.update(worker.dict_lib)
                cls._lib_workers.remove(worker)

        if not len(cls._lib_workers):
            LOGGER.info(
                f"Total time scanning classes: {time.time() - cls._time_start}s."
            )
            GS.signals.class_scanning_finished.emit()

    def flush(cls):
        """
        Resets all class-related attributes to None.
        """
        cls._all_classes = None
        cls._all_scenes = None
        cls._all_classes_simplified = None

        cls._lib_workers = []


CLASS_REGISTRY = ClassRegistry()  # Singleton to use


# -------------------------------- WORKER -------------------------------- #
class LibWorkerSignaler(QtCore.QObject):
    finished = QtCore.Signal()


class LibWorker(QtCore.QRunnable):
    def __init__(self, lib_path: str):
        super(LibWorker, self).__init__()

        self.lib_path = lib_path
        self.lib_name = Path(lib_path).name
        self.dict_lib = None

        self.signaler = LibWorkerSignaler()

        self.finished = False

    def run(self):
        path = self.lib_path.strip()

        # TODO examine classes to make sure there are no repeated names?
        self.dict_lib = register_node_lib(path)
        self.finished = True
        self.signaler.finished.emit()
