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
