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
