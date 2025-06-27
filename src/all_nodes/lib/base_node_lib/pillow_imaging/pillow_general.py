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
        "internal_image": {
            "type": PIL.Image.Image,
            "gui_type": PreviewsGUI.IMAGE_PREVIEW,
        },
    }

    def run(self):
        import random
        from PIL import Image

        width = self.get_attribute_value("in_width")
        height = self.get_attribute_value("in_height")
        num_seeds = self.get_attribute_value("num_seeds")

        img = Image.new("RGB", (width, height), (0, 0, 0))
        pixels = img.load()

        # Generate random seed points and assign them a random color
        # Each seed is (x, y, (r, g, b))
        seeds = []
        for _ in range(num_seeds):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            color = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )
            seeds.append((x, y, color))

        # Iterate over each pixel in the image
        for py in range(height):
            for px in range(width):
                min_dist_sq = float("inf")
                closest_color = (0, 0, 0)

                # Find the closest seed point for the current pixel
                for sx, sy, s_color in seeds:
                    # Calculate squared Euclidean distance to avoid sqrt for performance
                    dist_sq = (px - sx) ** 2 + (py - sy) ** 2
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        closest_color = s_color

                # Set the pixel color to the color of the closest seed
                pixels[px, py] = closest_color

        # Display previews
        self.set_output("out_image", img)
        self.set_attribute_value("internal_image", img)


