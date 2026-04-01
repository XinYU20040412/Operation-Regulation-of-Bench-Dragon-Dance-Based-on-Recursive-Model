# -*- coding: utf-8 -*-
"""
第二问优化版 + 高级可视化展示
--------------------------------
目标：
1) 在不改变题目物理建模逻辑的前提下，优化碰撞检测流程；
2) 一次运行直接输出：关键结果 + 高质量静态图 + 动画 GIF；
3) 方便 GitHub README 直接展示。

相较原版主要优化：
- 只计算碰撞检测所需的前若干节，避免全链条重复计算；
- AABB 粗筛 + SAT 精判，降低矩形相交判定开销；
- 统一缓存与结构化输出，便于复现实验和展示；
- 自动生成 GitHub 首页 README 与各子目录 README，便于直接推仓展示。
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import textwrap
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib

# 兼容本地/服务器/CI 环境，避免无显示设备时报错。
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation
from matplotlib.colors import LinearSegmentedColormap
from scipy.optimize import root_scalar


@dataclass
class Config:
    # 模型参数
    pitch: float = 0.55
    head_hole_distance: float = 0.01 * (341 - 2 * 27.5)
    body_hole_distance: float = 0.01 * (220 - 2 * 27.5)

    # 时间扫描区间（与原版第二问一致）
    t_start: float = 412.0
    t_end: float = 414.0
    dt: float = 0.02

    # 检测与可视化规模
    front_check: int = 50
    max_offset: int = 50
    handles_for_collision: int = 104
    handles_for_visual: int = 140
    handles_for_dashboard: int = 90

    # 几何参数
    board_width: float = 0.30

    # 输出
    output_dir: str = "viz_output"
    gif_fps: int = 8
    max_gif_frames: int = 80
    bg_points: int = 2000

    # GitHub 展示与文档自动化
    project_root: str = ""
    generate_root_readme: bool = True
    generate_subfolder_docs: bool = True
    overwrite_docs: bool = True


class DragonCollisionVisualizer:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.pi = math.pi
        self.k = cfg.pitch / (2 * self.pi)
        self.C = 0.5 * self.k * self.k * math.log(self.k)
        self.rA = self.k * (32 * self.pi)
        self.tA = (self._spiral_integral(self.rA) - self.C) / self.k

        self._head_cache: Dict[float, Tuple[float, float]] = {}
        self._handles_cache: Dict[Tuple[float, int], np.ndarray] = {}
        self._bg_xy = self._build_spiral_background()
        self._board_ratio_head = (341 - 27.5) / (341 - 55)
        self._board_ratio_body = (220 - 27.5) / (220 - 55)

    def _build_spiral_background(self) -> Tuple[np.ndarray, np.ndarray]:
        th_bg = np.linspace(0.0, 32.0 * self.pi, self.cfg.bg_points)
        r_bg = self._r_from_theta(th_bg)
        xb = r_bg * np.cos(th_bg)
        yb = r_bg * np.sin(th_bg)
        return xb, yb

    # -----------------------------
    # 基础几何与方程
    # -----------------------------
    def _spiral_integral(self, r: float) -> float:
        return 0.5 * (r * math.sqrt(r * r + self.k * self.k) + self.k * self.k * math.log(r + math.sqrt(r * r + self.k * self.k)))

    def _theta_from_r(self, r: float) -> float:
        return r / self.k

    def _r_from_theta(self, theta: float) -> float:
        return self.k * theta

    def _xy_from_theta(self, theta: float) -> Tuple[float, float]:
        r = self._r_from_theta(theta)
        return r * math.cos(theta), r * math.sin(theta)

    def _theta_from_xy(self, x: float, y: float) -> float:
        r = math.hypot(x, y)
        return 2 * self.pi * (r / self.cfg.pitch)

    def _head_radius_at_time(self, t: float) -> float:
        # 与原脚本 p_(t, i) 对齐：T = tA - t
        T = self.tA - t
        target = self.k * T + self.C

        def f(r: float) -> float:
            return self._spiral_integral(r) - target

        # 半径在 (0, rA] 上单调可解
        sol = root_scalar(f, bracket=[1e-9, self.rA], method="brentq")
        if not sol.converged:
            raise RuntimeError(f"head radius solve failed at t={t:.4f}")
        return float(sol.root)

    def head_xy(self, t: float) -> Tuple[float, float]:
        key = round(float(t), 6)
        if key in self._head_cache:
            return self._head_cache[key]

        r = self._head_radius_at_time(t)
        th = self._theta_from_r(r)
        x, y = r * math.cos(th), r * math.sin(th)
        self._head_cache[key] = (x, y)
        return x, y

    # -----------------------------
    # 把手递推（核心）
    # -----------------------------
    def _next_theta(self, theta_now: float, d: float) -> float:
        x0, y0 = self._xy_from_theta(theta_now)

        def g(delta: float) -> float:
            th2 = theta_now + delta
            x2, y2 = self._xy_from_theta(th2)
            return (x2 - x0) ** 2 + (y2 - y0) ** 2 - d * d

        lo = 1e-8
        hi = 0.6
        # 自动扩张区间直到跨过根
        while g(hi) < 0 and hi < 8.0:
            hi *= 1.6

        if g(hi) < 0:
            raise RuntimeError("failed to bracket delta_theta root")

        sol = root_scalar(g, bracket=[lo, hi], method="brentq")
        if not sol.converged:
            raise RuntimeError("delta_theta solve failed")
        return theta_now + float(sol.root)

    def compute_handles(self, t: float, n_handles: int) -> np.ndarray:
        key = (round(float(t), 6), int(n_handles))
        if key in self._handles_cache:
            return self._handles_cache[key]

        hx, hy = self.head_xy(t)
        th = self._theta_from_xy(hx, hy)

        pts = [(hx, hy)]
        th_now = th
        for i in range(1, n_handles):
            d = self.cfg.head_hole_distance if i == 1 else self.cfg.body_hole_distance
            th_next = self._next_theta(th_now, d)
            pts.append(self._xy_from_theta(th_next))
            th_now = th_next

        arr = np.asarray(pts, dtype=float)
        self._handles_cache[key] = arr
        return arr

    # -----------------------------
    # 板凳矩形 + 碰撞判定（AABB + SAT）
    # -----------------------------
    def _board_ratio(self, i: int) -> float:
        if i == 0:
            return self._board_ratio_head
        return self._board_ratio_body

    def segment_polygon(self, p0: np.ndarray, p1: np.ndarray, i: int) -> np.ndarray:
        ratio = self._board_ratio(i)
        a = p1 - ratio * (p1 - p0)
        b = p0 + ratio * (p1 - p0)

        d = b - a
        n = np.array([-d[1], d[0]], dtype=float)
        n_norm = np.linalg.norm(n)
        if n_norm < 1e-12:
            n = np.array([0.0, 1.0], dtype=float)
            n_norm = 1.0
        n /= n_norm

        off = 0.5 * self.cfg.board_width * n
        poly = np.array([
            a + off,
            b + off,
            b - off,
            a - off,
        ])
        return poly

    @staticmethod
    def _aabb(poly: np.ndarray) -> Tuple[float, float, float, float]:
        x = poly[:, 0]
        y = poly[:, 1]
        return float(x.min()), float(y.min()), float(x.max()), float(y.max())

    @staticmethod
    def _aabb_overlap(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]) -> bool:
        return (a[0] <= b[2]) and (a[2] >= b[0]) and (a[1] <= b[3]) and (a[3] >= b[1])

    @staticmethod
    def _sat_overlap(poly1: np.ndarray, poly2: np.ndarray) -> bool:
        def axes(poly: np.ndarray) -> List[np.ndarray]:
            out = []
            for i in range(len(poly)):
                p = poly[i]
                q = poly[(i + 1) % len(poly)]
                edge = q - p
                axis = np.array([-edge[1], edge[0]], dtype=float)
                n = np.linalg.norm(axis)
                if n > 1e-12:
                    out.append(axis / n)
            return out

        for axis in axes(poly1) + axes(poly2):
            p1 = poly1 @ axis
            p2 = poly2 @ axis
            if p1.max() < p2.min() or p2.max() < p1.min():
                return False
        return True

    def build_segments(self, handles: np.ndarray, n_segments: int) -> List[np.ndarray]:
        n_segments = min(n_segments, len(handles) - 1)
        segs = []
        for i in range(n_segments):
            segs.append(self.segment_polygon(handles[i], handles[i + 1], i))
        return segs

    def detect_collision(self, segments: List[np.ndarray]) -> Tuple[bool, Optional[Tuple[int, int]]]:
        aabbs = [self._aabb(p) for p in segments]
        max_i = min(self.cfg.front_check, len(segments) - 1)

        for i in range(max_i + 1):
            for offset in range(2, self.cfg.max_offset + 1):
                j = i + offset
                if j >= len(segments):
                    break
                if not self._aabb_overlap(aabbs[i], aabbs[j]):
                    continue
                if self._sat_overlap(segments[i], segments[j]):
                    return True, (i, j)
        return False, None

    # -----------------------------
    # 指标与可视化
    # -----------------------------
    @staticmethod
    def min_nonadjacent_center_distance(handles: np.ndarray) -> float:
        centers = 0.5 * (handles[:-1] + handles[1:])
        n = len(centers)
        if n < 3:
            return float("inf")

        # 只考虑非相邻板凳中心距离：j >= i + 2
        diff = centers[:, None, :] - centers[None, :, :]
        dist = np.sqrt(np.einsum("ijk,ijk->ij", diff, diff))
        mask = np.triu(np.ones((n, n), dtype=bool), k=2)
        return float(np.min(dist[mask])) if np.any(mask) else float("inf")

    def _draw_scene(self, ax: plt.Axes, state: Dict, n_draw_segments: int = 60) -> None:
        t = state["t"]
        handles = state["handles"]
        hit = state["hit"]
        pair = state["pair"]

        ax.set_facecolor("#0b1220")

        xb, yb = self._bg_xy
        ax.plot(xb, yb, color="#334155", linewidth=1.0, alpha=0.50)

        # 主轨迹 + 发光层
        ax.plot(handles[:, 0], handles[:, 1], color="#38bdf8", linewidth=2.6, alpha=0.20)
        ax.plot(handles[:, 0], handles[:, 1], color="#38bdf8", linewidth=1.2, alpha=0.95)

        # 龙头
        ax.scatter(handles[0, 0], handles[0, 1], s=48, c="#f43f5e", edgecolors="white", linewidths=0.8, zorder=5)

        # 板凳矩形
        segs = state.get("draw_segments")
        if segs is None:
            segs = self.build_segments(handles, n_draw_segments)
        for i, poly in enumerate(segs):
            fc = "#22c55e"
            ec = "#4ade80"
            alpha = 0.09
            if hit and pair is not None and i in pair:
                fc = "#ef4444"
                ec = "#fca5a5"
                alpha = 0.50

            patch = plt.Polygon(poly, closed=True, facecolor=fc, edgecolor=ec, linewidth=0.6, alpha=alpha)
            ax.add_patch(patch)

        # 信息面板
        msg = [
            f"t = {t:.2f} s",
            f"min clearance ≈ {state['clearance']:.4f} m",
            f"collision = {'YES' if hit else 'NO'}",
        ]
        if hit and pair is not None:
            msg.append(f"pair = ({pair[0]}, {pair[1]})")

        ax.text(
            0.02,
            0.98,
            "\n".join(msg),
            transform=ax.transAxes,
            va="top",
            ha="left",
            fontsize=10,
            color="#e2e8f0",
            bbox=dict(facecolor="#0f172a", edgecolor="#334155", boxstyle="round,pad=0.4", alpha=0.85),
        )

        ax.set_title("Dragon Collision Search (Optimized Visual)", color="#e2e8f0", fontsize=13, pad=10)
        ax.grid(color="#334155", linestyle="--", linewidth=0.6, alpha=0.35)
        ax.set_aspect("equal", adjustable="box")

        # 自动边界
        pad = 0.8
        xmin, xmax = handles[:, 0].min() - pad, handles[:, 0].max() + pad
        ymin, ymax = handles[:, 1].min() - pad, handles[:, 1].max() + pad
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)

        for spine in ax.spines.values():
            spine.set_color("#334155")
        ax.tick_params(colors="#cbd5e1")

    def scan(self) -> List[Dict]:
        times = np.arange(self.cfg.t_start, self.cfg.t_end + 1e-12, self.cfg.dt)
        states: List[Dict] = []

        for t in times:
            handles = self.compute_handles(float(t), self.cfg.handles_for_visual)

            segs = self.build_segments(handles[: self.cfg.handles_for_collision], self.cfg.handles_for_collision - 1)
            hit, pair = self.detect_collision(segs)

            clearance = self.min_nonadjacent_center_distance(handles[: self.cfg.handles_for_collision])
            states.append(
                {
                    "t": float(t),
                    "handles": handles,
                    "hit": bool(hit),
                    "pair": pair,
                    "clearance": float(clearance),
                }
            )

            if hit:
                break

        return states

    def _export_metrics_csv(self, states: List[Dict]) -> str:
        csv_path = os.path.join(self.cfg.output_dir, "collision_metrics.csv")
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "frame",
                "t",
                "clearance",
                "hit",
                "pair_i",
                "pair_j",
                "head_x",
                "head_y",
            ])
            for idx, state in enumerate(states):
                pair_i, pair_j = (state["pair"] if state["pair"] is not None else ("", ""))
                writer.writerow([
                    idx,
                    f"{state['t']:.6f}",
                    f"{state['clearance']:.8f}",
                    int(state["hit"]),
                    pair_i,
                    pair_j,
                    f"{state['handles'][0, 0]:.8f}",
                    f"{state['handles'][0, 1]:.8f}",
                ])
        return csv_path

    def _export_cover_poster(self, states: List[Dict], summary: Dict, frame_png: str) -> str:
        cover_png = os.path.join(self.cfg.output_dir, "collision_cover.png")

        fig = plt.figure(figsize=(13, 7.2), dpi=180)
        ax_bg = fig.add_axes([0.0, 0.0, 1.0, 1.0])
        ax_bg.axis("off")

        w, h = 1200, 720
        x = np.linspace(0.0, 1.0, w)
        y = np.linspace(0.0, 1.0, h)
        xx, yy = np.meshgrid(x, y)
        grad = 0.45 * yy + 0.35 * xx + 0.20 * np.exp(-((xx - 0.22) ** 2 + (yy - 0.70) ** 2) / 0.05)
        cmap = LinearSegmentedColormap.from_list("hero", ["#020617", "#0f172a", "#082f49", "#14532d"])
        ax_bg.imshow(grad, cmap=cmap, origin="lower", extent=(0, 1, 0, 1), interpolation="bicubic")

        fig.text(0.06, 0.86, "Dragon Collision", color="#e2e8f0", fontsize=38, weight="bold")
        fig.text(0.06, 0.79, "Optimized Search & Visual Pipeline", color="#7dd3fc", fontsize=20, weight="semibold")

        first_hit = summary.get("first_collision_time")
        pair = summary.get("collision_pair")
        min_clearance = min(float(s["clearance"]) for s in states)

        metrics_lines = [
            f"Scan window : [{self.cfg.t_start:.2f}, {self.cfg.t_end:.2f}] s",
            f"Step dt     : {self.cfg.dt:.3f} s",
            f"Frames      : {summary.get('frames_scanned', len(states))}",
            f"Min clearance: {min_clearance:.4f} m",
        ]
        if first_hit is not None:
            metrics_lines.append(f"First collision: t = {first_hit:.3f} s")
        else:
            metrics_lines.append("First collision: not found in scan range")
        if pair is not None:
            metrics_lines.append(f"Collision pair: ({pair[0]}, {pair[1]})")

        fig.text(
            0.06,
            0.58,
            "\n".join(metrics_lines),
            color="#cbd5e1",
            fontsize=14,
            family="monospace",
            linespacing=1.45,
            bbox=dict(facecolor="#0b1220", edgecolor="#334155", boxstyle="round,pad=0.7", alpha=0.75),
        )

        fig.text(0.06, 0.14, "Generated by optimized visualization script", color="#94a3b8", fontsize=11)

        ax_img = fig.add_axes([0.50, 0.10, 0.46, 0.82])
        ax_img.set_facecolor("#0b1220")
        ax_img.set_xticks([])
        ax_img.set_yticks([])
        for spine in ax_img.spines.values():
            spine.set_color("#38bdf8")
            spine.set_linewidth(1.2)

        try:
            img = plt.imread(frame_png)
            ax_img.imshow(img)
        except Exception:
            ax_img.text(0.5, 0.5, "collision_frame.png not found", ha="center", va="center", color="#e2e8f0", fontsize=14)

        fig.savefig(cover_png, bbox_inches="tight", pad_inches=0.12)
        plt.close(fig)
        return cover_png

    def _export_dashboard_html(self, states: List[Dict], summary: Dict) -> str:
        dashboard_path = os.path.join(self.cfg.output_dir, "collision_dashboard.html")

        payload = {
            "frames": [
                {
                    "t": float(s["t"]),
                    "clearance": float(s["clearance"]),
                    "hit": bool(s["hit"]),
                    "pair": (list(s["pair"]) if s["pair"] is not None else None),
                    "handles": np.round(s["handles"][: self.cfg.handles_for_dashboard], 6).tolist(),
                }
                for s in states
            ],
            "summary": {
                "scan_range": summary.get("scan_range"),
                "dt": summary.get("dt"),
                "frames_scanned": summary.get("frames_scanned"),
                "collision_found": summary.get("collision_found"),
                "first_collision_time": summary.get("first_collision_time"),
                "collision_pair": summary.get("collision_pair"),
            },
        }
        payload_json = json.dumps(payload, ensure_ascii=False)

        html_template = """<!doctype html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Dragon Collision Dashboard</title>
    <style>
        :root {
            --bg: #030712;
            --card: rgba(15, 23, 42, 0.72);
            --line: #38bdf8;
            --accent: #ef4444;
            --text: #e2e8f0;
            --muted: #94a3b8;
            --border: #334155;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            color: var(--text);
            background:
                radial-gradient(circle at 20% 16%, #12315c 0%, transparent 38%),
                radial-gradient(circle at 88% 24%, #0f5132 0%, transparent 32%),
                linear-gradient(160deg, #020617 0%, #0f172a 48%, #111827 100%);
            font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
            min-height: 100vh;
            padding: 28px;
        }
        .hero {
            max-width: 1200px;
            margin: 0 auto 18px auto;
            padding: 22px 24px;
            border: 1px solid var(--border);
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.86), rgba(8, 47, 73, 0.68));
            backdrop-filter: blur(10px);
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.32);
        }
        .hero h1 {
            margin: 0;
            font-size: 30px;
            line-height: 1.2;
            letter-spacing: 0.4px;
        }
        .hero p {
            margin: 8px 0 0 0;
            color: var(--muted);
            font-size: 15px;
        }
        .chips {
            margin-top: 14px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .chip {
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 13px;
            border: 1px solid var(--border);
            background: rgba(15, 23, 42, 0.80);
            color: #cbd5e1;
        }
        .layout {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1.35fr 1fr;
            gap: 16px;
        }
        .card {
            border: 1px solid var(--border);
            background: var(--card);
            border-radius: 16px;
            padding: 14px;
            box-shadow: 0 10px 28px rgba(0, 0, 0, 0.30);
            backdrop-filter: blur(8px);
        }
        h2 {
            margin: 2px 0 10px 0;
            font-size: 16px;
            color: #cbd5e1;
            letter-spacing: 0.3px;
        }
        canvas {
            width: 100%;
            border-radius: 12px;
            border: 1px solid #1e293b;
            background: #070f1f;
            display: block;
        }
        .controls {
            margin-top: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        button {
            cursor: pointer;
            border: 1px solid #0284c7;
            color: #e0f2fe;
            background: linear-gradient(135deg, #0369a1, #0f766e);
            border-radius: 10px;
            font-weight: 600;
            padding: 7px 14px;
        }
        input[type="range"] {
            flex: 1;
            min-width: 220px;
        }
        #frameLabel {
            min-width: 170px;
            font-family: Consolas, monospace;
            color: #bfdbfe;
            font-size: 13px;
        }
        .metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 10px;
        }
        .metric {
            background: rgba(2, 6, 23, 0.78);
            border: 1px solid #1f2937;
            border-radius: 12px;
            padding: 10px;
        }
        .metric .k {
            font-size: 12px;
            color: var(--muted);
        }
        .metric .v {
            margin-top: 3px;
            font-size: 18px;
            font-weight: 700;
            color: #e2e8f0;
        }
        .hint {
            margin-top: 8px;
            color: #94a3b8;
            font-size: 12px;
            line-height: 1.45;
        }
        @media (max-width: 980px) {
            body { padding: 14px; }
            .hero h1 { font-size: 24px; }
            .layout { grid-template-columns: 1fr; }
            .metrics { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <section class="hero">
        <h1>Dragon Collision Dashboard</h1>
        <p>优化版第二问可视化产物：轨迹回放、时间线与关键指标联动展示。</p>
        <div class="chips" id="chips"></div>
    </section>

    <main class="layout">
        <section class="card">
            <h2>Trajectory Replay</h2>
            <canvas id="sceneCanvas" width="920" height="620"></canvas>
            <div class="controls">
                <button id="playBtn" type="button">播放</button>
                <input id="frameSlider" type="range" min="0" max="0" value="0" step="1" />
                <span id="frameLabel">frame 0</span>
            </div>
        </section>

        <section class="card">
            <h2>Metrics Timeline</h2>
            <div class="metrics" id="metricCards"></div>
            <canvas id="timelineCanvas" width="820" height="300"></canvas>
            <div class="hint">
                使用滑块查看不同时刻轨迹，时间线红线对应首次碰撞帧（若存在）。
            </div>
        </section>
    </main>

    <script>
        const payload = __PAYLOAD__;
        const frames = payload.frames || [];
        const summary = payload.summary || {};

        const sceneCanvas = document.getElementById("sceneCanvas");
        const timelineCanvas = document.getElementById("timelineCanvas");
        const slider = document.getElementById("frameSlider");
        const label = document.getElementById("frameLabel");
        const playBtn = document.getElementById("playBtn");
        const chips = document.getElementById("chips");
        const metricCards = document.getElementById("metricCards");

        slider.max = Math.max(frames.length - 1, 0);

        const clearances = frames.map((f) => f.clearance);
        const times = frames.map((f) => f.t);
        const minClear = clearances.length ? Math.min(...clearances) : NaN;
        const firstHitIdx = frames.findIndex((f) => !!f.hit);

        function addChip(text) {
            const el = document.createElement("span");
            el.className = "chip";
            el.textContent = text;
            chips.appendChild(el);
        }

        function addMetric(key, val) {
            const card = document.createElement("div");
            card.className = "metric";
            const k = document.createElement("div");
            k.className = "k";
            k.textContent = key;
            const v = document.createElement("div");
            v.className = "v";
            v.textContent = val;
            card.appendChild(k);
            card.appendChild(v);
            metricCards.appendChild(card);
        }

        addChip(`dt = ${Number(summary.dt ?? 0).toFixed(3)} s`);
        addChip(`frames = ${summary.frames_scanned ?? frames.length}`);
        addChip(`collision = ${summary.collision_found ? "YES" : "NO"}`);
        addMetric("Minimum Clearance", Number.isFinite(minClear) ? `${minClear.toFixed(4)} m` : "-" );
        addMetric("First Collision Time", Number.isFinite(summary.first_collision_time) ? `${summary.first_collision_time.toFixed(3)} s` : "None");
        addMetric("Collision Pair", Array.isArray(summary.collision_pair) ? `(${summary.collision_pair[0]}, ${summary.collision_pair[1]})` : "None");
        addMetric("Scan Range", Array.isArray(summary.scan_range) ? `${summary.scan_range[0]} ~ ${summary.scan_range[1]} s` : "-" );

        function computeBounds() {
            let xmin = Infinity;
            let ymin = Infinity;
            let xmax = -Infinity;
            let ymax = -Infinity;
            for (const frame of frames) {
                for (const p of frame.handles) {
                    if (p[0] < xmin) xmin = p[0];
                    if (p[0] > xmax) xmax = p[0];
                    if (p[1] < ymin) ymin = p[1];
                    if (p[1] > ymax) ymax = p[1];
                }
            }
            if (!Number.isFinite(xmin)) {
                xmin = -1; ymin = -1; xmax = 1; ymax = 1;
            }
            return { xmin, ymin, xmax, ymax };
        }

        const bounds = computeBounds();

        function mapToCanvas(x, y) {
            const pad = 40;
            const width = sceneCanvas.width - 2 * pad;
            const height = sceneCanvas.height - 2 * pad;
            const sx = width / Math.max(bounds.xmax - bounds.xmin, 1e-9);
            const sy = height / Math.max(bounds.ymax - bounds.ymin, 1e-9);
            const s = Math.min(sx, sy);
            const ox = pad + 0.5 * (width - s * (bounds.xmax - bounds.xmin));
            const oy = pad + 0.5 * (height - s * (bounds.ymax - bounds.ymin));
            return [
                ox + s * (x - bounds.xmin),
                sceneCanvas.height - (oy + s * (y - bounds.ymin)),
            ];
        }

        function drawScene(frameIndex) {
            const frame = frames[frameIndex];
            if (!frame) return;

            const ctx = sceneCanvas.getContext("2d");
            ctx.clearRect(0, 0, sceneCanvas.width, sceneCanvas.height);

            const bg = ctx.createLinearGradient(0, 0, sceneCanvas.width, sceneCanvas.height);
            bg.addColorStop(0, "#020617");
            bg.addColorStop(1, "#082f49");
            ctx.fillStyle = bg;
            ctx.fillRect(0, 0, sceneCanvas.width, sceneCanvas.height);

            ctx.strokeStyle = "rgba(148, 163, 184, 0.20)";
            ctx.lineWidth = 1;
            for (let i = 1; i < 12; i += 1) {
                const x = (sceneCanvas.width * i) / 12;
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, sceneCanvas.height);
                ctx.stroke();
            }
            for (let j = 1; j < 8; j += 1) {
                const y = (sceneCanvas.height * j) / 8;
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(sceneCanvas.width, y);
                ctx.stroke();
            }

            const handles = frame.handles;
            ctx.beginPath();
            handles.forEach((p, i) => {
                const [cx, cy] = mapToCanvas(p[0], p[1]);
                if (i === 0) ctx.moveTo(cx, cy);
                else ctx.lineTo(cx, cy);
            });
            ctx.strokeStyle = "rgba(56, 189, 248, 0.88)";
            ctx.lineWidth = 2.2;
            ctx.shadowColor = "rgba(56, 189, 248, 0.60)";
            ctx.shadowBlur = 8;
            ctx.stroke();
            ctx.shadowBlur = 0;

            const [hx, hy] = mapToCanvas(handles[0][0], handles[0][1]);
            ctx.beginPath();
            ctx.arc(hx, hy, 6.2, 0, Math.PI * 2);
            ctx.fillStyle = "#f43f5e";
            ctx.fill();
            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = 1.2;
            ctx.stroke();

            if (Array.isArray(frame.pair)) {
                for (const idx of frame.pair) {
                    if (idx >= 0 && idx + 1 < handles.length) {
                        const p0 = mapToCanvas(handles[idx][0], handles[idx][1]);
                        const p1 = mapToCanvas(handles[idx + 1][0], handles[idx + 1][1]);
                        ctx.beginPath();
                        ctx.moveTo(p0[0], p0[1]);
                        ctx.lineTo(p1[0], p1[1]);
                        ctx.strokeStyle = "#ef4444";
                        ctx.lineWidth = 4;
                        ctx.stroke();
                    }
                }
            }

            ctx.fillStyle = "rgba(2, 6, 23, 0.72)";
            ctx.fillRect(14, 14, 248, 88);
            ctx.strokeStyle = "rgba(148, 163, 184, 0.35)";
            ctx.strokeRect(14, 14, 248, 88);
            ctx.fillStyle = "#e2e8f0";
            ctx.font = "13px Consolas, monospace";
            ctx.fillText(`t = ${frame.t.toFixed(3)} s`, 24, 40);
            ctx.fillText(`clearance = ${frame.clearance.toFixed(4)} m`, 24, 62);
            ctx.fillText(`collision = ${frame.hit ? "YES" : "NO"}`, 24, 84);
        }

        function drawTimeline(currentIdx) {
            const ctx = timelineCanvas.getContext("2d");
            const W = timelineCanvas.width;
            const H = timelineCanvas.height;
            ctx.clearRect(0, 0, W, H);

            const bg = ctx.createLinearGradient(0, 0, W, H);
            bg.addColorStop(0, "#020617");
            bg.addColorStop(1, "#111827");
            ctx.fillStyle = bg;
            ctx.fillRect(0, 0, W, H);

            if (!frames.length) return;

            const margin = { l: 52, r: 20, t: 20, b: 38 };
            const minX = times[0];
            const maxX = times[times.length - 1];
            const minY = Math.min(...clearances);
            const maxY = Math.max(...clearances);

            const px = (x) => margin.l + ((x - minX) / Math.max(maxX - minX, 1e-9)) * (W - margin.l - margin.r);
            const py = (y) => H - margin.b - ((y - minY) / Math.max(maxY - minY, 1e-9)) * (H - margin.t - margin.b);

            ctx.strokeStyle = "rgba(148, 163, 184, 0.28)";
            ctx.lineWidth = 1;
            for (let i = 0; i <= 4; i += 1) {
                const yy = margin.t + ((H - margin.t - margin.b) * i) / 4;
                ctx.beginPath();
                ctx.moveTo(margin.l, yy);
                ctx.lineTo(W - margin.r, yy);
                ctx.stroke();
            }

            ctx.beginPath();
            clearances.forEach((y, i) => {
                const x = times[i];
                const cx = px(x);
                const cy = py(y);
                if (i === 0) ctx.moveTo(cx, cy);
                else ctx.lineTo(cx, cy);
            });
            ctx.strokeStyle = "#38bdf8";
            ctx.lineWidth = 2;
            ctx.stroke();

            if (firstHitIdx >= 0) {
                const hitX = px(times[firstHitIdx]);
                ctx.beginPath();
                ctx.moveTo(hitX, margin.t);
                ctx.lineTo(hitX, H - margin.b);
                ctx.strokeStyle = "#ef4444";
                ctx.lineWidth = 1.5;
                ctx.setLineDash([6, 5]);
                ctx.stroke();
                ctx.setLineDash([]);
            }

            const markerX = px(times[currentIdx]);
            const markerY = py(clearances[currentIdx]);
            ctx.beginPath();
            ctx.arc(markerX, markerY, 4.5, 0, Math.PI * 2);
            ctx.fillStyle = "#f8fafc";
            ctx.fill();
            ctx.strokeStyle = "#38bdf8";
            ctx.lineWidth = 2;
            ctx.stroke();

            ctx.fillStyle = "#cbd5e1";
            ctx.font = "12px Consolas, monospace";
            ctx.fillText(`t: ${times[currentIdx].toFixed(3)} s`, margin.l + 4, H - 12);
            ctx.fillText(`clearance: ${clearances[currentIdx].toFixed(4)} m`, margin.l + 130, H - 12);
        }

        function render(frameIndex) {
            if (!frames.length) return;
            const idx = Math.max(0, Math.min(frames.length - 1, frameIndex));
            slider.value = idx;
            drawScene(idx);
            drawTimeline(idx);
            label.textContent = `frame ${idx + 1}/${frames.length} | t=${frames[idx].t.toFixed(3)} s`;
        }

        slider.addEventListener("input", (e) => {
            render(Number(e.target.value));
        });

        let timer = null;
        playBtn.addEventListener("click", () => {
            if (!frames.length) return;
            if (timer) {
                clearInterval(timer);
                timer = null;
                playBtn.textContent = "播放";
                return;
            }

            playBtn.textContent = "暂停";
            timer = setInterval(() => {
                let next = Number(slider.value) + 1;
                if (next >= frames.length) {
                    next = 0;
                }
                render(next);
            }, 220);
        });

        render(0);
    </script>
</body>
</html>
"""
        html = html_template.replace("__PAYLOAD__", payload_json)
        with open(dashboard_path, "w", encoding="utf-8") as f:
            f.write(html)
        return dashboard_path

    def _project_root(self) -> Path:
        if self.cfg.project_root:
            return Path(self.cfg.project_root).resolve()
        return Path(self.cfg.output_dir).resolve().parent

    def _output_relative_path(self, target_name: str) -> str:
        root = self._project_root()
        out_dir = Path(self.cfg.output_dir).resolve()
        target = out_dir / target_name
        try:
            rel = target.relative_to(root)
        except ValueError:
            rel = Path(target_name)
        return rel.as_posix()

    def _render_root_readme(self, summary: Dict) -> str:
        files = summary["output_files"]
        cover = self._output_relative_path(files["cover_png"])
        gif = self._output_relative_path(files["gif"])
        timeline = self._output_relative_path(files["timeline_png"])
        frame = self._output_relative_path(files["frame_png"])
        dashboard = self._output_relative_path(files["dashboard_html"])
        csv_path = self._output_relative_path(files["metrics_csv"])

        first_hit = summary.get("first_collision_time")
        pair = summary.get("collision_pair")
        first_hit_text = "未在扫描区间内发现碰撞" if first_hit is None else f"{first_hit:.3f} s"
        pair_text = "None" if pair is None else f"({pair[0]}, {pair[1]})"

        return textwrap.dedent(
            f"""
            <div align=\"center\">

            # Dragon Collision Visualization

            一次运行，自动输出碰撞结论 + 高质量图像 + 动态回放 + 交互式 Dashboard。

            ![Python](https://img.shields.io/badge/Python-3.10+-0ea5e9?style=for-the-badge)
            ![Method](https://img.shields.io/badge/Method-AABB%2BSAT-14b8a6?style=for-the-badge)
            ![Collision](https://img.shields.io/badge/Collision-{str(summary.get('collision_found', False)).upper()}-ef4444?style=for-the-badge)

            </div>

            ![Cover]({cover})

            ## Highlights

            - 碰撞检测：AABB 粗筛 + SAT 精判，速度与准确性兼顾。
            - 展示输出：封面海报、时间线、关键帧、GIF、Dashboard 一次导出。
            - GitHub 友好：推送仓库后主页可直接展示核心结果。

            ## Quick Start

            ```bash
            python 第二问_优化可视化展示.py
            ```

            ## Core Results

            - 首次碰撞时间：{first_hit_text}
            - 碰撞板凳对：{pair_text}
            - 扫描帧数：{summary.get('frames_scanned', '-')}
            - 时间步长 dt：{summary.get('dt', '-')}

            ## Gallery

            ### Process Animation
            ![Dragon Motion]({gif})

            ### Clearance Timeline
            ![Timeline]({timeline})

            ### Collision Key Frame
            ![Collision Frame]({frame})

            ## Interactive Dashboard

            - 本地文件：[{dashboard}]({dashboard})
            - 建议开启 GitHub Pages 后在线预览该 HTML。

            ## Data Outputs

            - 指标表 CSV：[{csv_path}]({csv_path})
            - 结构化摘要 JSON：[{self._output_relative_path('summary.json')}]({self._output_relative_path('summary.json')})
            """
        ).strip() + "\n"

    def _render_output_readme(self, summary: Dict) -> str:
        files = summary["output_files"]
        first_hit = summary.get("first_collision_time")
        first_hit_text = "None" if first_hit is None else f"{float(first_hit):.3f}"
        pair = summary.get("collision_pair")
        pair_text = "None" if pair is None else f"[{pair[0]}, {pair[1]}]"
        return textwrap.dedent(
            f"""
            # viz_output

            本目录存放第二问优化可视化脚本自动生成的结果文件。

            ## 文件说明

            - `{files['cover_png']}`：封面图，适合放在仓库 README 顶部。
            - `{files['gif']}`：碰撞过程 GIF 动画。
            - `{files['timeline_png']}`：最小安全间距时间线图。
            - `{files['frame_png']}`：首次碰撞关键帧（若无碰撞则为末帧）。
            - `{files['dashboard_html']}`：交互式可视化页面（滑块 + 回放）。
            - `{files['metrics_csv']}`：逐帧指标表。
            - `summary.json`：结构化运行摘要。

            ## 关键指标

            - collision_found: `{summary.get('collision_found', False)}`
            - first_collision_time: `{first_hit_text}`
            - collision_pair: `{pair_text}`
            - frames_scanned: `{summary.get('frames_scanned', '-')}`
            - dt: `{summary.get('dt', '-')}`

            ## 复现

            在上级目录执行：

            ```bash
            python 第二问_优化可视化展示.py
            ```
            """
        ).strip() + "\n"

    def _write_docs(self, summary: Dict) -> Dict[str, List[str]]:
        root = self._project_root()
        out_dir = Path(self.cfg.output_dir).resolve()
        created: List[str] = []
        skipped: List[str] = []

        if self.cfg.generate_root_readme:
            root_readme = root / "README.md"
            if self.cfg.overwrite_docs or not root_readme.exists():
                root_readme.write_text(self._render_root_readme(summary), encoding="utf-8")
                created.append(str(root_readme))
            else:
                skipped.append(str(root_readme))

        if self.cfg.generate_subfolder_docs:
            for subdir in sorted([p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")]):
                readme = subdir / "README.md"
                if not (self.cfg.overwrite_docs or not readme.exists()):
                    skipped.append(str(readme))
                    continue

                if subdir.resolve() == out_dir:
                    content = self._render_output_readme(summary)
                else:
                    content = textwrap.dedent(
                        f"""
                        # {subdir.name}

                        该目录为“{subdir.name}”模块。

                        ## 目录职责

                        - 存放与 `{subdir.name}` 相关的代码、数据或可视化产物。
                        - 建议在本文件中持续补充：输入输出定义、运行方式、参数说明。
                        """
                    ).strip() + "\n"

                readme.write_text(content, encoding="utf-8")
                created.append(str(readme))

        return {"created": created, "skipped": skipped}

    def export_visuals(self, states: List[Dict]) -> Dict:
        os.makedirs(self.cfg.output_dir, exist_ok=True)
        export_t0 = time.perf_counter()

        # 1) 时间-最小间距曲线
        t_vals = [s["t"] for s in states]
        c_vals = [s["clearance"] for s in states]
        hit_idx = next((i for i, s in enumerate(states) if s["hit"]), None)

        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(10, 4.5), dpi=160)
        fig.patch.set_facecolor("#0b1220")
        ax.set_facecolor("#0b1220")
        ax.plot(t_vals, c_vals, color="#38bdf8", linewidth=2.0)
        if hit_idx is not None:
            ax.axvline(t_vals[hit_idx], color="#ef4444", linestyle="--", linewidth=1.2, label="first collision")
            ax.scatter([t_vals[hit_idx]], [c_vals[hit_idx]], c="#ef4444", s=36)
        ax.set_title("Timeline of minimum non-adjacent clearance", color="#e2e8f0")
        ax.set_xlabel("time (s)", color="#cbd5e1")
        ax.set_ylabel("clearance (m)", color="#cbd5e1")
        ax.grid(color="#334155", linestyle="--", alpha=0.35)
        ax.tick_params(colors="#cbd5e1")
        if hit_idx is not None:
            ax.legend(facecolor="#0f172a", edgecolor="#334155")
        timeline_png = os.path.join(self.cfg.output_dir, "collision_timeline.png")
        fig.tight_layout()
        fig.savefig(timeline_png)
        plt.close(fig)
        timeline_elapsed = time.perf_counter() - export_t0

        # 2) 首次碰撞帧（或末帧）
        key_state = states[hit_idx] if hit_idx is not None else states[-1]
        fig, ax = plt.subplots(figsize=(8.4, 8.4), dpi=160)
        fig.patch.set_facecolor("#0b1220")
        self._draw_scene(ax, key_state)
        frame_png = os.path.join(self.cfg.output_dir, "collision_frame.png")
        fig.tight_layout()
        fig.savefig(frame_png)
        plt.close(fig)
        frame_elapsed = time.perf_counter() - export_t0 - timeline_elapsed

        # 3) 动画 GIF（采样避免体积过大）
        max_frames = max(1, int(self.cfg.max_gif_frames))
        if len(states) > max_frames:
            idx = np.linspace(0, len(states) - 1, max_frames).astype(int)
            anim_states = [states[i] for i in idx]
        else:
            anim_states = states

        fig, ax = plt.subplots(figsize=(7.2, 7.2), dpi=120)
        fig.patch.set_facecolor("#0b1220")

        def update(frame_id: int):
            ax.clear()
            self._draw_scene(ax, anim_states[frame_id])
            return []

        ani = animation.FuncAnimation(fig, update, frames=len(anim_states), interval=120, blit=False)
        gif_path = os.path.join(self.cfg.output_dir, "dragon_motion.gif")
        ani.save(gif_path, writer=animation.PillowWriter(fps=self.cfg.gif_fps))
        plt.close(fig)
        gif_elapsed = time.perf_counter() - export_t0 - timeline_elapsed - frame_elapsed

        # 4) 结果摘要
        summary = {
            "scan_range": [self.cfg.t_start, self.cfg.t_end],
            "dt": self.cfg.dt,
            "frames_scanned": len(states),
            "collision_found": hit_idx is not None,
            "first_collision_time": (t_vals[hit_idx] if hit_idx is not None else None),
            "collision_pair": (list(states[hit_idx]["pair"]) if hit_idx is not None and states[hit_idx]["pair"] is not None else None),
            "output_files": {
                "timeline_png": os.path.basename(timeline_png),
                "frame_png": os.path.basename(frame_png),
                "gif": os.path.basename(gif_path),
            },
        }

        metrics_csv = self._export_metrics_csv(states)
        cover_png = self._export_cover_poster(states, summary, frame_png)
        dashboard_html = self._export_dashboard_html(states, summary)
        summary["output_files"].update(
            {
                "cover_png": os.path.basename(cover_png),
                "dashboard_html": os.path.basename(dashboard_html),
                "metrics_csv": os.path.basename(metrics_csv),
            }
        )
        summary["timing_sec"] = {
            "timeline": round(timeline_elapsed, 4),
            "frame": round(frame_elapsed, 4),
            "gif": round(gif_elapsed, 4),
            "total_export": round(time.perf_counter() - export_t0, 4),
        }
        summary["cache_stats"] = {
            "head_cache_size": len(self._head_cache),
            "handles_cache_size": len(self._handles_cache),
        }

        summary_path = os.path.join(self.cfg.output_dir, "summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        docs_result = self._write_docs(summary)
        summary["docs"] = {
            "created": docs_result["created"],
            "skipped": docs_result["skipped"],
        }

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        return summary


def main():
    parser = argparse.ArgumentParser(description="第二问优化可视化脚本")
    parser.add_argument("--t-start", type=float, default=412.0, help="时间扫描起点")
    parser.add_argument("--t-end", type=float, default=414.0, help="时间扫描终点")
    parser.add_argument("--dt", type=float, default=0.02, help="时间步长")
    parser.add_argument("--gif-fps", type=int, default=8, help="GIF 帧率")
    parser.add_argument("--max-gif-frames", type=int, default=80, help="GIF 最大帧数")
    parser.add_argument("--output-dir", type=str, default="", help="输出目录，留空则写入脚本目录下的 viz_output")
    parser.add_argument("--no-root-readme", action="store_true", help="不生成根目录 README.md")
    parser.add_argument("--no-subfolder-docs", action="store_true", help="不为各子目录生成 README.md")
    parser.add_argument("--keep-existing-docs", action="store_true", help="已有 README.md 存在时不覆盖")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = args.output_dir if args.output_dir else os.path.join(base_dir, "viz_output")

    cfg = Config(
        t_start=float(args.t_start),
        t_end=float(args.t_end),
        dt=float(args.dt),
        gif_fps=int(args.gif_fps),
        max_gif_frames=max(1, int(args.max_gif_frames)),
        output_dir=out_dir,
        project_root=base_dir,
        generate_root_readme=not bool(args.no_root_readme),
        generate_subfolder_docs=not bool(args.no_subfolder_docs),
        overwrite_docs=not bool(args.keep_existing_docs),
    )
    solver = DragonCollisionVisualizer(cfg)

    print("[info] scanning time range ...")
    scan_t0 = time.perf_counter()
    states = solver.scan()
    scan_elapsed = time.perf_counter() - scan_t0
    summary = solver.export_visuals(states)
    summary.setdefault("timing_sec", {})
    summary["timing_sec"]["scan"] = round(scan_elapsed, 4)

    summary_path = os.path.join(cfg.output_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("[done] visualization generated")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
