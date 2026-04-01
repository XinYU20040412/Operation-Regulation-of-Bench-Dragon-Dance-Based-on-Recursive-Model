# viz_output

本目录存放第二问优化可视化脚本自动生成的结果文件。

## 快速入口

- 项目首页：[../../../README.md](../../../README.md)
- 正式代码说明：[../README.md](../README.md)
- 交互式 Dashboard：[collision_dashboard.html](collision_dashboard.html)
- 结构化摘要：[summary.json](summary.json)
- 逐帧指标：[collision_metrics.csv](collision_metrics.csv)

## 文件说明

- `collision_cover.png`：封面图，适合放在仓库 README 顶部。
- `dragon_motion.gif`：碰撞过程 GIF 动画。
- `collision_timeline.png`：最小安全间距时间线图。
- `collision_frame.png`：首次碰撞关键帧（若无碰撞则为末帧）。
- `collision_dashboard.html`：交互式可视化页面（滑块 + 回放）。
- `collision_metrics.csv`：逐帧指标表。
- `summary.json`：结构化运行摘要。

## 可视化预览

![Cover](collision_cover.png)

![Timeline](collision_timeline.png)

![Collision Frame](collision_frame.png)

## 关键指标

- collision_found: `True`
- first_collision_time: `412.480`
- collision_pair: `[0, 8]`
- frames_scanned: `25`
- dt: `0.02`

## 复现

在上级目录执行：

```bash
python 第二问_优化可视化展示.py
```
