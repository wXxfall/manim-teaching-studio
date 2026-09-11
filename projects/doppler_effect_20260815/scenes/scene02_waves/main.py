"""scene02 波面图景:静止波源同心圆波面 vs 运动波源前方压缩/后方拉伸,波速不变.

Run:
    MANIM_LOW_RES=1 manim -pql main.py WavesScene     # 低清预览(画面审查用)
    manim -pqh main.py WavesScene                     # 1080p60 高清成片
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

# ---------- 配色(spec_lock ## colors,不得自造)----------
BG_COLOR = "#282c34"
WHITE_ = "#ffffff"
COL_A = "#58b9ff"
COL_B = "#8be9fd"
ACCENT = "#ffd866"
ERR = "#ff6188"
GREEN_A = "#a6e22e"

FONT = "Times New Roman"
CJK_FONT = "SimSun"

# 波面几何参数(物理参数集中,便于调节)
V_STATIC = 0.7          # 静止波源波面半径步长(示意单位)
V_MOVE = 0.7            # 运动波源波速(示意单位)
V_SRC = 0.2             # 运动波源速度(示意单位,每个周期前进量)
N_STATIC = 4            # 静止波面圈数
N_MOVE = 4              # 运动波面圈数
SRC_STATIC = np.array([-4.8, 2.0, 0.0])
SRC_MOVE_START = np.array([-2.0, -0.8, 0.0])
SRC_MOVE_END = np.array([0.0, -0.8, 0.0])


def make_waves(center: np.ndarray, n: int, dr: float, color) -> VGroup:
    """同心圆虚线波面组(示意用)。"""
    waves = VGroup()
    for i in range(1, n + 1):
        c = DashedVMobject(Circle(radius=dr * i, color=color, stroke_width=2), num_dashes=48)
        c.move_to(center).set_opacity(0.7)
        waves.add(c)
    return waves


def make_moving_pattern() -> VGroup:
    """运动波源某一时刻的波面:第 i 圈圆心在 v_s·i 处、半径 v·i(前方压缩/后方拉伸)。"""
    waves = VGroup()
    for i in range(1, N_MOVE + 1):
        center = SRC_MOVE_END - np.array([V_SRC * i, 0.0, 0.0])
        c = DashedVMobject(Circle(radius=V_MOVE * i, color=COL_A, stroke_width=2), num_dashes=48)
        c.move_to(center).set_opacity(0.75)
        waves.add(c)
    return waves


class WavesScene(Scene):
    """波面图景:相对运动改变"每秒接收的波数"的几何根源。"""

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR

        # ==== Phase 1: 静止波源(上方)====
        src0 = Dot(SRC_STATIC, radius=0.09, color=WHITE_).set_name("静止波源")
        lab0 = Text("波源静止 · 前后波长一样", font=CJK_FONT, font_size=18, color=WHITE_)
        lab0.next_to(src0, DOWN, buff=0.35).set_name("标注·静止")

        self.play(FadeIn(src0), run_time=0.8)
        self.wait(0.5)
        waves0 = make_waves(SRC_STATIC, N_STATIC, 0.45, COL_B).set_name("静止波面")
        self.play(LaggedStart(*[Create(c) for c in waves0], lag_ratio=0.6), run_time=2.2)
        self.wait(0.8)

        # λ 标注(右侧两圈之间)
        lam0_arr = DoubleArrow(SRC_STATIC + np.array([1.35, 0, 0]), SRC_STATIC + np.array([1.8, 0, 0]),
                               color=WHITE_, stroke_width=2, tip_length=0.12, max_tip_length_to_length_ratio=0.4)
        lam0_txt = MathTex(r"\lambda", color=WHITE_).scale(0.7)
        lam0_txt.next_to(lam0_arr, UP, buff=0.12).set_name("标注·波长")
        self.play(FadeIn(lam0_arr), FadeIn(lam0_txt), run_time=0.8)
        self.wait(0.8)
        self.play(FadeIn(lab0, shift=UP * 0.1), run_time=0.8)
        self.wait(0.8)

        # ==== Phase 2: 运动波源(下方)====
        src = Dot(SRC_MOVE_START, radius=0.09, color=COL_A).set_name("运动波源")
        varr = Arrow(SRC_MOVE_END + np.array([0.35, 0, 0]), SRC_MOVE_END + np.array([0.95, 0, 0]),
                     color=COL_A, stroke_width=3, tip_length=0.14, max_tip_length_to_length_ratio=0.3)
        vs_txt = MathTex(r"v_s", color=COL_A).scale(0.7)
        vs_txt.next_to(varr, UP, buff=0.12).set_name("标注·波源速度")

        self.play(FadeIn(src), run_time=0.8)
        self.wait(0.4)
        self.play(FadeIn(varr), FadeIn(vs_txt), run_time=0.6)
        self.wait(0.3)
        self.play(src.animate.move_to(SRC_MOVE_END), run_time=1.2)
        self.wait(0.4)

        waves_m = make_moving_pattern().set_name("运动波面")
        self.play(LaggedStart(*[Create(c) for c in waves_m], lag_ratio=0.5), run_time=2.6)
        self.wait(0.6)

        # ==== Phase 3: 波长标注 + 关键句 ====
        # 前方(右)交点间隔 = (v−v_s)·T = 0.5;后方(左)间隔 = (v+v_s)·T = 0.9
        lam_f_arr = DoubleArrow(np.array([1.55, -0.8, 0]), np.array([1.95, -0.8, 0]),
                                color=ERR, stroke_width=3, tip_length=0.12, max_tip_length_to_length_ratio=0.4)
        lam_f_txt = Text("λ′ 小", font=CJK_FONT, font_size=18, color=ERR)
        lam_f_txt.next_to(lam_f_arr, RIGHT, buff=0.15).set_name("标注·前方波长")
        lam_b_arr = DoubleArrow(np.array([-3.55, -0.8, 0]), np.array([-2.75, -0.8, 0]),
                                color=GREEN_A, stroke_width=3, tip_length=0.12, max_tip_length_to_length_ratio=0.4)
        lam_b_txt = Text("λ″ 大", font=CJK_FONT, font_size=18, color=GREEN_A)
        lam_b_txt.next_to(lam_b_arr, LEFT, buff=0.15).set_name("标注·后方波长")

        self.play(FadeIn(lam_f_arr), FadeIn(lam_f_txt), FadeIn(lam_b_arr), FadeIn(lam_b_txt), run_time=1.2)
        self.wait(0.8)

        key = Text(
            "波源动 → 前方波长被压缩(波密)、后方被拉伸(波疏);波速 v 不变,变的只是波长",
            font=CJK_FONT, font_size=20, color=ACCENT,
        ).to_edge(DOWN, buff=0.2).set_name("关键句")
        self.play(FadeIn(key, shift=UP * 0.15), run_time=1.2)
        self.wait(1.2)

        # 结尾留白(shot_table wait 预算内)
        self.wait(3.0)
