"""把色号网格渲染成图纸：色块、坐标、每10格粗线、板边界、标题、色卡。"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

_GRID = (200, 200, 200)
_HEAVY = (90, 90, 90)
_BOARD = (220, 40, 40)
_TEXT = (0, 0, 0)
_BG = (255, 255, 255)


def _font():
    return ImageFont.load_default()


def render_chart(grid, palette, grid_size, *, cell=20, margin=24,
                 show_symbols=False, title="", bom=None):
    rows, cols = grid.shape
    rgb = palette.rgb_array()
    colors = palette.colors()
    font = _font()

    coord_band = cell                      # 顶部/左侧坐标带
    title_h = 0 if not title else cell + 8
    legend_h = 0 if not bom else _legend_height(bom, cols * cell, font)

    grid_x0 = margin + coord_band
    grid_y0 = margin + title_h + coord_band
    width = grid_x0 + cols * cell + margin
    height = grid_y0 + rows * cell + (legend_h + margin if bom else margin)

    img = Image.new("RGB", (width, height), _BG)
    d = ImageDraw.Draw(img)

    if title:
        d.text((grid_x0, margin), title, fill=_TEXT, font=font)

    # 色块
    for r in range(rows):
        for c in range(cols):
            x0 = grid_x0 + c * cell
            y0 = grid_y0 + r * cell
            d.rectangle([x0, y0, x0 + cell, y0 + cell],
                        fill=tuple(int(v) for v in rgb[grid[r, c]]))
            if show_symbols:
                sym = colors[grid[r, c]].symbol
                if sym:
                    d.text((x0 + 2, y0 + 1), sym, fill=_TEXT, font=font)

    # 细网格线
    for c in range(cols + 1):
        x = grid_x0 + c * cell
        d.line([(x, grid_y0), (x, grid_y0 + rows * cell)], fill=_GRID)
    for r in range(rows + 1):
        y = grid_y0 + r * cell
        d.line([(grid_x0, y), (grid_x0 + cols * cell, y)], fill=_GRID)

    # 每 10 格粗线 + 坐标数字
    for c in range(0, cols + 1, 10):
        x = grid_x0 + c * cell
        d.line([(x, grid_y0), (x, grid_y0 + rows * cell)], fill=_HEAVY, width=2)
        if c < cols:
            d.text((x + 2, grid_y0 - coord_band + 2), str(c), fill=_TEXT, font=font)
    for r in range(0, rows + 1, 10):
        y = grid_y0 + r * cell
        d.line([(grid_x0, y), (grid_x0 + cols * cell, y)], fill=_HEAVY, width=2)
        if r < rows:
            d.text((grid_x0 - coord_band + 2, y + 2), str(r), fill=_TEXT, font=font)

    # 板边界线（更粗的红线）
    bw = grid_size.board.width
    bh = grid_size.board.height
    for c in range(0, cols + 1, bw):
        x = grid_x0 + c * cell
        d.line([(x, grid_y0), (x, grid_y0 + rows * cell)], fill=_BOARD, width=3)
    for r in range(0, rows + 1, bh):
        y = grid_y0 + r * cell
        d.line([(grid_x0, y), (grid_x0 + cols * cell, y)], fill=_BOARD, width=3)

    # 底部色卡
    if bom:
        _draw_legend(d, bom, grid_x0, grid_y0 + rows * cell + margin // 2,
                     cols * cell, font)

    return img


def _legend_swatch():
    return 16


def _legend_height(bom, avail_w, font):
    sw = _legend_swatch()
    per_row = max(1, avail_w // 110)
    nrows = (len(bom) + per_row - 1) // per_row
    return nrows * (sw + 6) + 8


def _draw_legend(d, bom, x0, y0, avail_w, font):
    sw = _legend_swatch()
    per_row = max(1, avail_w // 110)
    for i, e in enumerate(bom):
        col = i % per_row
        row = i // per_row
        x = x0 + col * 110
        y = y0 + row * (sw + 6)
        d.rectangle([x, y, x + sw, y + sw], fill=e.rgb, outline=_HEAVY)
        d.text((x + sw + 4, y + 2), f"{e.code} x{e.count}", fill=_TEXT, font=font)
