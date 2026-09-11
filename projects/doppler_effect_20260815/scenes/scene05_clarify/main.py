"""scene05 澄清:三大误区(✗ 错误 → ✓ 正解)+ 一句总结.

Run:
    MANIM_LOW_RES=1 manim -pql main.py ClarifyScene     # 低清预览(画面审查用)
    manim -pqh main.py ClarifyScene                     # 1080p60 高清成片
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


def make_cross() -> VGroup:
    """✗(线段绘制,避免字体缺字)。"""
    return VGroup(
        Line(LEFT * 0.14 + UP * 0.14, RIGHT * 0.14 + DOWN * 0.14, color=ERR, stroke_width=5),
        Line(LEFT * 0.14 + DOWN * 0.14, RIGHT * 0.14 + UP * 0.14, color=ERR, stroke_width=5),
    )


def make_check() -> VGroup:
    """✓(线段绘制,避免字体缺字)。"""
    return VGroup(
        Line(LEFT * 0.15 + DOWN * 0.02, LEFT * 0.02 + UP * 0.12, color=GREEN_A, stroke_width=5),
        Line(LEFT * 0.02 + UP * 0.12, RIGHT * 0.16 + DOWN * 0.14, color=GREEN_A, stroke_width=5),
    )


class ClarifyScene(Scene):
    """澄清:三个误区 + 一句话总结。"""

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR

        # ==== Phase 1: 标题 ====
        title = Text("三个常见误区", font=CJK_FONT, font_size=34, color=WHITE_).to_edge(UP, buff=0.35).set_name("标题")
        self.play(FadeIn(title, shift=DOWN * 0.3), run_time=1.0)
        self.wait(0.6)

        # ==== Phase 2: 三张误区卡片 ====
        xs = (-4.3, 0.0, 4.3)
        wrongs = ("声源运动会改变波速", "声源动与观察者动完全一样", "音调变化只是响度或错觉")
        rights = ("波速由介质决定,\n声源只改波长", "一个在分母、一个在分子,\n低速时才趋同", "接收频率真实变化,\n可以精确测量")
        labels = ("误区一", "误区二", "误区三")

        cards, wrong_txts, right_txts = [], [], []
        for k, x in enumerate(xs):
            card = RoundedRectangle(width=3.9, height=3.4, corner_radius=0.12, color=WHITE_, stroke_width=2)
            card.move_to([x, 0.5, 0])
            cards.append(card)

        self.play(FadeIn(cards[0]), FadeIn(cards[1]), FadeIn(cards[2]), run_time=1.2)
        self.wait(0.6)

        for k, x in enumerate(xs):
            lab = Text(labels[k], font=CJK_FONT, font_size=17, color=COL_B).move_to([x, 1.65, 0])
            lab.set_name(f"标签·{labels[k]}")
            wrong = Text(wrongs[k], font=CJK_FONT, font_size=18, color=ERR).move_to([x, 1.05, 0])
            wrong.set_name(f"误区·{k+1}")
            cross = make_cross().move_to([x - 1.55, 1.05, 0])
            if k == 0:  # 预览注解:误区·1 文字拖拽下移 0.5,✗ 图标随文字同步保持配对
                wrong.shift(DOWN * 0.5)
                cross.shift(DOWN * 0.5)
            right = Text(rights[k], font=CJK_FONT, font_size=17, color=GREEN_A, line_spacing=0.8)
            right.move_to([x, 0.1, 0])
            right.set_name(f"正解·{k+1}")
            check = make_check().move_to([x - 1.55, 0.1, 0])
            wrong_txts.append(wrong)
            right_txts.append(right)

            self.play(FadeIn(lab), run_time=0.5)
            self.play(FadeIn(cross), FadeIn(wrong), run_time=0.8)
            self.wait(0.8)
            self.play(FadeIn(check), FadeIn(right), run_time=1.0)
            self.wait(1.0)

        # ==== Phase 3: 总结条 ====
        bar = RoundedRectangle(width=11.6, height=0.95, corner_radius=0.2, color=ACCENT, stroke_width=2)
        bar.move_to([0, -2.35, 0]).set_name("总结条")
        summary = Text("多普勒效应 = 相对运动改变了每秒接收的波数", font=CJK_FONT, font_size=23, color=ACCENT)
        summary.move_to(bar.get_center()).set_name("总结句")
        note = Text("另:声学公式不直接套光,光的多普勒按相对论处理", font=CJK_FONT, font_size=15, color=COL_B)
        note.set_opacity(0.85).move_to([0, -3.3, 0]).set_name("补充注")

        self.play(FadeIn(bar), FadeIn(summary, shift=UP * 0.1), run_time=1.4)
        self.wait(1.2)
        self.play(FadeIn(note, shift=UP * 0.1), run_time=1.0)
        self.wait(1.2)

        # 结尾留白(shot_table wait 预算内)
        self.wait(3.2)
