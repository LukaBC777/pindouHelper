import numpy as np
import pytest
from PIL import Image

from pindou.palette import BeadColor, Palette


@pytest.fixture
def tiny_palette():
    """4 色微型调色板：红、绿、蓝、白（Lab 由构造函数计算）。"""
    colors = [
        BeadColor.from_rgb("R1", "red", (255, 0, 0)),
        BeadColor.from_rgb("G1", "green", (0, 255, 0)),
        BeadColor.from_rgb("B1", "blue", (0, 0, 255)),
        BeadColor.from_rgb("W1", "white", (255, 255, 255)),
    ]
    return Palette("tiny", colors)


@pytest.fixture
def swatch_image():
    """2x2 图：左上红、右上绿、左下蓝、右下白。"""
    arr = np.array(
        [[[255, 0, 0], [0, 255, 0]],
         [[0, 0, 255], [255, 255, 255]]],
        dtype=np.uint8,
    )
    return Image.fromarray(arr, "RGB")
