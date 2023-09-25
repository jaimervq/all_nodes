# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import OptionInput
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class ImageFileExtensionSelect(OptionInput):
    INPUT_OPTIONS = [".png", ".exr", ".jpg"]
    NICE_NAME = "Image file extension select"


class TextFileExtensionSelect(OptionInput):
    INPUT_OPTIONS = [".txt", ".json", ".yml"]
    NICE_NAME = "Text file extension select"