class PIL_PerlinNoise(GeneralLogicNode):
    INPUTS_DICT = {
        "in_width": {"type": int},
        "in_height": {"type": int},
        "scale": {"type": float},
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
        """
        Smooth interpolation curve (6t^5 - 15t^4 + 10t^3).
        Ensures that the derivatives are 0 at t=0 and t=1.
        """
        return t * t * t * (t * (t * 6 - 15) + 10)

    def lerp(self, a, b, t):
        """
        Linear interpolation between a and b based on t.
        """
        return a + t * (b - a)

    def gradient(self, hash_val, x, y):
        """
        Calculates the dot product of a pseudo-random gradient vector and a distance vector.
        hash_val determines the direction of the gradient.
        """
        h = hash_val & 3  # Get the last two bits (0-3) to choose a gradient direction
        # Gradient vectors for 2D Perlin noise
        # (1,1), (-1,1), (1,-1), (-1,-1) are chosen
        if h == 0:
            return x + y
        elif h == 1:
            return -x + y
        elif h == 2:
            return x - y
        else:  # h == 3
            return -x - y

    def run(self):
        import random
        from PIL import Image

        width = self.get_attribute_value("in_width")
        height = self.get_attribute_value("in_height")
        scale = self.get_attribute_value("scale")

        # Create a new blank image with black background (mode 'L' for grayscale)
        img = Image.new("L", (width, height), 0)
        pixels = img.load()

        # Perlin noise permutation table for pseudo-randomness
        # A list of numbers from 0-255, shuffled, and then doubled for wrapping
        p = list(range(256))
        random.shuffle(p)
        p += p  # Duplicate the list for easy wrapping (p[256] == p[0])

        # Iterate over each pixel in the image
        for py in range(height):
            for px in range(width):
                # Map pixel coordinates to noise input coordinates based on scale
                x = px / scale
                y = py / scale

                # Determine grid cell coordinates of the four corners
                xi = int(x) & 255  # Integer part, wrapped to 0-255
                yi = int(y) & 255

                # Fractional part (t-values for interpolation)
                xf = x - int(x)
                yf = y - int(y)

                # Fade curves for interpolation
                u = self.fade(xf)
                v = self.fade(yf)

                # Hash coordinates of the 4 corners of the square
                # p[] takes values in 0-255, p[p[]+x] accesses a pseudo-random value
                aa = p[p[xi] + yi]
                ba = p[p[xi + 1] + yi]
                ab = p[p[xi] + yi + 1]
                bb = p[p[xi + 1] + yi + 1]

                # Calculate gradients at each corner and then the dot product
                # of gradient vector and distance vector to the point (xf, yf)
                x1 = self.lerp(
                    self.gradient(aa, xf, yf),  # Top-left corner
                    self.gradient(ba, xf - 1, yf),  # Top-right corner
                    u,
                )
                x2 = self.lerp(
                    self.gradient(ab, xf, yf - 1),  # Bottom-left corner
                    self.gradient(bb, xf - 1, yf - 1),  # Bottom-right corner
                    u,
                )

                # Interpolate the results vertically
                noise_value = self.lerp(x1, x2, v)

                # Map the noise value (typically -1 to 1) to grayscale (0-255)
                # Add 1 to shift range to 0-2, then multiply by 127.5 to get 0-255
                color = int((noise_value + 1) * 127.5)
                pixels[px, py] = color

        # Display previews
        self.set_output("out_image", img.convert("RGB"))
        self.set_attribute_value("internal_image", img.convert("RGB"))


class PIL_SimplexNoise(GeneralLogicNode):
    INPUTS_DICT = {
        "in_width": {"type": int},
        "in_height": {"type": int},
        "scale": {"type": float},
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

    def dot(self, g, x, y):
        """Calculates the dot product of a gradient vector and a distance vector."""
        return g[0] * x + g[1] * y

    def simplex_noise_2d(self, xin, yin, p_table):
        """
        Generates 2D Simplex noise for a given point.

        Args:
            xin (float): X-coordinate of the point.
            yin (float): Y-coordinate of the point.
            p_table (list): Permutation table for pseudo-randomness.

        Returns:
            float: The noise value, typically in the range [-1, 1].
        """
        import math

        F2 = 0.5 * (math.sqrt(3.0) - 1.0)  # (sqrt(3)-1)/2
        G2 = (3.0 - math.sqrt(3.0)) / 6.0  # (3-sqrt(3))/6

        GRADIENTS = [
            (1, 1),
            (-1, 1),
            (1, -1),
            (-1, -1),
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
        ]

        # Skew the input coordinates to where the simplex grid lies
        s = (xin + yin) * F2
        i = math.floor(xin + s)
        j = math.floor(yin + s)
        t = (i + j) * G2
        x0 = xin - i + t
        y0 = yin - j + t

        # For 2D, the simplex is an equilateral triangle.
        # Determine which simplex we are in (lower left or upper right triangle)
        if x0 > y0:
            i1 = 1
            j1 = 0
        else:
            i1 = 0
            j1 = 1

        # Coordinates of the three corners of the simplex in the unskewed space
        x1 = x0 - i1 + G2
        y1 = y0 - j1 + G2
        x2 = x0 - 1.0 + 2.0 * G2
        y2 = y0 - 1.0 + 2.0 * G2

        # Hash coordinates of the corners
        # Use modulo 256 for wrapping with the permutation table
        ii = i & 255
        jj = j & 255

        # Get gradient indices from the permutation table
        gi0 = p_table[ii + p_table[jj]] % 8  # Use % 8 for GRADIENTS array size
        gi1 = p_table[ii + i1 + p_table[jj + j1]] % 8
        gi2 = p_table[ii + 1 + p_table[jj + 1]] % 8

        # Calculate contribution from each corner of the simplex
        noise = 0.0

        # Corner 0
        t0 = 0.5 - x0 * x0 - y0 * y0
        if t0 >= 0:
            t0 *= t0
            noise += t0 * t0 * self.dot(GRADIENTS[gi0], x0, y0)

        # Corner 1
        t1 = 0.5 - x1 * x1 - y1 * y1
        if t1 >= 0:
            t1 *= t1
            noise += t1 * t1 * self.dot(GRADIENTS[gi1], x1, y1)

        # Corner 2
        t2 = 0.5 - x2 * x2 - y2 * y2
        if t2 >= 0:
            t2 *= t2
            noise += t2 * t2 * self.dot(GRADIENTS[gi2], x2, y2)

        # Scale the output to a reasonable range, typically -1 to 1,
        # then adjust to match an appropriate amplitude for visualization.
        # The factor 70.0 is empirical for 2D to make the noise visible and span a good range.
        return noise * 70.0  # Adjust this multiplier to change the intensity/contrast

    def run(self):
        import random
        from PIL import Image

        width = self.get_attribute_value("in_width")
        height = self.get_attribute_value("in_height")
        scale = self.get_attribute_value("scale")

        img = Image.new("RGB", (width, height), (0, 0, 0))
        pixels = img.load()

        # Simplex noise permutation table
        # A list of numbers from 0-255, shuffled, and then doubled for wrapping
        p = list(range(256))
        random.shuffle(p)
        p += p  # Duplicate the list for easy wrapping (p[256] == p[0])

        # Iterate over each pixel in the image
        for py in range(height):
            for px in range(width):
                # Map pixel coordinates to noise input coordinates based on scale
                # We divide by scale to "stretch" the noise over the image
                noise_val = self.simplex_noise_2d(px / scale, py / scale, p)

                # Map the noise value (typically -1 to 1 after scaling) to grayscale (0-255)
                # Clip values to ensure they are within the valid range
                color = int((noise_val + 1) * 127.5)  # Map [-1, 1] to [0, 255]
                color = max(0, min(255, color))  # Clamp to 0-255

                pixels[px, py] = (
                    color,
                    color,
                    color,
                )  # Set RGB values to the grayscale color

        # Display previews
        self.set_output("out_image", img.convert("RGB"))
        self.set_attribute_value("internal_image", img.convert("RGB"))
