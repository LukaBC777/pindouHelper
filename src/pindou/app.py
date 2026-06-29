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
