# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import PIL

from all_nodes.constants import InputsGUI, PreviewsGUI
from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class PIL_ImageOpen(GeneralLogicNode):
    INPUTS_DICT = {"in_path": {"type": str}}
    OUTPUTS_DICT = {"out_image": {"type": PIL.Image.Image}}

    def run(self):
        self.set_output(
            "out_image",
            PIL.Image.open(self.get_attribute_value("in_path")),
        )


class PIL_ImagePreview(GeneralLogicNode):
    INPUTS_DICT = {"in_image": {"type": PIL.Image.Image}}

    INTERNALS_DICT = {
        "internal_image": {
            "type": PIL.Image.Image,
            "gui_type": PreviewsGUI.IMAGE_PREVIEW,
        }
    }

    def run(self):
        self.set_attribute_value("internal_image", self.get_attribute_value("in_image"))


class PIL_DirectOpen(GeneralLogicNode):
    OUTPUTS_DICT = {
        "out_image": {"type": PIL.Image.Image},
        "out_image_path": {"type": str},
    }

    INTERNALS_DICT = {
        "internal_str_image_path": {
            "type": str,
            "gui_type": InputsGUI.STR_INPUT,
        },
        "internal_image": {
            "type": PIL.Image.Image,
            "gui_type": PreviewsGUI.IMAGE_PREVIEW,
        },
    }

    def run(self):
        # Get inputs
        path = self.get_attribute_value("internal_str_image_path")
        opened_image = PIL.Image.open(path)

        # Set outputs
        self.set_output(
            "out_image",
            opened_image,
        )
        self.set_output(
            "out_image_path",
            path,
        )

        # Display previews
        self.set_attribute_value("internal_image", opened_image)


class PIL_OpenFromUrl(GeneralLogicNode):
    INPUTS_DICT = {"in_url": {"type": str}}

    OUTPUTS_DICT = {"out_image": {"type": PIL.Image.Image}}

    def run(self):
        import requests

        data = requests.get(self.get_attribute_value("in_url"), stream=True).raw
        img = PIL.Image.open(data)
        self.set_output("out_image", img)
