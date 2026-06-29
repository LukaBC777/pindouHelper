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


import importlib.resources as res


def test_bundled_mard_loads():
    with res.as_file(res.files("pindou.data").joinpath("mard.csv")) as p:
        pal = Palette.from_csv(p, name="mard")
    assert len(pal) > 100
    # 所有 RGB 在合法范围
    rgb = pal.rgb_array()
    assert rgb.min() >= 0 and rgb.max() <= 255
