"""scene01 开场:变色的散射光 — 绿激光照样品,散射出瑞利/斯托克斯/反斯托克斯三束光,1928 年故事引入.

Run:
    MANIM_LOW_RES=1 manim -pql main.py IntroScene    # 低清预览(画面审查用)
    manim -pqh main.py IntroScene                    # 1080p60 高清成片
"""

from __future__ import annotations

import os

import numpy as np
from manim import *  # noqa: F401,F403

# ---------- 分辨率/帧率(env-gate:MANIM_LOW_RES=1 时低清)----------
LOW_RES = os.environ.get("MANIM_LOW_RES", "0") == "1"
config.pixel_height = 480 if LOW_RES else 1080
config.pixel_width = 854 if LOW_RES else 1920
config.frame_rate = 15 if LOW_RES else 60

# ---------- 配色(必须与 spec_lock.md ## colors 一致)----------
BG_COLOR = "#282c34"
WHITE_ = "#ffffff"
COL_A = "#58b9ff"      # 反斯托克斯(蓝移)
COL_B = "#8be9fd"      # 辅助/样品
ACCENT = "#ffd866"     # 强调黄
ERR = "#ff6188"        # 斯托克斯(红移)
GREEN_A = "#a6e22e"    # 入射激光 532nm

FONT = "Times New Roman"
CJK_FONT = "SimSun"


class IntroScene(Scene):
    """开场:绿激光照样品,散射光里有三种颜色,引出拉曼发现的故事。"""

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR

        # ==== Phase 1: 标题 ====
        title_cn = Text("拉曼光谱", font=CJK_FONT, font_size=42, color=WHITE_)
        title_en = Text("Raman Spectroscopy", font=FONT, font_size=28, color=WHITE_).set_opacity(0.55)
        title = VGroup(title_cn, title_en).arrange(RIGHT, buff=0.4, aligned_edge=DOWN).to_edge(UP, buff=0.3)
        title.move_to([0, title_cn.get_y(), 0])  # to_edge(UP) 只改 Y,水平居中必须显式

        self.play(FadeIn(title_cn, shift=DOWN * 0.3), run_time=1.0)
        self.wait(0.4)
        self.play(FadeIn(title_en, shift=DOWN * 0.3), run_time=0.8)
        self.wait(0.8)

        # ==== Phase 2: 激光照样品 ====
        sample = (
            Square(side_length=0.9, color=COL_B, stroke_width=3)
            .shift(DOWN * 0.9 + RIGHT * 0.3)   # 预览注解:右移 0.3
            .scale(1.15)                        # 预览注解:放大
            .set_opacity(0.85)                  # 预览注解:深浅 0.85
        )
        sample_label = Text("样品", font=CJK_FONT, font_size=20, color=COL_B).next_to(sample, DOWN, buff=0.18)

        laser_start = sample.get_left() + LEFT * 3.0
        laser = Line(laser_start, sample.get_left(), color=GREEN_A, stroke_width=6)
        laser.add_tip(tip_length=0.22)
        laser_label = Text("532 nm 激光", font=CJK_FONT, font_size=20, color=GREEN_A).next_to(laser, UP, buff=0.2)
        spot = Dot(sample.get_right(), radius=0.08, color=GREEN_A, fill_opacity=0.9)  # 预览注解:入射点光斑

        self.play(FadeIn(sample, shift=UP * 0.2), FadeIn(sample_label), run_time=1.4)  # 预览注解:时长 1.4s
        self.play(Create(laser), run_time=1.0)  # GrowArrow 在 v0.19 有兼容坑,箭头用 Create
        self.play(ShowPassingFlash(laser.copy().set_color(WHITE_)), FadeIn(spot), run_time=0.9)
        self.wait(0.4)
        self.play(FadeIn(laser_label), run_time=0.6)
        self.wait(0.3)

        # ==== Phase 3: 三束散射光 ====
        right = sample.get_right()
        ray_rayleigh = Line(right, right + RIGHT * 2.8, color=WHITE_, stroke_width=8)
        ray_rayleigh.add_tip(tip_length=0.22)
        dir_stokes = np.array([np.cos(np.deg2rad(25)), np.sin(np.deg2rad(25)), 0.0])
        ray_stokes = Line(right, right + dir_stokes * 2.8, color=ERR, stroke_width=5)
        ray_stokes.add_tip(tip_length=0.2)
        dir_anti = np.array([np.cos(np.deg2rad(25)), -np.sin(np.deg2rad(25)), 0.0])
        ray_anti = Line(right, right + dir_anti * 2.8, color=COL_A, stroke_width=5)
        ray_anti.add_tip(tip_length=0.2)

        lab_rayleigh = Text("瑞利散射", font=CJK_FONT, font_size=20, color=WHITE_).next_to(ray_rayleigh, UP, buff=0.15)
        lab_stokes = Text("斯托克斯 · 红移", font=CJK_FONT, font_size=20, color=ERR).next_to(ray_stokes, UP, buff=0.15)
        lab_anti = Text("反斯托克斯 · 蓝移", font=CJK_FONT, font_size=20, color=COL_A).next_to(ray_anti, DOWN, buff=0.15)

        self.play(Create(ray_rayleigh), FadeIn(lab_rayleigh, shift=UP * 0.15), run_time=1.2)
        self.wait(0.4)
        self.play(Create(ray_stokes), FadeIn(lab_stokes, shift=UP * 0.15), run_time=1.2)
        self.wait(0.4)
        self.play(Create(ray_anti), FadeIn(lab_anti, shift=DOWN * 0.15), run_time=1.2)
        self.wait(0.5)

        # ==== Phase 4: 年份引言 ====
        note = Text(
            "1928 拉曼发现“变色的光” · 1930 诺贝尔物理学奖",
            font=CJK_FONT, font_size=20, color=WHITE_,
        ).set_opacity(0.75).to_edge(DOWN, buff=0.35)

        self.play(FadeIn(note, shift=UP * 0.2), run_time=1.2)
        self.wait(0.6)

        # 结尾留白(shot_table wait 预算内)
        self.wait(2.5)
