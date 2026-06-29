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
