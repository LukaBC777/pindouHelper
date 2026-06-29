"""拼豆板规格与按图片比例自动计算网格尺寸。"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Board:
    name: str
    width: int   # 单板宽（豆）
    height: int  # 单板高（豆）


STANDARD_BOARDS = {
    "15x15": Board("15x15", 15, 15),
    "29x29": Board("29x29", 29, 29),
    "52x52": Board("52x52", 52, 52),
    "52x104": Board("52x104", 52, 104),
}


@dataclass(frozen=True)
class GridSize:
    cols: int        # 总宽（豆）
    rows: int        # 总高（豆）
    board: Board
    board_cols: int  # 横向板数
    board_rows: int  # 纵向板数


def compute_grid_size(image_w, image_h, board, max_boards_per_axis=4):
    """选定板型后，按图片宽高比选最接近的拼板数（行×列）。

    在 1..max_boards_per_axis 的板数组合里，最小化总网格宽高比与
    图片宽高比之差；平局时优先板数更少（总豆数更小）的方案。
    """
    target = image_w / image_h
    best = None  # (score, total_boards, GridSize)
    for bc in range(1, max_boards_per_axis + 1):
        for br in range(1, max_boards_per_axis + 1):
            cols = bc * board.width
            rows = br * board.height
            score = abs(cols / rows - target)
            cand = (round(score, 9), bc * br, bc, br, cols, rows)
            if best is None or cand[:2] < best[:2]:
                best = cand
    _, _, bc, br, cols, rows = best
    return GridSize(cols=cols, rows=rows, board=board,
                    board_cols=bc, board_rows=br)
