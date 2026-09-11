"""scene04 应用:雷达测速 / 医用超声 / 天文红移三卡片 + 光多普勒点题.

Run:
    MANIM_LOW_RES=1 manim -pql main.py ApplicationsScene    # 低清预览(画面审查用)
    manim -pqh main.py ApplicationsScene                    # 1080p60 高清成片
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

CARD_W, CARD_H = 3.9, 3.4


def make_car() -> VGroup:
    """简化小汽车(雷达卡图标)。"""
    body = RoundedRectangle(width=1.5, height=0.5, corner_radius=0.15, color=COL_A, stroke_width=2)
    top = Rectangle(width=0.6, height=0.3, color=COL_A, stroke_width=2).move_to(body.get_center() + UP * 0.25)
    w1 = Circle(radius=0.1, color=COL_A, stroke_width=2).move_to(body.get_bottom() + LEFT * 0.35 + DOWN * 0.08)
    w2 = Circle(radius=0.1, color=COL_A, stroke_width=2).move_to(body.get_bottom() + RIGHT * 0.35 + DOWN * 0.08)
    return VGroup(body, top, w1, w2)


def make_probe_vessel() -> VGroup:
    """超声探头 + 血管 + 血细胞(超声卡图标)。"""
    probe = RoundedRectangle(width=0.5, height=0.35, corner_radius=0.1, color=GREEN_A, stroke_width=2)
    vessel = RoundedRectangle(width=2.4, height=0.4, corner_radius=0.2, color=GREEN_A, stroke_width=2)
    vessel.shift(DOWN * 1.1)
    cells = VGroup(*[Dot(radius=0.045, color=GREEN_A) for _ in range(4)])
    for j, c in enumerate(cells):
        c.move_to(vessel.get_center() + np.array([-0.8 + 0.55 * j, 0, 0]))
    beam = DashedLine(probe.get_bottom(), vessel.get_top(), color=GREEN_A, stroke_width=2, dash_length=0.12)
    return VGroup(probe, beam, vessel, cells)


def make_spectrum() -> VGroup:
    """光谱红移图标:原谱线 + 右移红端谱线。"""
    base = np.array([-0.8, 0.2, 0])
    lines = VGroup()
    for i, c in enumerate((COL_A, GREEN_A, ACCENT)):
        l = Line(base + np.array([0.35 * i, -0.35, 0]), base + np.array([0.35 * i, 0.35, 0]),
                 color=c, stroke_width=5)
        lines.add(l)
    shifted = VGroup()
    for i, c in enumerate((COL_A, GREEN_A, ACCENT)):
        l = Line(base + np.array([0.35 * i + 0.55, -0.35, 0]), base + np.array([0.35 * i + 0.55, 0.35, 0]),
                 color=ERR, stroke_width=5).set_opacity(0.8)
        shifted.add(l)
    arrow = Arrow(base + np.array([0.75, 0.6, 0]), base + np.array([1.35, 0.6, 0]), color=ERR,
                  stroke_width=2, tip_length=0.12, max_tip_length_to_length_ratio=0.3)
    return VGroup(lines, shifted, arrow)


class ApplicationsScene(Scene):
    """应用:同一频移,三种尺度——车速、血流、星系。"""

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR

        # ==== Phase 0: 三张卡片 ====
        card_radar = RoundedRectangle(width=CARD_W, height=CARD_H, corner_radius=0.12, color=COL_A, stroke_width=2)
        card_radar.move_to([-4.3, 0.3, 0]).set_name("卡片·雷达测速")
        card_sono = RoundedRectangle(width=CARD_W, height=CARD_H, corner_radius=0.12, color=GREEN_A, stroke_width=2)
        card_sono.move_to([0, 0.3, 0]).set_name("卡片·医用超声")
        card_red = RoundedRectangle(width=CARD_W, height=CARD_H, corner_radius=0.12, color=ERR, stroke_width=2)
        card_red.move_to([4.3, 0.3, 0]).set_name("卡片·天文红移")

        title = Text("多普勒效应 · 应用", font=CJK_FONT, font_size=30, color=WHITE_).to_edge(UP, buff=0.3).set_name("标题")
        self.play(FadeIn(title, shift=DOWN * 0.3), run_time=1.0)
        self.play(FadeIn(card_radar), FadeIn(card_sono), FadeIn(card_red), run_time=1.2)
        self.wait(0.8)

        # ==== Phase 1: 雷达测速 ====
        t1 = Text("雷达测速", font=CJK_FONT, font_size=22, color=COL_A).move_to([-4.3, 1.55, 0]).set_name("标题·雷达")
        gun = VGroup(
            Rectangle(width=0.16, height=0.55, color=COL_A, stroke_width=2).move_to([-5.0, 0.55, 0]),
            Arc(radius=0.35, start_angle=-0.9, angle=1.1, color=COL_A, stroke_width=2).move_to([-5.05, 0.28, 0]),
        )
        waves1 = VGroup(*[Arc(radius=r, start_angle=-0.35, angle=0.7, color=COL_A, stroke_width=2)
                          for r in (0.6, 0.9, 1.2)]).move_to([-4.45, 0.55, 0])
        icon1 = VGroup(gun, waves1, make_car().move_to([-3.6, 0.05, 0])).set_name("图标·雷达")
        eq1 = MathTex(r"f_d = \frac{2 f_0 v}{c}", color=WHITE_).scale(0.8).move_to([-4.3, -0.7, 0]).set_name("公式·雷达")
        val1 = Text("10.525 GHz · 100 km/h → ≈1.95 kHz", font=CJK_FONT, font_size=15, color=COL_B)
        val1.move_to([-4.3, -1.3, 0]).set_name("数值·雷达")

        self.play(FadeIn(t1), run_time=0.6)
        self.play(FadeIn(icon1), run_time=1.0)
        self.play(Write(eq1), run_time=1.2)
        self.play(FadeIn(val1, shift=UP * 0.1), run_time=1.0)
        self.wait(2.0)

        # ==== Phase 2: 医用超声 ====
        t2 = Text("医用超声", font=CJK_FONT, font_size=22, color=GREEN_A).move_to([0, 1.55, 0]).set_name("标题·超声")
        icon2 = make_probe_vessel().move_to([0, 0.15, 0]).set_name("图标·超声")
        eq2 = MathTex(r"f_d = \frac{2 f_0 v \cos\theta}{c}", color=WHITE_).scale(0.8).move_to([0, -0.7, 0]).set_name("公式·超声")
        val2 = Text("2~10 MHz · 血流 0.3~1 m/s → 几百 Hz~几 kHz", font=CJK_FONT, font_size=15, color=COL_B)
        val2.move_to([0, -1.3, 0]).set_name("数值·超声")

        self.play(FadeIn(t2), run_time=0.6)
        self.play(FadeIn(icon2), run_time=1.0)
        self.play(Write(eq2), run_time=1.2)
        self.play(FadeIn(val2, shift=UP * 0.1), run_time=1.0)
        self.wait(2.0)

        # ==== Phase 3: 天文红移 ====
        t3 = Text("天文红移", font=CJK_FONT, font_size=22, color=ERR).move_to([4.3, 1.55, 0]).set_name("标题·红移")
        icon3 = make_spectrum().move_to([4.3, 0.15, 0]).set_name("图标·红移")
        eq3 = MathTex(r"\frac{\Delta f}{f} \approx \frac{v}{c}", color=WHITE_).scale(0.8).move_to([4.3, -0.7, 0]).set_name("公式·红移")
        val3 = Text("星系远离 → 谱线红移;哈勃 v = H₀ d", font=CJK_FONT, font_size=15, color=COL_B)
        val3.move_to([4.3, -1.3, 0]).set_name("数值·红移")

        self.play(FadeIn(t3), run_time=0.6)
        self.play(FadeIn(icon3), run_time=1.0)
        self.play(Write(eq3), run_time=1.2)
        self.play(FadeIn(val3, shift=UP * 0.1), run_time=1.0)
        self.wait(2.2)

        # ==== Phase 4: 光多普勒点题 ====
        note_txt = Text("光的多普勒 · 无介质 · 高速须用相对论式:", font=CJK_FONT, font_size=20, color=WHITE_)
        note_eq = MathTex(
            r"f_{\mathrm{obs}} = f_s \sqrt{\frac{1+\beta}{1-\beta}}", r",\ \beta = \frac{v}{c}",
            color=WHITE_,
        )
        note = VGroup(note_txt, note_eq).arrange(RIGHT, buff=0.3).to_edge(DOWN, buff=0.3)
        note_txt.set_name("点题·文字")
        note_eq.set_name("点题·公式")

        self.play(FadeIn(note, shift=UP * 0.15), run_time=1.6)
        self.wait(2.0)

        # 结尾留白(shot_table wait 预算内)
        self.wait(3.0)
