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
