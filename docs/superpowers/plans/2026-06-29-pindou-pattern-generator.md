# 拼豆图纸生成器 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 Windows 桌面程序，把图片像素化成拼豆板网格、用 CIE Lab/CIEDE2000 匹配最接近的豆色，支持手动改色后导出带坐标/色号/用量的图纸（PNG/PDF）。

**Architecture:** 算法层（`color`/`palette`/`sizing`/`quantize`/`bom`/`render`/`editor`）为纯函数/纯数据模块，可独立单元测试；`app` 是 PySide6 薄壳，只编排这些模块并处理交互。数据流：图片 → sizing → quantize → 色号网格 →（bom + render）。手动改色由 `editor` 的覆盖层维护。

**Tech Stack:** Python 3.11+，PySide6（GUI），Pillow（图像 I/O 与绘制），numpy，scikit-image（`rgb2lab` + `deltaE_ciede2000`，避免手写色彩科学），pytest（测试）。

---

## File Structure

```
pindouHelper/
  pyproject.toml                 # 依赖、打包、pytest 配置
  src/pindou/
    __init__.py
    color.py                     # rgb_to_lab + nearest_indices（CIEDE2000）
    palette.py                   # BeadColor、Palette（从 CSV 加载，预算 Lab）
    sizing.py                    # Board、GridSize、compute_grid_size
    quantize.py                  # quantize_image（缩放→匹配→可选抖动/限色）
    bom.py                       # BomEntry、compute_bom
    render.py                    # render_chart（网格/坐标/粗线/板边界/标题/色卡）
    editor.py                    # EditorState（覆盖层 + 撤销/重做）
    app.py                       # PySide6 主窗口 + 程序入口
    data/
      mard.csv                   # 由 scripts/fetch_palette.py 生成并提交
  scripts/
    fetch_palette.py             # 下载并整理 MARD 色表为 data/mard.csv
  tests/
    conftest.py                  # 公用 fixtures（微型调色板、合成图）
    test_color.py
    test_palette.py
    test_sizing.py
    test_quantize.py
    test_bom.py
    test_render.py
    test_editor.py
    test_app_smoke.py
```

**职责边界：** `color` 只做色彩数学；`palette` 只做调色板加载与查询；`sizing`/`quantize`/`bom` 输入输出都是数组与数值，不碰 GUI；`render` 接收网格+调色板产出 `PIL.Image`；`editor` 维护编辑状态；`app` 仅编排。

---

## Task 0: 项目骨架

