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
