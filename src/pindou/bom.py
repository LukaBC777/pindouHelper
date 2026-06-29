"""统计各色号用量。"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BomEntry:
    code: str
    name: str
    rgb: tuple
    count: int


def compute_bom(grid, palette):
    """返回按用量降序的 BomEntry 列表（仅含出现过的色号）。"""
    counts = np.bincount(grid.ravel(), minlength=len(palette))
    colors = palette.colors()
    entries = [
        BomEntry(colors[i].code, colors[i].name, colors[i].rgb, int(counts[i]))
        for i in range(len(palette))
        if counts[i] > 0
    ]
    entries.sort(key=lambda e: e.count, reverse=True)
    return entries