**Files:**
- Create: `pyproject.toml`
- Create: `src/pindou/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: 创建 `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "pindou"
version = "0.1.0"
description = "图片转拼豆图纸生成器"
requires-python = ">=3.11"
dependencies = [
    "numpy>=1.26",
    "Pillow>=10.2",
    "scikit-image>=0.22",
    "PySide6>=6.6",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
pindou = "pindou.app:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
pindou = ["data/*.csv"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: 创建空包文件**

`src/pindou/__init__.py`:

```python
"""拼豆图纸生成器。"""
__version__ = "0.1.0"
```

- [ ] **Step 3: 创建测试公用 fixtures**

`tests/conftest.py`:

```python
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
```

- [ ] **Step 4: 安装为可编辑包**

Run: `python -m pip install -e ".[dev]"`
Expected: 安装成功，结尾 `Successfully installed pindou-0.1.0`（及依赖）。

- [ ] **Step 5: 验证 pytest 可发现（暂无测试）**

Run: `python -m pytest -q`
Expected: `no tests ran`（退出码 5），证明环境就绪。

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/pindou/__init__.py tests/conftest.py
git commit -m "chore: 项目骨架与依赖"
```

---

## Task 1: color.py — 色彩数学

**Files:**
- Create: `src/pindou/color.py`
- Test: `tests/test_color.py`

- [ ] **Step 1: 写失败测试**

`tests/test_color.py`:

```python
import numpy as np

from pindou.color import rgb_to_lab, nearest_indices


def test_rgb_to_lab_white_is_l100():
    lab = rgb_to_lab(np.array([[255, 255, 255]], dtype=np.uint8))
    assert lab.shape == (1, 3)
    assert abs(lab[0, 0] - 100.0) < 0.5      # L≈100
    assert abs(lab[0, 1]) < 0.5 and abs(lab[0, 2]) < 0.5  # a,b≈0


def test_rgb_to_lab_black_is_l0():
    lab = rgb_to_lab(np.array([[0, 0, 0]], dtype=np.uint8))
    assert abs(lab[0, 0]) < 0.5


def test_nearest_indices_exact_match():
    palette_lab = rgb_to_lab(
        np.array([[255, 0, 0], [0, 255, 0], [0, 0, 255]], dtype=np.uint8)
    )
    pixels_lab = rgb_to_lab(
        np.array([[0, 0, 255], [255, 0, 0]], dtype=np.uint8)
    )
    idx = nearest_indices(pixels_lab, palette_lab)
    assert list(idx) == [2, 0]
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_color.py -q`
Expected: FAIL，`ModuleNotFoundError: No module named 'pindou.color'`

- [ ] **Step 3: 实现 color.py**

```python
"""色彩空间转换与最近邻匹配（CIEDE2000）。"""
import numpy as np
from skimage.color import rgb2lab, deltaE_ciede2000


def rgb_to_lab(rgb):
    """RGB(0-255, 形状 (...,3)) -> CIE Lab，形状不变。"""
    arr = np.asarray(rgb, dtype=np.float64) / 255.0
    flat = arr.reshape(-1, 1, 3)            # rgb2lab 需要图像样形状
    lab = rgb2lab(flat).reshape(arr.shape)
    return lab


def nearest_indices(pixels_lab, palette_lab):
    """对每个像素返回调色板中 CIEDE2000 距离最小的索引。

    pixels_lab: (M,3)，palette_lab: (N,3) -> (M,) int 索引。
    """
    pixels_lab = np.asarray(pixels_lab, dtype=np.float64)
    palette_lab = np.asarray(palette_lab, dtype=np.float64)
    m = pixels_lab.shape[0]
    best = np.full(m, np.inf)
    idx = np.zeros(m, dtype=int)
    for j in range(palette_lab.shape[0]):
        ref = np.broadcast_to(palette_lab[j], (m, 3))
        d = deltaE_ciede2000(pixels_lab, ref)
        better = d < best
        best[better] = d[better]
        idx[better] = j
    return idx
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_color.py -q`
Expected: PASS（3 passed）

- [ ] **Step 5: Commit**

```bash
git add src/pindou/color.py tests/test_color.py
git commit -m "feat: rgb_to_lab 与 CIEDE2000 最近邻匹配"
```

---

## Task 2: palette.py — 调色板

**Files:**
- Create: `src/pindou/palette.py`
- Test: `tests/test_palette.py`

- [ ] **Step 1: 写失败测试**

`tests/test_palette.py`:

```python
import numpy as np

from pindou.palette import BeadColor, Palette


def test_beadcolor_from_rgb_computes_lab():
    c = BeadColor.from_rgb("W1", "white", (255, 255, 255))
    assert c.code == "W1"
    assert c.rgb == (255, 255, 255)
    assert abs(c.lab[0] - 100.0) < 0.5


def test_palette_arrays_align_with_colors(tiny_palette):
    assert len(tiny_palette) == 4
    rgb = tiny_palette.rgb_array()
    lab = tiny_palette.lab_array()
    assert rgb.shape == (4, 3)
    assert lab.shape == (4, 3)
    assert tuple(rgb[0]) == tiny_palette.colors()[0].rgb


def test_palette_from_csv(tmp_path):
    csv = tmp_path / "p.csv"
    csv.write_text(
        "reference_code,name,rgb_r,rgb_g,rgb_b,symbol\n"
        "A1,white,255,255,255,a\n"
        "B2,red,255,0,0,b\n",
        encoding="utf-8",
    )
    pal = Palette.from_csv(csv, name="test")
    assert pal.name == "test"
    assert len(pal) == 2
    assert pal.colors()[1].code == "B2"
    assert pal.colors()[0].symbol == "a"
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_palette.py -q`
Expected: FAIL，`ModuleNotFoundError: No module named 'pindou.palette'`

- [ ] **Step 3: 实现 palette.py**

```python
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
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_palette.py -q`
Expected: PASS（3 passed）

- [ ] **Step 5: Commit**

```bash
git add src/pindou/palette.py tests/test_palette.py
git commit -m "feat: 调色板加载（CSV + 预计算 Lab）"
```

---

## Task 3: 获取并打包 MARD 色表

**Files:**
- Create: `scripts/fetch_palette.py`
- Create: `src/pindou/data/mard.csv`（脚本生成）
- Test: `tests/test_palette.py`（追加一条 bundled 数据 sanity 测试）

- [ ] **Step 1: 写抓取脚本**

`scripts/fetch_palette.py`:

```python
"""下载并整理 MARD 色表为 src/pindou/data/mard.csv。

数据源：https://github.com/maxcleme/beadcolors（raw 格式）。
运行：python scripts/fetch_palette.py
"""
import csv
import io
import pathlib
import urllib.request

SRC = "https://beadcolors.eremes.xyz/raw/mard.csv"
OUT = pathlib.Path(__file__).resolve().parents[1] / "src" / "pindou" / "data" / "mard.csv"


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    raw = urllib.request.urlopen(SRC, timeout=30).read().decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(raw)))
    seen = set()
    out_rows = []
    for r in rows:
        code = r["reference_code"].strip()
        if not code or code in seen:
            continue
        seen.add(code)
        out_rows.append({
            "reference_code": code,
            "name": r.get("name", "").strip(),
            "rgb_r": int(r["rgb_r"]),
            "rgb_g": int(r["rgb_g"]),
            "rgb_b": int(r["rgb_b"]),
            "symbol": r.get("symbol", "").strip(),
        })
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh, fieldnames=["reference_code", "name", "rgb_r", "rgb_g", "rgb_b", "symbol"]
        )
        w.writeheader()
        w.writerows(out_rows)
    print(f"wrote {len(out_rows)} colors -> {OUT}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 运行脚本生成数据**

Run: `python scripts/fetch_palette.py`
Expected: `wrote 2NN colors -> .../src/pindou/data/mard.csv`（数量约 200+；若 raw 无 symbol 列则该列为空，可接受）。

> 若网络不可用：手动从数据源仓库取 `mard.csv` 放到 `src/pindou/data/mard.csv`，保证含列 `reference_code,name,rgb_r,rgb_g,rgb_b`（`symbol` 可缺省）。

- [ ] **Step 3: 追加 bundled 数据 sanity 测试**

在 `tests/test_palette.py` 末尾追加：

```python
import importlib.resources as res


def test_bundled_mard_loads():
    with res.as_file(res.files("pindou.data").joinpath("mard.csv")) as p:
        pal = Palette.from_csv(p, name="mard")
    assert len(pal) > 100
    # 所有 RGB 在合法范围
    rgb = pal.rgb_array()
    assert rgb.min() >= 0 and rgb.max() <= 255
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_palette.py::test_bundled_mard_loads -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/fetch_palette.py src/pindou/data/mard.csv tests/test_palette.py
git commit -m "feat: 抓取并打包 MARD 调色板数据"
```

---

## Task 4: sizing.py — 板型与自动尺寸

**Files:**
- Create: `src/pindou/sizing.py`
- Test: `tests/test_sizing.py`

- [ ] **Step 1: 写失败测试**

`tests/test_sizing.py`:

```python
from pindou.sizing import STANDARD_BOARDS, compute_grid_size


def test_standard_boards_present():
    assert set(STANDARD_BOARDS) == {"15x15", "29x29", "52x52", "52x104"}


def test_square_image_single_square_board():
    board = STANDARD_BOARDS["29x29"]
    g = compute_grid_size(100, 100, board, max_boards_per_axis=3)
    assert g.board_cols == 1 and g.board_rows == 1
    assert g.cols == 29 and g.rows == 29


def test_wide_image_uses_more_columns():
    board = STANDARD_BOARDS["29x29"]
    g = compute_grid_size(300, 100, board, max_boards_per_axis=3)  # 3:1
    assert g.board_cols == 3 and g.board_rows == 1
    assert g.cols == 87 and g.rows == 29


def test_tall_image_uses_more_rows():
    board = STANDARD_BOARDS["29x29"]
    g = compute_grid_size(100, 200, board, max_boards_per_axis=3)  # 1:2
    assert g.board_cols == 1 and g.board_rows == 2


def test_tie_break_prefers_fewer_boards():
    board = STANDARD_BOARDS["29x29"]
    g = compute_grid_size(100, 100, board, max_boards_per_axis=4)
    assert g.board_cols == 1 and g.board_rows == 1  # 不会选 2x2 等更大的同比例解
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_sizing.py -q`
Expected: FAIL，`ModuleNotFoundError: No module named 'pindou.sizing'`

- [ ] **Step 3: 实现 sizing.py**

```python
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
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_sizing.py -q`
Expected: PASS（5 passed）

- [ ] **Step 5: Commit**

```bash
git add src/pindou/sizing.py tests/test_sizing.py
git commit -m "feat: 板型规格与按比例自动尺寸"
```

---

## Task 5: quantize.py — 像素化与匹配（含限色/抖动）

**Files:**
- Create: `src/pindou/quantize.py`
- Test: `tests/test_quantize.py`

- [ ] **Step 1: 写失败测试（基础匹配）**

`tests/test_quantize.py`:

```python
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
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_quantize.py -q`
Expected: FAIL，`ModuleNotFoundError: No module named 'pindou.quantize'`

- [ ] **Step 3: 实现 quantize.py**

```python
"""图片像素化到拼豆网格：缩放 → 匹配 →（可选限色/抖动）。"""
import numpy as np
from PIL import Image
from skimage.color import deltaE_ciede2000

from pindou.color import rgb_to_lab, nearest_indices


def quantize_image(img, grid_size, palette, max_colors=None, dither=False):
    """返回形状 (rows, cols) 的 int 调色板索引网格。"""
    small = img.convert("RGB").resize(
        (grid_size.cols, grid_size.rows), Image.LANCZOS
    )
    arr = np.asarray(small, dtype=np.uint8)        # (rows, cols, 3)
    if dither:
        grid = _floyd_steinberg(arr, palette)
    else:
        flat_lab = rgb_to_lab(arr.reshape(-1, 3))
        idx = nearest_indices(flat_lab, palette.lab_array())
        grid = idx.reshape(grid_size.rows, grid_size.cols)
    if max_colors is not None:
        grid = _reduce_colors(grid, palette, max_colors)
    return grid


def _reduce_colors(grid, palette, max_colors):
    counts = np.bincount(grid.ravel(), minlength=len(palette))
    used = np.nonzero(counts)[0]
    if len(used) <= max_colors:
        return grid
    order = np.argsort(counts[used])[::-1]
    keep = used[order[:max_colors]]
    pal_lab = palette.lab_array()
    keep_lab = pal_lab[keep]
    out = grid.copy()
    for i in used:
        if i in keep:
            continue
        ref = np.broadcast_to(pal_lab[i], (len(keep), 3))
        nearest = keep[int(np.argmin(deltaE_ciede2000(ref, keep_lab)))]
        out[grid == i] = nearest
    return out


def _floyd_steinberg(arr, palette):
    rows, cols, _ = arr.shape
    work = arr.astype(np.float64)
    pal_lab = palette.lab_array()
    pal_rgb = palette.rgb_array().astype(np.float64)
    out = np.zeros((rows, cols), dtype=int)
    for r in range(rows):
        for c in range(cols):
            old = work[r, c].clip(0, 255)
            j = int(nearest_indices(rgb_to_lab(old.reshape(1, 3)), pal_lab)[0])
            out[r, c] = j
            err = old - pal_rgb[j]
            if c + 1 < cols:
                work[r, c + 1] += err * 7 / 16
            if r + 1 < rows:
                if c > 0:
                    work[r + 1, c - 1] += err * 3 / 16
                work[r + 1, c] += err * 5 / 16
                if c + 1 < cols:
                    work[r + 1, c + 1] += err * 1 / 16
    return out
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_quantize.py -q`
Expected: PASS（4 passed）

- [ ] **Step 5: Commit**

```bash
git add src/pindou/quantize.py tests/test_quantize.py
git commit -m "feat: 像素化匹配，含限色与 Floyd-Steinberg 抖动"
```

---

## Task 6: bom.py — 用量清单

**Files:**
- Create: `src/pindou/bom.py`
- Test: `tests/test_bom.py`

- [ ] **Step 1: 写失败测试**

`tests/test_bom.py`:

```python
import numpy as np

from pindou.bom import compute_bom, BomEntry


def test_bom_counts_and_sorts(tiny_palette):
    # 0 出现 3 次，2 出现 1 次，其余 0 次
    grid = np.array([[0, 0], [0, 2]], dtype=int)
    bom = compute_bom(grid, tiny_palette)
    assert all(isinstance(e, BomEntry) for e in bom)
    assert [e.count for e in bom] == [3, 1]      # 降序
    assert bom[0].code == "R1"
    assert bom[1].code == "B1"
    assert sum(e.count for e in bom) == 4


def test_bom_omits_unused(tiny_palette):
    grid = np.array([[3, 3]], dtype=int)
    bom = compute_bom(grid, tiny_palette)
    assert len(bom) == 1 and bom[0].code == "W1"
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_bom.py -q`
Expected: FAIL，`ModuleNotFoundError: No module named 'pindou.bom'`

- [ ] **Step 3: 实现 bom.py**

```python
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
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_bom.py -q`
Expected: PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add src/pindou/bom.py tests/test_bom.py
git commit -m "feat: 用量清单 BOM 统计"
```

---

## Task 7: render.py — 图纸渲染

**Files:**
- Create: `src/pindou/render.py`
- Test: `tests/test_render.py`

- [ ] **Step 1: 写失败测试**

`tests/test_render.py`:

```python
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
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_render.py -q`
Expected: FAIL，`ModuleNotFoundError: No module named 'pindou.render'`

- [ ] **Step 3: 实现 render.py**

```python
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
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_render.py -q`
Expected: PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add src/pindou/render.py tests/test_render.py
git commit -m "feat: 图纸渲染（网格/坐标/板边界/色卡）"
```

---

## Task 8: editor.py — 手动改色与撤销/重做

**Files:**
- Create: `src/pindou/editor.py`
- Test: `tests/test_editor.py`

- [ ] **Step 1: 写失败测试**

`tests/test_editor.py`:

```python
import numpy as np

from pindou.editor import EditorState


def _base():
    return np.array([[0, 0], [0, 0]], dtype=int)


def test_set_cell_reflected_in_grid():
    e = EditorState(_base())
    e.set_cell(0, 1, 3)
    assert e.grid()[0, 1] == 3
    assert e.grid()[0, 0] == 0          # 其余不变


def test_set_cell_does_not_mutate_base():
    base = _base()
    e = EditorState(base)
    e.set_cell(0, 0, 2)
    assert base[0, 0] == 0              # 原始网格不被改


def test_undo_redo_roundtrip():
    e = EditorState(_base())
    e.set_cell(1, 1, 2)
    e.undo()
    assert e.grid()[1, 1] == 0
    e.redo()
    assert e.grid()[1, 1] == 2


def test_set_after_undo_clears_redo():
    e = EditorState(_base())
    e.set_cell(0, 0, 1)
    e.undo()
    e.set_cell(0, 1, 2)
    e.redo()                            # redo 应已被清空，无效果
    assert e.grid()[0, 0] == 0
    assert e.grid()[0, 1] == 2
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_editor.py -q`
Expected: FAIL，`ModuleNotFoundError: No module named 'pindou.editor'`

- [ ] **Step 3: 实现 editor.py**

```python
"""编辑状态：在计算网格之上维护手动覆盖，支持撤销/重做。"""


class EditorState:
    def __init__(self, base_grid):
        self._base = base_grid.astype(int).copy()
        self._overrides = {}          # (r, c) -> index
        self._undo = []               # (r, c, prev_value_or_None)
        self._redo = []

    def grid(self):
        g = self._base.copy()
        for (r, c), i in self._overrides.items():
            g[r, c] = i
        return g

    def set_cell(self, r, c, index):
        prev = self._overrides.get((r, c))
        self._undo.append((r, c, prev))
        self._redo.clear()
        self._overrides[(r, c)] = index

    def undo(self):
        if not self._undo:
            return
        r, c, prev = self._undo.pop()
        cur = self._overrides.get((r, c))
        self._redo.append((r, c, cur))
        if prev is None:
            self._overrides.pop((r, c), None)
        else:
            self._overrides[(r, c)] = prev

    def redo(self):
        if not self._redo:
            return
        r, c, val = self._redo.pop()
        cur = self._overrides.get((r, c))
        self._undo.append((r, c, cur))
        if val is None:
            self._overrides.pop((r, c), None)
        else:
            self._overrides[(r, c)] = val
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_editor.py -q`
Expected: PASS（4 passed）

- [ ] **Step 5: Commit**

```bash
git add src/pindou/editor.py tests/test_editor.py
git commit -m "feat: 手动改色覆盖层与撤销/重做"
```

---

## Task 9: app.py — PySide6 主窗口

**Files:**
- Create: `src/pindou/app.py`
- Test: `tests/test_app_smoke.py`

- [ ] **Step 1: 写冒烟测试**

`tests/test_app_smoke.py`:

```python
import os

import pytest

# 无显示环境下用 offscreen 平台，避免弹窗
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")


def test_mainwindow_constructs():
    from PySide6.QtWidgets import QApplication
    from pindou.app import MainWindow

    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    assert w.windowTitle()
    assert w.board_combo.count() == 4      # 4 种标准板
    w.close()
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_app_smoke.py -q`
Expected: FAIL，`ModuleNotFoundError: No module named 'pindou.app'`

- [ ] **Step 3: 实现 app.py**

```python
"""PySide6 主窗口：导入图片 → 像素化 → 手动改色 → 导出 PNG/PDF。"""
import importlib.resources as res
import sys

import numpy as np
from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QInputDialog,
    QLabel, QMainWindow, QPushButton, QScrollArea, QSpinBox, QVBoxLayout, QWidget,
)

from pindou.bom import compute_bom
from pindou.editor import EditorState
from pindou.palette import Palette
from pindou.quantize import quantize_image
from pindou.render import render_chart
from pindou.sizing import STANDARD_BOARDS, compute_grid_size


def _load_default_palette():
    with res.as_file(res.files("pindou.data").joinpath("mard.csv")) as p:
        return Palette.from_csv(p, name="mard")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("拼豆图纸生成器")
        self.palette = _load_default_palette()
        self.image = None          # 原始 PIL.Image
        self.grid_size = None
        self.editor = None         # EditorState

        # --- 控件 ---
        self.board_combo = QComboBox()
        for name in STANDARD_BOARDS:
            self.board_combo.addItem(name)

        self.maxcolors_spin = QSpinBox()
        self.maxcolors_spin.setRange(0, len(self.palette))
        self.maxcolors_spin.setValue(0)        # 0 = 不限色
        self.maxcolors_spin.setPrefix("最大色数 ")
        self.maxcolors_spin.setSpecialValueText("最大色数 不限")

        self.dither_chk = QCheckBox("抖动")

        open_btn = QPushButton("打开图片")
        gen_btn = QPushButton("生成")
        export_png_btn = QPushButton("导出 PNG")
        export_pdf_btn = QPushButton("导出 PDF")

        open_btn.clicked.connect(self.on_open)
        gen_btn.clicked.connect(self.on_generate)
        export_png_btn.clicked.connect(lambda: self.on_export("png"))
        export_pdf_btn.clicked.connect(lambda: self.on_export("pdf"))

        controls = QHBoxLayout()
        for w in (open_btn, QLabel("板型:"), self.board_combo,
                  self.maxcolors_spin, self.dither_chk, gen_btn,
                  export_png_btn, export_pdf_btn):
            controls.addWidget(w)
        controls.addStretch()

        # --- 预览 ---
        self.preview = QLabel("打开一张图片开始")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.mousePressEvent = self._on_preview_click
        scroll = QScrollArea()
        scroll.setWidget(self.preview)
        scroll.setWidgetResizable(True)

        self.bom_label = QLabel("")
        self.bom_label.setAlignment(Qt.AlignTop)

        body = QHBoxLayout()
        body.addWidget(scroll, 4)
        body.addWidget(self.bom_label, 1)

        root = QVBoxLayout()
        root.addLayout(controls)
        root.addLayout(body)
        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

        self._preview_cell = 12        # 预览每格像素

    # ---------- 交互 ----------
    def on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片 (*.png *.jpg *.jpeg *.bmp)")
        if not path:
            return
        self.image = Image.open(path)
        self.on_generate()

    def on_generate(self):
        if self.image is None:
            return
        board = STANDARD_BOARDS[self.board_combo.currentText()]
        self.grid_size = compute_grid_size(self.image.width, self.image.height, board)
        max_colors = self.maxcolors_spin.value() or None
        grid = quantize_image(self.image, self.grid_size, self.palette,
                              max_colors=max_colors, dither=self.dither_chk.isChecked())
        self.editor = EditorState(grid)
        self._refresh()

    def _on_preview_click(self, event):
        if self.editor is None:
            return
        c = int(event.position().x()) // self._preview_cell
        r = int(event.position().y()) // self._preview_cell
        g = self.editor.grid()
        if not (0 <= r < g.shape[0] and 0 <= c < g.shape[1]):
            return
        codes = [col.code for col in self.palette.colors()]
        code, ok = QInputDialog.getItem(self, "改色", f"({r},{c}) 选新色号", codes,
                                        editable=False)
        if ok:
            self.editor.set_cell(r, c, codes.index(code))
            self._refresh()

    def _refresh(self):
        if self.editor is None:
            return
        grid = self.editor.grid()
        title = f"{self.palette.name}{len(self.palette)}"
        img = render_chart(grid, self.palette, self.grid_size,
                           cell=self._preview_cell, title=title,
                           bom=compute_bom(grid, self.palette))
        self._qt = ImageQt(img.convert("RGB"))     # 保引用防回收
        self.preview.setPixmap(QPixmap.fromImage(self._qt))
        self.preview.resize(img.width, img.height)
        bom = compute_bom(grid, self.palette)
        lines = [f"总数 {sum(e.count for e in bom)}"]
        lines += [f"{e.code}  x{e.count}" for e in bom]
        self.bom_label.setText("\n".join(lines))

    def on_export(self, fmt):
        if self.editor is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出", f"pindou.{fmt}", f"*.{fmt}")
        if not path:
            return
        grid = self.editor.grid()
        title = f"{self.palette.name}{len(self.palette)}"
        img = render_chart(grid, self.palette, self.grid_size, cell=20,
                           show_symbols=True, title=title,
                           bom=compute_bom(grid, self.palette)).convert("RGB")
        img.save(path)


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1100, 800)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_app_smoke.py -q`
Expected: PASS（1 passed）

- [ ] **Step 5: 全量测试**

Run: `python -m pytest -q`
Expected: 全部 PASS。

- [ ] **Step 6: 手动验证（人工）**

Run: `python -m pindou.app`
Expected: 窗口打开 → 打开一张图 → 自动生成像素图纸 → 点格子改色 → 导出 PNG 成功。

- [ ] **Step 7: Commit**

```bash
git add src/pindou/app.py tests/test_app_smoke.py
git commit -m "feat: PySide6 主窗口（生成/改色/导出）"
```

---

## Task 10: 打包为 Windows exe

**Files:**
- Modify: `pyproject.toml`（dev 依赖加 `pyinstaller`）

- [ ] **Step 1: 加打包依赖**

把 `pyproject.toml` 的 dev 依赖改为：

```toml
dev = ["pytest>=8.0", "pyinstaller>=6.3"]
```

- [ ] **Step 2: 安装**

Run: `python -m pip install -e ".[dev]"`
Expected: 安装成功。

- [ ] **Step 3: 打包**

Run:
```bash
pyinstaller --noconfirm --windowed --name pindouHelper ^
  --add-data "src/pindou/data/mard.csv;pindou/data" ^
  src/pindou/app.py
```
Expected: 生成 `dist/pindouHelper/pindouHelper.exe`（scikit-image/scipy 体积较大属正常）。

- [ ] **Step 4: 验证 exe**

双击 `dist/pindouHelper/pindouHelper.exe`，确认窗口打开、能打开图片并生成图纸。

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "build: PyInstaller 打包配置"
```

---

## Self-Review

**1. Spec 覆盖核对：**
- §2 技术选型 → Task 0（依赖：PySide6/Pillow/numpy/scikit-image）✅
- §4 `palette` → Task 2/3；`sizing` → Task 4；`quantize` → Task 5；`bom` → Task 6；`render` → Task 7；`editor_state` → Task 8；`gui` → Task 9 ✅
- §5.1 Lab/CIEDE2000 匹配 → Task 1 + Task 5 ✅
- §5.2 板型自动尺寸（15/29/52/52×104）→ Task 4 ✅
- §5.3 最大色数限制 → Task 5（`_reduce_colors`）✅
- §5.4 抖动默认关、可选 FS → Task 5（`_floyd_steinberg`）+ Task 9（复选框默认未勾）✅
- §5.5 手动改色 + 撤销/重做 → Task 8 + Task 9 点击改色 ✅
- §6 图纸要素（色块/坐标/每10格粗线/板边界/标题/色卡/symbol/PNG·PDF）→ Task 7 + Task 9 导出 ✅
- §7 错误处理（非法图/超大图/调色板缺失）→ 见下「补充」⚠️
- §8 数据获取 → Task 3 ✅
- 两阶段流程（先编辑像素图、再导出）→ Task 9（生成→改色→导出分离）✅

**2. 占位符扫描：** 无 TBD/TODO；每个代码步骤均为完整代码。

**3. 类型一致性核对：** `Palette.colors()/rgb_array()/lab_array()`、`GridSize.cols/rows/board/board_cols/board_rows`、`Board.width/height`、`BomEntry.code/name/rgb/count`、`EditorState.grid()/set_cell/undo/redo` 在各 Task 间签名一致。`quantize_image(img, grid_size, palette, max_colors, dither)` 与 app 调用一致；`render_chart(grid, palette, grid_size, *, cell, margin, show_symbols, title, bom)` 与 app/测试调用一致。

**4. 补充（spec §7 错误处理）：** 当前 MVP 未显式处理「非法图片/超大网格/调色板缺失」。`Image.open` 失败会抛异常、`from_csv` 缺文件会抛 `FileNotFoundError`。下方追加 Task 11 收敛这些边界，避免 GUI 崩溃。

---

## Task 11: 错误处理收敛（spec §7）

**Files:**
- Modify: `src/pindou/sizing.py`（加最大豆数夹取）
- Modify: `src/pindou/app.py`（打开图/生成时捕获异常并提示）
- Test: `tests/test_sizing.py`（追加上限测试）

- [ ] **Step 1: 写失败测试（网格上限夹取）**

在 `tests/test_sizing.py` 追加：

```python
def test_grid_size_clamped_to_max_beads():
    from pindou.sizing import STANDARD_BOARDS, compute_grid_size
    board = STANDARD_BOARDS["52x104"]
    g = compute_grid_size(1000, 100, board, max_boards_per_axis=10, max_beads=200)
    assert g.cols * g.rows <= 200 * 1.0 + g.board.width * g.board.height
    assert g.board_cols >= 1 and g.board_rows >= 1
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_sizing.py::test_grid_size_clamped_to_max_beads -q`
Expected: FAIL，`TypeError: compute_grid_size() got an unexpected keyword argument 'max_beads'`

- [ ] **Step 3: 给 compute_grid_size 加 max_beads 夹取**

把 `src/pindou/sizing.py` 的 `compute_grid_size` 替换为：

```python
def compute_grid_size(image_w, image_h, board, max_boards_per_axis=4,
                      max_beads=20000):
    """选定板型后，按图片宽高比选最接近的拼板数（行×列）。

    在 1..max_boards_per_axis 的板数组合里，最小化总网格宽高比与图片
    宽高比之差；平局时优先板数更少。总豆数超过 max_beads 的组合被跳过
    （至少保留 1×1 板，避免无解）。
    """
    target = image_w / image_h
    best = None
    for bc in range(1, max_boards_per_axis + 1):
        for br in range(1, max_boards_per_axis + 1):
            cols = bc * board.width
            rows = br * board.height
            if cols * rows > max_beads and not (bc == 1 and br == 1):
                continue
            score = abs(cols / rows - target)
            cand = (round(score, 9), bc * br, bc, br, cols, rows)
            if best is None or cand[:2] < best[:2]:
                best = cand
    _, _, bc, br, cols, rows = best
    return GridSize(cols=cols, rows=rows, board=board,
                    board_cols=bc, board_rows=br)
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_sizing.py -q`
Expected: PASS（全部）

- [ ] **Step 5: app 捕获异常提示**

在 `src/pindou/app.py` 顶部 import 区加入 `QMessageBox`：

```python
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QInputDialog,
    QLabel, QMainWindow, QMessageBox, QPushButton, QScrollArea, QSpinBox,
    QVBoxLayout, QWidget,
)
```

把 `on_open` 与 `on_generate` 改为带异常捕获：

```python
    def on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片 (*.png *.jpg *.jpeg *.bmp)")
        if not path:
            return
        try:
            self.image = Image.open(path)
            self.image.load()
        except Exception as exc:                       # noqa: BLE001
            QMessageBox.warning(self, "打开失败", f"无法读取图片：{exc}")
            return
        self.on_generate()

    def on_generate(self):
        if self.image is None:
            return
        try:
            board = STANDARD_BOARDS[self.board_combo.currentText()]
            self.grid_size = compute_grid_size(
                self.image.width, self.image.height, board)
            max_colors = self.maxcolors_spin.value() or None
            grid = quantize_image(
                self.image, self.grid_size, self.palette,
                max_colors=max_colors, dither=self.dither_chk.isChecked())
        except Exception as exc:                       # noqa: BLE001
            QMessageBox.warning(self, "生成失败", str(exc))
            return
        self.editor = EditorState(grid)
        self._refresh()
```

- [ ] **Step 6: 回归冒烟测试**

Run: `python -m pytest tests/test_app_smoke.py -q`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/pindou/sizing.py src/pindou/app.py tests/test_sizing.py
git commit -m "fix: 网格上限夹取与 GUI 异常提示（spec §7）"
```
