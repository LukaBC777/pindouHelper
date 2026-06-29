import numpy as np
from PIL import Image

from pindou.sizing import Board, GridSize
from pindou.quantize import quantize_image


def _grid_size(cols, rows):
    b = Board("t", cols, rows)
    return GridSize(cols=cols, rows=rows, board=b, board_cols=1, board_rows=1)


def test_quantize_maps_pure_colors(tiny_palette, swatch_image):
    g = _grid_size(2, 2)
    grid = quantize_image(swatch_image, g, tiny_palette)
    assert grid.shape == (2, 2)
    # 调色板顺序：R=0,G=1,B=2,W=3；图：左上红 右上绿 左下蓝 右下白
    assert grid[0, 0] == 0
    assert grid[0, 1] == 1
    assert grid[1, 0] == 2
    assert grid[1, 1] == 3


def test_quantize_indices_within_palette(tiny_palette):
    img = Image.new("RGB", (10, 10), (123, 200, 50))
    g = _grid_size(5, 5)
    grid = quantize_image(img, g, tiny_palette)
    assert grid.min() >= 0 and grid.max() < len(tiny_palette)


def test_max_colors_limits_distinct_colors(tiny_palette, swatch_image):
    g = _grid_size(2, 2)
    grid = quantize_image(swatch_image, g, tiny_palette, max_colors=2)
    assert len(set(grid.ravel().tolist())) <= 2


def test_dither_stays_within_palette(tiny_palette):
    img = Image.new("RGB", (8, 8), (180, 180, 180))
    g = _grid_size(4, 4)
    grid = quantize_image(img, g, tiny_palette, dither=True)
    assert grid.min() >= 0 and grid.max() < len(tiny_palette)
