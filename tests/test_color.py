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
