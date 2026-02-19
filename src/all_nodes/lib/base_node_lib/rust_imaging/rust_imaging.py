# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2026, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import numpy as np
import PIL

from all_nodes.constants import PreviewsGUI
from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes.helpers.rust import rust_image_processing
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


def rust_image_to_pil(rust_img, gamma=2.2):
    w = rust_img.width
    h = rust_img.height

    pixels = rust_img.get_pixels()
    arr = np.array(pixels, dtype=np.float32).reshape((h, w, 4))

    # optional gamma (TODO this properly with colorspaces)
    arr = np.power(np.clip(arr, 0, None), 1 / gamma)

    # TODO detect alpha properly
    alpha = arr[..., 3]
    has_alpha = not np.all(alpha == 0.0)
    if not has_alpha:
        arr[..., 3] = 1.0

    arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)

    # create PIL image
    img = PIL.Image.fromarray(arr, mode="RGBA")
    return img


class LoadExr_Rust(GeneralLogicNode):
    INPUTS_DICT = {
        "in_exr_path": {"type": str},
    }
    OUTPUTS_DICT = {
        "out_image": {"type": rust_image_processing.RustImage},
    }

    def run(self):
        rust_img = rust_image_processing.load_exr(self.get_input("in_exr_path"))
        self.set_output(
            "out_image",
            rust_img,
        )


class PreviewExr_Rust(LoadExr_Rust):
    INPUTS_DICT = {
        "in_image": {"type": rust_image_processing.RustImage},
    }

    OUTPUTS_DICT = {
        "out_image": {"type": rust_image_processing.RustImage},
    }

    INTERNALS_DICT = {
        "internal_image": {
            "type": PIL.Image.Image,
            "gui_type": PreviewsGUI.IMAGE_PREVIEW,
        },
    }

    def run(self):
        rust_img = self.get_input("in_image")
        pil_img = rust_image_to_pil(rust_img)

        self.set_attribute_value("internal_image", pil_img)
        self.set_output(
            "out_image",
            rust_img,
        )
