# pindouHelper 拼豆图纸生成器

把图片转换成可照着拼的**拼豆图纸**：图片像素化到拼豆板网格，每格匹配最接近的豆子颜色（CIE Lab + CIEDE2000 最近邻），输出带坐标、色号和用量清单（BOM）的图纸。

- 平台：Windows 桌面（Python + PySide6）
- 流程：导入图片 → 选板型自动像素化 → 手动微调豆色 → 导出 PNG / PDF
- 调色板：可切换品牌（基准数据来自开源 [maxcleme/beadcolors](https://github.com/maxcleme/beadcolors) 的 MARD 色表）

设计文档见 [docs/superpowers/specs/2026-06-29-pindou-pattern-generator-design.md](docs/superpowers/specs/2026-06-29-pindou-pattern-generator-design.md)。

> 状态：设计已确认，实现计划编写中。
