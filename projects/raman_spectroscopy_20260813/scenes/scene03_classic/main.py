"""scene03 经典推导:三频率分量 + 光谱示意 — p=αE、极化率展开、代入得到 ν₀/ν₀−ν_vib/ν₀+ν_vib,光谱对称双峰,拉曼位移定义.

Run:
    MANIM_LOW_RES=1 manim -pql main.py ClassicScene    # 低清预览(画面审查用)
    manim -pqh main.py ClassicScene                    # 1080p60 高清成片
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
GREEN_A = "#a6e22e"    # 入射/电场

FONT = "Times New Roman"
CJK_FONT = "SimSun"


class ClassicScene(Scene):
    """经典电磁图像推导三频率分量,并落到光谱图与拉曼位移定义(derivation 型)。"""

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR

        # ==== Phase 0: 标题 ====
        title_cn = Text("三个频率从哪来", font=CJK_FONT, font_size=42, color=WHITE_)
        title_en = Text("Classical Picture", font=FONT, font_size=28, color=WHITE_).set_opacity(0.55)
        title = VGroup(title_cn, title_en).arrange(RIGHT, buff=0.4, aligned_edge=DOWN).to_edge(UP, buff=0.25)
        title.move_to([0, title_cn.get_y(), 0])
        self.play(FadeIn(title_cn, shift=DOWN * 0.3), run_time=0.8)
        self.play(FadeIn(title_en, shift=DOWN * 0.3), run_time=0.6)
        self.wait(0.4)

        # ==== Phase 1: 诱导偶极 ====
        eq_p = MathTex(r"\mathbf{p} = \alpha\,\mathbf{E}", color=WHITE_).move_to([0, 2.3, 0])
        self.play(FadeIn(eq_p, shift=DOWN * 0.2), run_time=1.0)
        self.wait(0.8)

        # ==== Phase 2: 极化率展开 + 简谐坐标 ====
        eq_alpha = MathTex(
            r"\alpha(Q)", "=", r"\alpha_0", "+", r"\left(\frac{\partial\alpha}{\partial Q}\right)_0 Q",
        ).move_to([-1.7, 1.35, 0])
        eq_qt = MathTex(r"Q(t) = Q_0 \cos(2\pi \nu_{\mathrm{vib}} t)").move_to([2.8, 1.35, 0])
        self.play(FadeIn(eq_alpha, shift=DOWN * 0.2), run_time=1.2)
        self.wait(0.6)
        self.play(FadeIn(eq_qt, shift=DOWN * 0.2), run_time=1.2)
        self.wait(0.8)

        # ==== Phase 2.5: 分子振子小图(为什么 α 随 Q 变;与公式行留 0.2 间隙)====
        atom_l = Circle(radius=0.22, color=COL_B, fill_opacity=0.25).move_to([-0.9, 0.75, 0])
        atom_r = Circle(radius=0.22, color=COL_B, fill_opacity=0.25).move_to([0.9, 0.75, 0])
        spring = Line(atom_l.get_right(), atom_r.get_left(), color=WHITE_, stroke_width=2)
        vib_anim = VGroup(atom_l, atom_r, spring)
        vib_note = Text("分子振动 → 极化率随时间变化", font=CJK_FONT, font_size=16, color=COL_B).next_to(vib_anim, DOWN, buff=0.12)
        self.play(FadeIn(atom_l), FadeIn(atom_r), Create(spring), run_time=0.8)
        self.play(
            atom_l.animate.shift(LEFT * 0.15),
            atom_r.animate.shift(RIGHT * 0.15),
            rate_func=rate_functions.smooth, run_time=0.7,
        )
        self.play(
            atom_l.animate.shift(RIGHT * 0.15),
            atom_r.animate.shift(LEFT * 0.15),
            rate_func=rate_functions.smooth, run_time=0.7,
        )
        self.play(FadeIn(vib_note), run_time=0.6)
        self.wait(0.5)

        # ==== Phase 3: 代入 → 三频率分量 ====
        arrow_in = Line([0, 0.15, 0], [0, -0.05, 0], color=ACCENT, stroke_width=3)
        arrow_in.add_tip(tip_length=0.14)
        eq_result = MathTex(
            r"\nu_0", r",\quad", r"\nu_0-\nu_{\mathrm{vib}}", r",\quad", r"\nu_0+\nu_{\mathrm{vib}}",
        ).move_to([0, -0.6, 0])
        eq_result[0].set_color(WHITE_)
        eq_result[2].set_color(ERR)
        eq_result[4].set_color(COL_A)
        self.play(Create(arrow_in), run_time=0.7)
        self.play(FadeIn(eq_result, shift=DOWN * 0.2), run_time=1.2)
        # 推导中间过程淡出保留(不删除)
        self.play(
            eq_alpha.animate.set_opacity(0.35),
            eq_qt.animate.set_opacity(0.35),
            vib_anim.animate.set_opacity(0.35),
            vib_note.animate.set_opacity(0.35),
            run_time=1.0,
        )
        self.wait(1.0)

        # ==== Phase 4: 光谱示意(三频率结论淡出,光谱接管画面)====
        ax = Axes(
            x_range=[-1.6, 1.6, 0.5], y_range=[0, 1.15, 0.25],
            x_length=6.4, y_length=2.2,
            axis_config={"color": WHITE_, "stroke_width": 2, "include_ticks": False},
        ).move_to([0, -1.75, 0])
        xlab_neg = MathTex(r"-\nu_{\mathrm{vib}}", color=WHITE_).scale(0.7).next_to(ax.c2p(-1.0, 0), DOWN, buff=0.05)
        xlab_zero = MathTex(r"\nu_0", color=WHITE_).scale(0.7).next_to(ax.c2p(0, 0), DOWN, buff=0.05)
        xlab_pos = MathTex(r"+\nu_{\mathrm{vib}}", color=WHITE_).scale(0.7).next_to(ax.c2p(1.0, 0), DOWN, buff=0.05)
        ax_title = Text("散射光谱(颜色为频率偏移记号)", font=CJK_FONT, font_size=18, color=COL_B).next_to(ax, UP, buff=0.15)
        self.play(
            FadeIn(ax), FadeIn(xlab_neg), FadeIn(xlab_zero), FadeIn(xlab_pos), FadeIn(ax_title),
            FadeOut(eq_result),
            run_time=1.5,
        )
        self.wait(0.5)

        # 瑞利峰(中央最高,白色)
        g_rayleigh = ax.plot(lambda x: 1.0 * np.exp(-((x / 0.07) ** 2) / 2), color=WHITE_, stroke_width=4)
        lab_ray = Text("瑞利", font=CJK_FONT, font_size=16, color=WHITE_).next_to(ax.c2p(0, 1.02), UP, buff=0.05)
        self.play(Create(g_rayleigh), FadeIn(lab_ray), run_time=1.2)
        self.wait(0.6)

        # 斯托克斯峰(左,红,高 0.25)
        g_stokes = ax.plot(lambda x: 0.25 * np.exp(-(((x + 1.0) / 0.12) ** 2) / 2), color=ERR, stroke_width=4)
        lab_sto = Text("斯托克斯", font=CJK_FONT, font_size=16, color=ERR).next_to(ax.c2p(-1.0, 0.25), UP, buff=0.08)
        self.play(Create(g_stokes), FadeIn(lab_sto), run_time=1.2)
        self.wait(0.6)

        # 反斯托克斯峰(右,蓝,真实高度 0.008——按 spec_lock honesty 真实取值)
        g_anti = ax.plot(lambda x: 0.008 * np.exp(-(((x - 1.0) / 0.12) ** 2) / 2), color=COL_A, stroke_width=4)
        lab_anti = Text("反斯托克斯", font=CJK_FONT, font_size=16, color=COL_A).next_to(ax.c2p(1.0, 0.008), UP, buff=0.25)
        self.play(Create(g_anti), FadeIn(lab_anti), run_time=1.2)
        self.wait(0.8)

        # inset:反斯托克斯峰放大 100 倍(诚实标注放大倍数)
        inset = Axes(
            x_range=[0.55, 1.45, 0.3], y_range=[0, 0.01, 0.005],
            x_length=1.7, y_length=1.0,
            axis_config={"color": WHITE_, "stroke_width": 1.5, "include_ticks": False},
        ).move_to([4.35, -3.0, 0])
        inset_curve = inset.plot(lambda x: 0.008 * np.exp(-(((x - 1.0) / 0.12) ** 2) / 2), color=COL_A, stroke_width=5)
        inset_note = Text("×100 放大", font=CJK_FONT, font_size=14, color=COL_A).next_to(inset, UP, buff=0.05)
        inset_frame = SurroundingRectangle(inset, color=COL_B, stroke_width=1, buff=0.08)
        self.play(FadeIn(inset_frame), FadeIn(inset), Create(inset_curve), FadeIn(inset_note), run_time=1.5)
        self.wait(0.8)

        # ==== Phase 5: 拉曼位移定义 ====
        d_arrow_l = DoubleArrow(
            ax.c2p(-1.0, 0.32), ax.c2p(0, 0.32), color=ACCENT, stroke_width=3, tip_length=0.12,
        )
        d_arrow_r = DoubleArrow(
            ax.c2p(0, 0.32), ax.c2p(1.0, 0.32), color=ACCENT, stroke_width=3, tip_length=0.12,
        )
        d_label = MathTex(r"\Delta\bar{\nu}", color=ACCENT).scale(0.8).next_to(ax.c2p(0.5, 0.32), UP, buff=0.08)
        self.play(Create(d_arrow_l), Create(d_arrow_r), FadeIn(d_label), run_time=1.2)
        self.wait(0.5)

        eq_shift = MathTex(r"\Delta\bar{\nu} = \frac{1}{\lambda_0} - \frac{1}{\lambda'}", color=ACCENT).move_to([5.1, -1.3, 0])
        eq_shift_note = Text("只由振动模决定,与激光波长无关", font=CJK_FONT, font_size=16, color=WHITE_).set_opacity(0.75).next_to(eq_shift, DOWN, buff=0.15)
        self.play(FadeIn(eq_shift, shift=UP * 0.2), run_time=1.2)
        self.play(FadeIn(eq_shift_note, shift=UP * 0.2), run_time=0.8)
        self.wait(1.2)

        # ==== Phase 6: 强度比注记(两行居中,避开右侧 ×100 inset 与画布下缘)====
        ratio_note = VGroup(
            Text("两侧不等强:玻尔兹曼分布(300 K)", font=CJK_FONT, font_size=14, color=WHITE_),
            Text("I反斯托克斯 / I斯托克斯 ≈ 0.008", font=CJK_FONT, font_size=14, color=WHITE_),
        ).arrange(DOWN, buff=0.12).set_opacity(0.75).move_to([0, -3.7, 0])
        self.play(FadeIn(ratio_note, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)

        self.wait(2.0)
