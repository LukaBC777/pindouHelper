import numpy as np
from PIL import Image

from pindou.sizing import Board, GridSize
from pindou.bom import compute_bom
from pindou.render import render_chart


def _grid_size(cols, rows, bw, bh):
    return GridSize(cols=cols, rows=rows, board=Board("b", bw, bh),
                    board_cols=cols // bw, board_rows=rows // bh)


def test_render_returns_image_and_contains_cell_colors(tiny_palette):
    grid = np.array([[0, 1], [2, 3]], dtype=int)
    gs = _grid_size(2, 2, 2, 2)
    img = render_chart(grid, tiny_palette, gs, cell=20, title="tiny",
                       bom=compute_bom(grid, tiny_palette))
    assert isinstance(img, Image.Image)
    pixels = set(map(tuple, np.asarray(img.convert("RGB")).reshape(-1, 3)))
    # 每个用到的豆色都应出现在画面里
    for c in tiny_palette.colors():
        assert c.rgb in pixels


def test_render_scales_with_cell_size(tiny_palette):
    grid = np.zeros((2, 2), dtype=int)
    gs = _grid_size(2, 2, 2, 2)
    small = render_chart(grid, tiny_palette, gs, cell=10)
    big = render_chart(grid, tiny_palette, gs, cell=30)
    assert big.width > small.width and big.height > small.height
