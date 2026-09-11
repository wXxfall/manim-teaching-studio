"""scene02 能级图:三种散射 — 虚态虚线,瑞利/斯托克斯/反斯托克斯三支箭头,能量守恒 hν' = hν₀ ± hν_vib.

Run:
    MANIM_LOW_RES=1 manim -pql main.py EnergyScene    # 低清预览(画面审查用)
    manim -pqh main.py EnergyScene                    # 1080p60 高清成片
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
COL_B = "#8be9fd"      # 辅助
ACCENT = "#ffd866"     # 强调黄
ERR = "#ff6188"        # 斯托克斯(红移)
GREEN_A = "#a6e22e"    # 入射光

FONT = "Times New Roman"
CJK_FONT = "SimSun"


class EnergyScene(Scene):
    """能级图讲解:三种散射路径 + 能量守恒(definition 型,信息集中在左右两栏)。"""

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR

        # ==== Phase 0: 标题 ====
        title_cn = Text("光子与分子的能量交换", font=CJK_FONT, font_size=42, color=WHITE_)
        title_en = Text("Energy Exchange", font=FONT, font_size=28, color=WHITE_).set_opacity(0.55)
        title = VGroup(title_cn, title_en).arrange(RIGHT, buff=0.4, aligned_edge=DOWN).to_edge(UP, buff=0.3)
        title.move_to([0, title_cn.get_y(), 0])
        self.play(FadeIn(title_cn, shift=DOWN * 0.3), run_time=0.8)
        self.play(FadeIn(title_en, shift=DOWN * 0.3), run_time=0.6)
        self.wait(0.5)

        # ==== Phase 1: 能级骨架(左侧)====
        diag_left = -2.6
        lv0_y, lv1_y, lvv_y = -1.7, -0.4, 1.5
        lv0 = Line([diag_left - 0.3, lv0_y, 0], [diag_left + 1.8, lv0_y, 0], color=WHITE_, stroke_width=4)
        lv1 = Line([diag_left - 0.3, lv1_y, 0], [diag_left + 1.8, lv1_y, 0], color=WHITE_, stroke_width=4)
        lab0 = Text("振动基态 v = 0", font=CJK_FONT, font_size=18, color=WHITE_).next_to(lv0, LEFT, buff=0.15)
        lab1 = Text("振动激发态 v = 1", font=CJK_FONT, font_size=18, color=WHITE_).next_to(lv1, LEFT, buff=0.15)

        gap = Line([diag_left + 1.35, lv0_y, 0], [diag_left + 1.35, lv1_y, 0], color=COL_B, stroke_width=2)
        gap.add_tip(tip_length=0.12)
        gap.add_tip(tip_length=0.12, at_start=True)
        gap_label = MathTex(r"h\nu_{\mathrm{vib}}", color=COL_B).scale(0.8).next_to(gap, RIGHT, buff=0.12)

        self.play(Create(lv0), Create(lv1), FadeIn(lab0), FadeIn(lab1), run_time=1.2)
        self.play(Create(gap), FadeIn(gap_label), run_time=1.0)
        self.wait(0.5)

        # 虚态:虚线 + 标注"非真实能级"(spec_lock visual_forbidden:必须虚线)
        lvv = DashedLine([diag_left - 0.3, lvv_y, 0], [diag_left + 1.8, lvv_y, 0], color=COL_B, stroke_width=3, dash_length=0.14)
        labv = Text("虚态(非真实能级)", font=CJK_FONT, font_size=18, color=COL_B).next_to(lvv, LEFT, buff=0.15)
        self.play(Create(lvv), FadeIn(labv, shift=LEFT * 0.2), run_time=1.2)
        self.wait(0.8)

        # ==== Phase 2: 公式面板(右侧)====
        panel = RoundedRectangle(width=4.6, height=1.6, corner_radius=0.15, color=WHITE_, stroke_width=2)
        panel.move_to([4.6, -0.9, 0])
        eq = MathTex(r"h\nu'", "=", r"h\nu_0", r"\pm", r"h\nu_{\mathrm{vib}}").move_to(panel.get_center())
        panel_title = Text("能量守恒", font=CJK_FONT, font_size=20, color=ACCENT).next_to(panel, UP, buff=0.15)
        self.play(FadeIn(panel), FadeIn(panel_title), run_time=0.8)
        self.play(FadeIn(eq, shift=UP * 0.2), run_time=1.0)
        self.wait(0.6)

        # ==== Phase 3: 三种散射路径 ====
        # 说明文字固定列垂直分层(避免三支路径的文字水平重叠、侵入右侧面板)
        def path(x0: float, up_color, down_color, note_text, note_color, note_y: float) -> None:
            up = Line([x0, lv0_y, 0], [x0, lvv_y, 0], color=GREEN_A, stroke_width=5)
            up.add_tip(tip_length=0.16)
            down = Line([x0, lvv_y, 0], [x0, lv1_y, 0], color=down_color, stroke_width=5)
            down.add_tip(tip_length=0.16)
            note = Text(note_text, font=CJK_FONT, font_size=18, color=note_color).move_to([0.7, note_y, 0])
            self.play(Create(up), run_time=1.0)
            self.play(Create(down), run_time=1.0)
            self.play(FadeIn(note, shift=UP * 0.15), run_time=0.8)
            self.wait(1.0)
            return up, down, note

        # 阶段 1:瑞利(回基态)
        up1, down1, note1 = path(diag_left + 0.3, GREEN_A, WHITE_, "瑞利:频率不变", WHITE_, 1.05)
        eq[2].set_color(ACCENT)
        self.play(Indicate(eq[2], color=ACCENT), run_time=0.8)
        self.wait(0.6)

        # 阶段 2:斯托克斯(到激发态,红移)
        up2, down2, note2 = path(diag_left + 0.9, GREEN_A, ERR, "斯托克斯:留一个量子给分子", ERR, 0.05)
        eq[4].set_color(ERR)
        self.play(Indicate(eq[4], color=ERR), run_time=0.8)
        self.wait(0.6)

        # 阶段 3:反斯托克斯(从激发态出发,蓝移)
        up3 = Line([diag_left + 1.5, lv1_y, 0], [diag_left + 1.5, lvv_y, 0], color=GREEN_A, stroke_width=5)
        up3.add_tip(tip_length=0.16)
        down3 = Line([diag_left + 1.5, lvv_y, 0], [diag_left + 1.5, lv0_y, 0], color=COL_A, stroke_width=5)
        down3.add_tip(tip_length=0.16)
        note3 = Text("反斯托克斯:拿走一个量子", font=CJK_FONT, font_size=18, color=COL_A).move_to([0.7, -1.35, 0])
        self.play(Create(up3), run_time=1.0)
        self.play(Create(down3), run_time=1.0)
        self.play(FadeIn(note3, shift=UP * 0.15), run_time=0.8)
        eq[3].set_color(COL_A)
        self.play(Indicate(eq[3], color=COL_A), run_time=0.8)
        self.wait(1.0)

        # ==== Phase 4: 收尾 ====
        summary = Text("光子与分子,交换一个振动量子", font=CJK_FONT, font_size=24, color=WHITE_).move_to([4.6, -2.5, 0])
        self.play(FadeIn(summary, shift=UP * 0.2), run_time=1.0)
        self.wait(0.6)
        self.play(Indicate(summary, color=ACCENT), run_time=0.8)
        self.wait(2.0)
