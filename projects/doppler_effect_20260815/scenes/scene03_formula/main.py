"""scene03 公式:观察者动 / 波源动分情况推导 → 统一式 → 救护车数值例题.

Run:
    MANIM_LOW_RES=1 manim -pql main.py FormulaScene    # 低清预览(画面审查用)
    manim -pqh main.py FormulaScene                    # 1080p60 高清成片
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

PANEL_X = 3.1   # 右侧公式面板中心 x(预览注解:面板左移 0.5)
DIAG_Y = 1.5    # 左侧示意图基准 y


def make_observer() -> VGroup:
    """简化观察者图标(头+身)。"""
    head = Circle(radius=0.1, color=WHITE_, fill_color=WHITE_, fill_opacity=1.0, stroke_width=2)
    body = Line(head.get_bottom(), head.get_bottom() + DOWN * 0.3, color=WHITE_, stroke_width=3)
    return VGroup(head, body)


class FormulaScene(Scene):
    """推导:分子分母各管一件事,统一式 + 数值例题。"""

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR

        # ==== Phase 0: 面板 ====
        panel = RoundedRectangle(width=6.6, height=6.8, corner_radius=0.15, color=WHITE_, stroke_width=2)
        panel.move_to([PANEL_X, 0.35, 0]).set_name("公式面板")
        panel_title = Text("从波面到公式", font=CJK_FONT, font_size=24, color=ACCENT)
        panel_title.move_to([PANEL_X, 3.45, 0]).set_name("面板标题")  # 预览注解:标题下移 0.5,入面板内

        self.play(FadeIn(panel), FadeIn(panel_title), run_time=1.2)
        self.wait(0.8)

        # ==== Phase 1: 观察者动 ====
        # 左图:静止波源 + 同心圆,观察者向左(朝波源)运动
        src1 = Dot([-4.2, DIAG_Y, 0], radius=0.09, color=WHITE_).set_name("静止波源")
        circ1 = VGroup()
        for r in (0.5, 1.0, 1.5):
            c = DashedVMobject(Circle(radius=r, color=COL_B, stroke_width=2), num_dashes=40)
            c.move_to(src1.get_center()).set_opacity(0.7)
            circ1.add(c)
        circ1.set_name("波面·静止")
        obs1 = make_observer().move_to([0.0, DIAG_Y, 0]).set_name("观察者")
        vo_arr = Arrow([0.55, DIAG_Y, 0], [-0.1, DIAG_Y, 0], color=COL_A, stroke_width=3,
                       tip_length=0.14, max_tip_length_to_length_ratio=0.25)
        vo_txt = MathTex(r"v_o", color=COL_A).scale(0.7)
        vo_txt.next_to(vo_arr, UP, buff=0.12).set_name("标注·观察者速度")

        self.play(FadeIn(src1), run_time=0.6)
        self.play(LaggedStart(*[Create(c) for c in circ1], lag_ratio=0.6), run_time=2.0)
        self.wait(0.6)
        self.play(FadeIn(obs1), FadeIn(vo_arr), FadeIn(vo_txt), run_time=0.8)
        self.play(obs1.animate.move_to([-1.2, DIAG_Y, 0]), run_time=1.0)
        self.wait(0.6)

        eq_base = MathTex(r"v = \lambda f", color=WHITE_).scale(0.8).move_to([PANEL_X, 3.0, 0]).set_name("公式·波速关系")
        lab1 = Text("① 观察者动 · 波源不动", font=CJK_FONT, font_size=20, color=COL_A)
        lab1.move_to([PANEL_X, 2.6, 0]).set_name("阶段标签·观察者动")
        eq_obs_1 = MathTex(r"f' = \frac{v \pm v_o}{\lambda}", color=WHITE_).move_to([PANEL_X, 2.15, 0]).set_name("公式·观察者动1")
        eq_obs_2 = MathTex(r"f' = f\left(1 + \frac{v_o}{v}\right)", color=WHITE_).move_to([PANEL_X, 1.55, 0]).set_name("公式·观察者动2")

        self.play(FadeIn(eq_base), FadeIn(lab1), run_time=0.8)
        self.play(Write(eq_obs_1), run_time=1.4)
        self.wait(1.2)
        self.play(Write(eq_obs_2), run_time=1.4)
        self.play(eq_obs_2.animate.set_color(COL_A), run_time=0.6)
        self.wait(2.0)

        # ==== Phase 2: 波源动 ====
        group1 = VGroup(eq_base, lab1, eq_obs_1, eq_obs_2)
        self.play(group1.animate.set_opacity(0.35).shift(UP * 0.6), run_time=1.2)
        self.play(FadeOut(vo_arr), FadeOut(vo_txt), FadeOut(obs1), FadeOut(circ1), run_time=0.8)

        # 左图:波源向右运动,波面前密后疏
        src2 = Dot([-2.6, DIAG_Y, 0], radius=0.09, color=COL_A).set_name("运动波源")
        vs_arr = Arrow([-2.2, DIAG_Y, 0], [-1.6, DIAG_Y, 0], color=COL_A, stroke_width=3,
                       tip_length=0.14, max_tip_length_to_length_ratio=0.25)
        vs_txt = MathTex(r"v_s", color=COL_A).scale(0.7)
        vs_txt.next_to(vs_arr, UP, buff=0.12).set_name("标注·波源速度")
        obs2 = make_observer().move_to([0.0, DIAG_Y, 0]).set_name("观察者·静止")

        self.play(FadeIn(src2), FadeIn(vs_arr), FadeIn(vs_txt), FadeIn(obs2), run_time=0.8)
        self.play(src2.animate.move_to([-1.6, DIAG_Y, 0]), run_time=0.8)
        circ2 = VGroup()
        for i in (1, 2, 3):  # 圆心 -1.6-0.2i,半径 0.5i → 前方间隔 0.3 / 后方 0.7
            c = DashedVMobject(Circle(radius=0.5 * i, color=COL_A, stroke_width=2), num_dashes=40)
            c.move_to([-1.6 - 0.2 * i, DIAG_Y, 0]).set_opacity(0.75)
            circ2.add(c)
        circ2.set_name("波面·运动")
        self.play(LaggedStart(*[Create(c) for c in circ2], lag_ratio=0.5), run_time=1.8)
        self.wait(0.6)
        lam_arr = DoubleArrow([-1.3, DIAG_Y, 0], [-1.0, DIAG_Y, 0], color=ERR, stroke_width=3,
                              tip_length=0.1, max_tip_length_to_length_ratio=0.35)
        lam_txt = MathTex(r"\lambda'", color=ERR).scale(0.7)
        lam_txt.next_to(lam_arr, UP, buff=0.1).set_name("标注·压缩波长")
        self.play(FadeIn(lam_arr), FadeIn(lam_txt), run_time=0.8)
        self.wait(0.6)

        lab2 = Text("② 波源动 · 观察者不动", font=CJK_FONT, font_size=20, color=GREEN_A)
        lab2.move_to([PANEL_X, 1.35, 0]).set_name("阶段标签·波源动")
        eq_src_1 = MathTex(r"\lambda' = \frac{v \mp v_s}{f}", color=WHITE_).move_to([PANEL_X, 0.8, 0]).set_name("公式·波源动波长")
        eq_src_2 = MathTex(r"f' = \frac{v}{\lambda'} = f\,\frac{v}{v \mp v_s}", color=WHITE_)
        eq_src_2.move_to([PANEL_X, 0.15, 0]).set_name("公式·波源动频率")

        self.play(FadeIn(lab2), run_time=0.6)
        self.play(Write(eq_src_1), run_time=1.4)
        self.wait(1.0)
        self.play(Write(eq_src_2), run_time=1.6)
        self.play(eq_src_2.animate.set_color(GREEN_A), run_time=0.6)
        self.wait(2.0)

        # ==== Phase 3: 统一式 + 例题 ====
        lab3 = Text("③ 统一式 + 救护车例题", font=CJK_FONT, font_size=20, color=ACCENT)
        lab3.move_to([PANEL_X, -0.6, 0]).set_name("阶段标签·统一式")
        eq_unified = MathTex(r"f' = f\,\frac{v \pm v_o}{v \mp v_s}", color=WHITE_).scale(1.1)
        eq_unified.move_to([PANEL_X, -1.2, 0]).set_name("公式·统一式")

        self.play(FadeIn(lab3), run_time=0.6)
        self.play(Write(eq_unified), run_time=1.8)
        self.play(eq_unified.animate.set_color(ACCENT), run_time=0.6)
        # 预览注解(自由文本"最终太密集"):淡出左侧示意图,让公式成为视觉主体
        self.play(
            VGroup(src2, circ2, vs_arr, vs_txt, obs2, lam_arr, lam_txt).animate.set_opacity(0.3),
            run_time=1.0,
        )
        self.wait(1.2)

        example = MathTex(r"\frac{340}{340-27.8} \approx 1.089", color=WHITE_).move_to([PANEL_X, -1.95, 0]).set_name("公式·例题")
        amb_note = Text("救护车 100 km/h ≈ 27.8 m/s,驶近", font=CJK_FONT, font_size=17, color=COL_B)
        amb_note.move_to([PANEL_X, -2.4, 0]).set_name("标注·救护车")
        hz_note = Text("1000 Hz 的笛声 → 1089 Hz(约 +9%)", font=CJK_FONT, font_size=19, color=ACCENT)
        hz_note.move_to([PANEL_X, -2.8, 0]).set_name("标注·频率变化")

        self.play(FadeIn(amb_note), run_time=0.8)
        self.play(Write(example), run_time=1.6)
        self.wait(0.8)
        self.play(FadeIn(hz_note, shift=UP * 0.1), run_time=1.2)
        self.wait(2.4)

        # 结尾留白(shot_table wait 预算内)
        self.wait(3.5)
