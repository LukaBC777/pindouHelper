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
