# pindouHelper 拼豆图纸生成器

把图片转换成可照着拼的**拼豆图纸**：图片像素化到拼豆板网格，每格匹配最接近的豆子颜色（CIE Lab + CIEDE2000 最近邻），输出带坐标、色号和用量清单（BOM）的图纸。

- 平台：Windows 桌面（Python + PySide6）
- 流程：导入图片 → 选板型自动像素化 → 手动微调豆色 → 导出 PNG / PDF
- 调色板：可切换品牌（基准数据来自开源 [maxcleme/beadcolors](https://github.com/maxcleme/beadcolors) 的 MARD 色表，默认 291 色）

## 运行

```bash
python -m pip install -e ".[dev]"   # 安装依赖
python -m pindou.app                 # 启动桌面程序
python -m pytest -q                  # 运行测试
```

## 打包为 Windows exe

```bash
pyinstaller --noconfirm --windowed --name pindouHelper \
  --add-data "src/pindou/data/mard.csv;pindou/data" \
  --collect-submodules skimage --collect-data skimage \
  --collect-submodules scipy --collect-submodules PIL \
  --exclude-module matplotlib src/pindou/app.py
```

> 状态：核心功能已实现，测试通过。星芒拼豆 221 色的精确色号映射待后续校准。
