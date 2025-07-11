# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import numpy as np
import PIL

from all_nodes.constants import InputsGUI, PreviewsGUI
from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)
MAX_W = 500  # Only for previews, otherwise it will crash


class PIL_ImageOpen(GeneralLogicNode):
    INPUTS_DICT = {"in_path": {"type": str}}
    OUTPUTS_DICT = {"out_image": {"type": PIL.Image.Image}}

    def run(self):
        self.set_output(
            "out_image",
            PIL.Image.open(self.get_input("in_path")),
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
        img = self.get_input("in_image")
        w_percent = MAX_W / float(img.width)
        new_height = int(img.height * w_percent)
        self.set_attribute_value("internal_image", img.resize((MAX_W, new_height)))


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
        from io import BytesIO
        import os
        import requests

        # Get inputs
        path = self.get_attribute_value("internal_str_image_path")
        if os.path.exists(path):
            opened_image = PIL.Image.open(path)
        else:
            response = requests.get(path)
            response.raise_for_status()
            opened_image = PIL.Image.open(BytesIO(response.content))

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
        w_percent = MAX_W / float(opened_image.width)
        new_height = int(opened_image.height * w_percent)
        self.set_attribute_value(
            "internal_image", opened_image.resize((MAX_W, new_height))
        )


class PIL_OpenFromUrl(GeneralLogicNode):
    INPUTS_DICT = {"in_url": {"type": str}}
    OUTPUTS_DICT = {"out_image": {"type": PIL.Image.Image}}

    def run(self):
        from io import BytesIO
        import requests

        response = requests.get(self.get_attribute_value("in_url"))
        response.raise_for_status()

        img = PIL.Image.open(BytesIO(response.content))
        self.set_output("out_image", img)


class PIL_Checkerboard(GeneralLogicNode):
    OUTPUTS_DICT = {
        "out_image": {"type": PIL.Image.Image},
    }

    INTERNALS_DICT = {
        "internal_image": {
            "type": PIL.Image.Image,
            "gui_type": PreviewsGUI.IMAGE_PREVIEW,
        },
    }

    def run(self):
        from PIL import Image

        width, height = 100, 100

        color_grid = [[0] * height for _ in range(width)]
        row = 0
        column = 0
        for i in range(height):
            if i % 10 == 0:
                row += 1
            for j in range(width):
                if j % 10 == 0:
                    column += 1

                if (row + column) % 2 == 0:
                    color = (0, 0, 0)
                else:
                    color = (255, 255, 255)

                color_grid[i][j] = color

        flat_pixels = [pixel for row in color_grid for pixel in row]

        img = Image.new("RGB", (width, height))
        img.putdata(flat_pixels)

        self.set_output("out_image", img)
        self.set_attribute_value("internal_image", img)


class PIL_VoronoiNoise(GeneralLogicNode):
    INPUTS_DICT = {
        "in_width": {"type": int},
        "in_height": {"type": int},
        "num_seeds": {"type": int},
    }

    OUTPUTS_DICT = {
        "out_image": {"type": PIL.Image.Image},
    }

    INTERNALS_DICT = {
        "executor_type": {
            "type": str,
            "gui_type": InputsGUI.OPTION_INPUT,
            "options": ["Rust", "Python"],
        },
        "internal_image": {
            "type": PIL.Image.Image,
            "gui_type": PreviewsGUI.IMAGE_PREVIEW,
        },
        "internal_time_feedback": {
            "type": str,
            "gui_type": PreviewsGUI.STR_PREVIEW,
        },
    }

    def generate_voronoi_rgb(self, height, width, num_seeds, seed=None):
        if seed is not None:
            np.random.seed(seed)

        # Random seed positions
        seed_points = np.random.randint(0, [width, height], size=(num_seeds, 2))

        # Random RGB color for each seed
        colors = np.random.randint(0, 256, size=(num_seeds, 3), dtype=np.uint8)

        # Coordinates of each pixel in the image
        y, x = np.indices((height, width))
        coords = np.stack((x, y), axis=-1)

        # Compute squared distance from every pixel to every seed
        diff = coords[:, :, None, :] - seed_points[None, None, :, :]
        distances = np.sum(diff**2, axis=-1)

        # Find closest seed for each pixel
        nearest = np.argmin(distances, axis=-1)

        # Assign color from the closest seed
        image_rgb = colors[nearest]

        # Flatten into 1D array of bytes for PIL
        return image_rgb.reshape(-1)

    def run(self):
        import platform
        import time

        from PIL import Image

        width = self.get_attribute_value("in_width")
        height = self.get_attribute_value("in_height")
        num_seeds = self.get_attribute_value("num_seeds")

        execution_start = time.perf_counter()

        if self.get_attribute_value("executor_type") == "Rust":
            if platform.system() in ["Windows", "Linux"]:
                from all_nodes.helpers.rust import rust_noise

                rgb_flat = rust_noise.voronoi_rgb(width, height, num_seeds)
            else:
                self.fail(
                    "Rust executor is not avaliable for this platform. Please use Python executor instead"
                )
        else:
            rgb_flat = self.generate_voronoi_rgb(width, height, num_seeds)

        img = Image.frombytes("RGB", (width, height), bytes(rgb_flat))

        # Out
        self.set_attribute_value(
            "internal_time_feedback",
            f"Execution time: {(time.perf_counter() - execution_start):.4f}",
        )
        self.set_output("out_image", img)
        self.set_attribute_value("internal_image", img)


class PIL_PerlinNoise(GeneralLogicNode):
    INPUTS_DICT = {
        "in_width": {"type": int},
        "in_height": {"type": int},
        "scale": {"type": float},
        "seed": {"type": int, "optional": True},
    }

    OUTPUTS_DICT = {
        "out_image": {"type": PIL.Image.Image},
    }

    INTERNALS_DICT = {
        "internal_image": {
            "type": PIL.Image.Image,
            "gui_type": PreviewsGUI.IMAGE_PREVIEW,
        },
    }

    def fade(self, t):
        return 6 * t**5 - 15 * t**4 + 10 * t**3

    def lerp(self, a, b, t):
        return a + t * (b - a)

    def get_gradient_vectors(self):
        return np.array(
            [[0, 1], [0, -1], [1, 0], [-1, 0], [1, 1], [-1, 1], [1, -1], [-1, -1]]
        )

    def generate_perlin_noise(self, height, width, scale=10, seed=None):
        if seed is not None:
            np.random.seed(seed)

        gradient_vectors = self.get_gradient_vectors()

        # Grid size in gradient space
        grid_x = int(width // scale + 2)
        grid_y = int(height // scale + 2)

        # Random gradient indices
        gradient_grid = np.random.randint(0, 8, (grid_y, grid_x))

        # Image pixel coordinates
        y, x = np.indices((height, width))
        xf = x / scale
        yf = y / scale

        xi = xf.astype(int)
        yi = yf.astype(int)
        xf -= xi
        yf -= yi

        u = self.fade(xf)
        v = self.fade(yf)

        # Get gradients from corners
        aa = gradient_vectors[gradient_grid[yi % grid_y, xi % grid_x]]
        ab = gradient_vectors[gradient_grid[(yi + 1) % grid_y, xi % grid_x]]
        ba = gradient_vectors[gradient_grid[yi % grid_y, (xi + 1) % grid_x]]
        bb = gradient_vectors[gradient_grid[(yi + 1) % grid_y, (xi + 1) % grid_x]]

        # Offset vectors
        d_aa = np.stack([xf, yf], axis=-1)
        d_ba = np.stack([xf - 1, yf], axis=-1)
        d_ab = np.stack([xf, yf - 1], axis=-1)
        d_bb = np.stack([xf - 1, yf - 1], axis=-1)

        # Dot products
        dot_aa = np.sum(aa * d_aa, axis=-1)
        dot_ba = np.sum(ba * d_ba, axis=-1)
        dot_ab = np.sum(ab * d_ab, axis=-1)
        dot_bb = np.sum(bb * d_bb, axis=-1)

        # Interpolation
        lerp_x1 = self.lerp(dot_aa, dot_ba, u)
        lerp_x2 = self.lerp(dot_ab, dot_bb, u)
        perlin = self.lerp(lerp_x1, lerp_x2, v)

        # Normalize to [0, 255]
        perlin -= perlin.min()
        perlin /= perlin.max()
        perlin *= 255

        return perlin.astype(np.uint8).reshape(-1)

    def run(self):
        from PIL import Image

        width = self.get_attribute_value("in_width")
        height = self.get_attribute_value("in_height")
        scale = self.get_attribute_value("scale")

        # Create a new blank image with black background (mode 'L' for grayscale)
        pixels = self.generate_perlin_noise(
            height, width, scale=scale, seed=self.get_attribute_value("seed") or 123
        )
        img = Image.frombytes("L", (width, height), pixels.tobytes()).convert("RGB")

        # Display previews
        self.set_output("out_image", img)
        self.set_attribute_value("internal_image", img)


class PIL_FbmNoise(GeneralLogicNode):
    INPUTS_DICT = {
        "in_width": {"type": int},
        "in_height": {"type": int},
        "scale": {"type": float},
        "seed": {"type": int},
    }

    OUTPUTS_DICT = {
        "out_image": {"type": PIL.Image.Image},
    }

    INTERNALS_DICT = {
        "internal_image": {
            "type": PIL.Image.Image,
            "gui_type": PreviewsGUI.IMAGE_PREVIEW,
        },
        "internal_time_feedback": {
            "type": str,
            "gui_type": PreviewsGUI.STR_PREVIEW,
        },
    }

    def run(self):
        import platform
        import time

        from PIL import Image

        width = self.get_attribute_value("in_width")
        height = self.get_attribute_value("in_height")
        scale = self.get_attribute_value("scale")
        seed = self.get_attribute_value("seed")

        execution_start = time.perf_counter()

        if platform.system() in ["Windows", "Linux"]:
            from all_nodes.helpers.rust import rust_noise

            rgb_flat = rust_noise.colorful_fbm_noise(width, height, scale, seed)
            img = Image.frombytes("RGB", (width, height), bytes(rgb_flat))
        else:
            self.fail("This node is not supported on this platform")
            return

        # Out
        self.set_attribute_value(
            "internal_time_feedback",
            f"Execution time: {(time.perf_counter() - execution_start):.4f}",
        )
        self.set_output("out_image", img)
        self.set_attribute_value("internal_image", img)


class PIL_SaveImage(GeneralLogicNode):
    INPUTS_DICT = {
        "in_image": {"type": PIL.Image.Image},
        "in_path": {"type": str},
    }

    def run(self):
        img = self.get_input("in_image")
        img.save(self.get_input("in_path"))
