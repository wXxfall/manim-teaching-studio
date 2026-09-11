"""scene05 澄清与总结:三张 ✗ 误区 → ✓ 正解 卡片依次呈现,收尾总结条.

Run:
    MANIM_LOW_RES=1 manim -pql main.py ClarifyScene    # 低清预览(画面审查用)
    manim -pqh main.py ClarifyScene                    # 1080p60 高清成片
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
COL_A = "#58b9ff"
COL_B = "#8be9fd"
ACCENT = "#ffd866"
ERR = "#ff6188"
GREEN_A = "#a6e22e"

FONT = "Times New Roman"
CJK_FONT = "SimSun"


class ClarifyScene(Scene):
    """三张误区澄清卡片(anchor 型,慢节奏留白),收尾总结。"""

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR

        # ==== Phase 0: 标题 ====
        title_cn = Text("三个最常见的误区", font=CJK_FONT, font_size=42, color=WHITE_)
        title_en = Text("Common Misconceptions", font=FONT, font_size=28, color=WHITE_).set_opacity(0.55)
        title = VGroup(title_cn, title_en).arrange(RIGHT, buff=0.4, aligned_edge=DOWN).to_edge(UP, buff=0.25)
        title.move_to([0, title_cn.get_y(), 0])
        self.play(FadeIn(title_cn, shift=DOWN * 0.3), run_time=0.8)
        self.play(FadeIn(title_en, shift=DOWN * 0.3), run_time=0.6)
        self.wait(0.8)

        cards = [
            (
                "误区一:拉曼是吸收过程",
                "正解:拉曼是散射——光子并未被共振吸收,\n虚态不要求光子能量匹配任何实能级",
            ),
            (
                "误区二:拉曼位移随激光波长而变",
                "正解:位移只由振动模决定;\n换波长只是谱线整体平移,位移不变",
            ),
            (
                "误区三:反斯托克斯线与斯托克斯等强",
                "正解:常温下反斯托克斯约 0.8%;\n玻尔兹曼分布——这个比值反过来能测温",
            ),
        ]

        card_box = RoundedRectangle(width=9.6, height=2.6, corner_radius=0.15, color=WHITE_, stroke_width=2)
        card_box.move_to([0, 0.3, 0])

        for i, (wrong, right) in enumerate(cards):
            cross = Text("×", font=CJK_FONT, font_size=64, color=ERR).move_to([-4.0, 0.3, 0])
            wrong_txt = Text(wrong, font=CJK_FONT, font_size=26, color=ERR).move_to([-0.6, 0.3, 0])
            check = Text("√", font=CJK_FONT, font_size=56, color=GREEN_A).move_to([-4.0, 0.3, 0])
            right_txt = Text(right, font=CJK_FONT, font_size=24, color=WHITE_, line_spacing=1.4).move_to([-0.6, 0.3, 0])

            if i == 0:
                self.play(FadeIn(card_box), run_time=0.6)
            self.play(FadeIn(cross, scale=0.8), FadeIn(wrong_txt, shift=UP * 0.15), run_time=1.2)
            self.wait(1.5)  # 思考停顿
            self.play(
                FadeOut(cross, scale=0.6),
                FadeOut(wrong_txt, shift=UP * 0.1),
                run_time=0.8,
            )
            self.play(FadeIn(check, scale=1.2), FadeIn(right_txt, shift=UP * 0.15), run_time=1.2)
            self.wait(1.5)
            if i < 2:
                self.play(
                    FadeOut(check), FadeOut(right_txt, shift=UP * 0.1),
                    run_time=0.8,
                )

        # 第三张卡片停留后,整体淡出
        self.play(FadeOut(check), FadeOut(right_txt), FadeOut(card_box), run_time=1.0)

        # ==== Phase 1: 总结条 ====
        summary_1 = Text("一束光,打听到分子振动的秘密", font=CJK_FONT, font_size=30, color=WHITE_).move_to([0, 1.0, 0])
        summary_2 = Text(
            "无需标记 · 不伤样品 · 指纹识别 —— 这就是拉曼光谱",
            font=CJK_FONT, font_size=24, color=ACCENT,
        ).move_to([0, -0.1, 0])
        summary_3 = Text(
            "从 1928 年地中海上的一抹深蓝,到今天的实验室利器",
            font=CJK_FONT, font_size=18, color=WHITE_,
        ).set_opacity(0.6).move_to([0, -1.2, 0])

        self.play(FadeIn(summary_1, shift=UP * 0.2), run_time=1.2)
        self.wait(0.5)
        self.play(FadeIn(summary_2, shift=UP * 0.2), run_time=1.2)
        self.wait(0.5)
        self.play(FadeIn(summary_3, shift=UP * 0.2), run_time=1.0)
        self.wait(0.8)
        self.play(Indicate(summary_2, color=ACCENT), run_time=0.9)

        self.wait(3.0)
