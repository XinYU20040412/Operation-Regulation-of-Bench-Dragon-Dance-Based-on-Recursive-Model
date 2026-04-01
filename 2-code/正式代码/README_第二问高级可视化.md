# 第二问优化版：高级可视化展示

这个版本面向 GitHub 项目展示，目标是做到“运行一次，展示齐全”：
- 算法端：AABB 粗筛 + SAT 精判，减少无效碰撞计算；
- 可视化端：封面海报 + 时间线 + 关键帧 + GIF 动画；
- 展示端：自动生成交互式 Dashboard HTML 与结构化 JSON/CSV。

## 1. 快速运行

```bash
python 第二问_优化可视化展示.py
```

## 2. 输出文件（viz_output/）

- `collision_cover.png`：封面级海报图（适合 README 顶部）
- `dragon_motion.gif`：运动过程动画
- `collision_timeline.png`：最小安全间距时间线
- `collision_frame.png`：首次碰撞（或末帧）关键画面
- `collision_dashboard.html`：交互式仪表盘（滑块 + 回放 + 时间线联动）
- `collision_metrics.csv`：逐帧指标表（可用于论文表格/二次分析）
- `summary.json`：结构化摘要（碰撞时刻、碰撞对、扫描区间等）

## 3. 高级展示模板（直接复制到仓库 README）

```markdown
## Dragon Collision Visualization (Optimized)

![cover](2-code/正式代码/viz_output/collision_cover.png)

> 从几何建模到视觉展示一体化输出：可复现、可解释、可演示。

![badge-python](https://img.shields.io/badge/Python-3.10+-0ea5e9?style=for-the-badge)
![badge-status](https://img.shields.io/badge/Collision-Detected-ef4444?style=for-the-badge)
![badge-method](https://img.shields.io/badge/Method-AABB%2BSAT-14b8a6?style=for-the-badge)

### Process Animation
![Dragon Motion](2-code/正式代码/viz_output/dragon_motion.gif)

### Timeline
![Timeline](2-code/正式代码/viz_output/collision_timeline.png)

### Key Collision Frame
![Collision Frame](2-code/正式代码/viz_output/collision_frame.png)

### Interactive Dashboard
- Local file: `2-code/正式代码/viz_output/collision_dashboard.html`
- 建议配合 GitHub Pages 发布后在线查看。
```

## 4. 交互式 Dashboard 使用说明

- 双击打开 `viz_output/collision_dashboard.html`
- 通过滑块切换帧，查看不同时刻龙身几何状态
- 点击播放按钮自动回放
- 时间线红色虚线对应首次碰撞时刻

## 5. 可写进项目亮点的表述

- “碰撞检测采用 AABB 粗筛 + SAT 精判，兼顾速度与精度。”
- “求解结果、动态图、关键帧、海报图和指标表一次性自动导出。”
- “支持交互式 Dashboard，便于答辩时逐帧解释碰撞形成过程。”
