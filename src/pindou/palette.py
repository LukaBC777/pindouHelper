"""拼豆调色板：色号、RGB、预计算 Lab，可从 CSV 加载。"""
import csv as _csv
from dataclasses import dataclass

import numpy as np

from pindou.color import rgb_to_lab


@dataclass(frozen=True)
class BeadColor:
    code: str
    name: str
    rgb: tuple
    lab: tuple
    symbol: str = ""

    @classmethod
    def from_rgb(cls, code, name, rgb, symbol=""):
        lab = rgb_to_lab(np.array([rgb], dtype=np.uint8))[0]
        return cls(code, name, tuple(int(x) for x in rgb),
                   tuple(float(x) for x in lab), symbol)


class Palette:
    def __init__(self, name, colors):
        self._name = name
        self._colors = list(colors)
        self._rgb = np.array([c.rgb for c in self._colors], dtype=np.uint8)
        self._lab = np.array([c.lab for c in self._colors], dtype=np.float64)

    @property
    def name(self):
        return self._name

    def __len__(self):
        return len(self._colors)

    def colors(self):
        return self._colors

    def rgb_array(self):
        return self._rgb

    def lab_array(self):
        return self._lab

    @classmethod
    def from_csv(cls, path, name):
        colors = []
        with open(path, newline="", encoding="utf-8") as fh:
            for row in _csv.DictReader(fh):
                colors.append(BeadColor.from_rgb(
                    row["reference_code"],
                    row.get("name", ""),
                    (int(row["rgb_r"]), int(row["rgb_g"]), int(row["rgb_b"])),
                    row.get("symbol", "") or "",
                ))
        return cls(name, colors)
