"""scene04 分子指纹:三种物质特征谱线 + 拉曼/红外选律互补 + 应用卡片.

Run:
    MANIM_LOW_RES=1 manim -pql main.py FingerprintScene    # 低清预览(画面审查用)
    manim -pqh main.py FingerprintScene                    # 1080p60 高清成片
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


def make_peak_axes(peak_x: float, height: float = 0.85, x_span: float = 240.0) -> Axes:
    """单峰谱图小坐标系(数据坐标:波数偏移)."""
    return Axes(
        x_range=[peak_x - x_span, peak_x + x_span, x_span / 2],
        y_range=[0, 1.0, 0.5],
        x_length=2.5, y_length=1.5,
        axis_config={"color": WHITE_, "stroke_width": 1.5, "include_ticks": False},
    )


class FingerprintScene(Scene):
    """指纹谱线(金刚石/石墨/硅)+ 拉曼与红外选律互补 + 应用(demo 型)。"""

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR

        # ==== Phase 0: 标题 ====
        title_cn = Text("分子指纹", font=CJK_FONT, font_size=42, color=WHITE_)
        title_en = Text("Molecular Fingerprint", font=FONT, font_size=28, color=WHITE_).set_opacity(0.55)
        title = VGroup(title_cn, title_en).arrange(RIGHT, buff=0.4, aligned_edge=DOWN).to_edge(UP, buff=0.25)
        title.move_to([0, title_cn.get_y(), 0])
        self.play(FadeIn(title_cn, shift=DOWN * 0.3), run_time=0.8)
        self.play(FadeIn(title_en, shift=DOWN * 0.3), run_time=0.6)
        self.wait(0.5)

        intro = Text(
            "每种分子有自己的一组振动模,于是有自己的一组谱线——像指纹",
            font=CJK_FONT, font_size=20, color=WHITE_,
        ).move_to([0, 2.35, 0])
        self.play(FadeIn(intro, shift=UP * 0.15), run_time=1.0)
        self.wait(0.8)

        # ==== Phase 1: 三列指纹谱图(左侧;右列与选律面板留间隙)====
        cols_x = [-4.7, -1.8, 1.1]
        specs = [
            ("金刚石", 1332, ACCENT, "sp³ 碳", 4.0),
            ("石墨 G 峰", 1580, GREEN_A, "sp² 碳", 3.2),
            ("单晶硅", 520, COL_A, "晶格振动", 3.5),
        ]
        peak_axes = []
        for i, (name, peak, color, note, sigma) in enumerate(specs):
            ax = make_peak_axes(float(peak)).move_to([cols_x[i], 0.55, 0])
            curve = ax.plot(
                lambda x, s=sigma, p=peak: 0.85 * np.exp(-(((x - p) / s) ** 2) / 2),
                color=color, stroke_width=5,
            )
            name_lab = Text(name, font=CJK_FONT, font_size=20, color=color).next_to(ax, UP, buff=0.15)
            value_lab = MathTex(rf"{peak}\,\mathrm{{cm}}^{{-1}}", color=WHITE_).scale(0.75).next_to(ax, DOWN, buff=0.18)
            note_lab = Text(note, font=CJK_FONT, font_size=14, color=WHITE_).set_opacity(0.6).next_to(value_lab, DOWN, buff=0.1)
            group = VGroup(ax, curve, name_lab, value_lab, note_lab)
            peak_axes.append(group)
            self.play(FadeIn(ax), FadeIn(name_lab), run_time=0.8)
            self.play(Create(curve), FadeIn(value_lab), FadeIn(note_lab), run_time=1.0)
            self.wait(0.5)

        fingerprint_note = Text(
            "同样的碳原子,结构不同,指纹就不同",
            font=CJK_FONT, font_size=18, color=WHITE_,
        ).set_opacity(0.75).move_to([-2.9, -1.55, 0])
        self.play(FadeIn(fingerprint_note, shift=UP * 0.15), run_time=1.0)
        self.wait(0.6)

        # ==== Phase 2: 选律面板(右侧;面板下移缩高,标题避开 intro 行)====
        panel = RoundedRectangle(width=4.4, height=3.0, corner_radius=0.12, color=WHITE_, stroke_width=2).move_to([4.7, 0.15, 0])
        panel_title = Text("谁能在光谱里露面", font=CJK_FONT, font_size=22, color=ACCENT).next_to(panel, UP, buff=0.15)
        # 面板内四元素用绝对 y 坐标硬排(next_to 相对定位在中文渲染下间距不足,曾与公式重叠)
        eq_raman = MathTex(r"\left(\frac{\partial\alpha}{\partial Q}\right)_0 \neq 0", color=WHITE_).scale(0.85).move_to([4.7, 0.85, 0])
        eq_raman_lab = Text("拉曼活性:振动时极化率在变", font=CJK_FONT, font_size=18, color=WHITE_).move_to([4.7, 0.3, 0])
        eq_ir = MathTex(r"\left(\frac{\partial\mu}{\partial Q}\right)_0 \neq 0", color=WHITE_).scale(0.85).move_to([4.7, -0.3, 0])
        eq_ir_lab = Text("红外活性:振动时偶极矩在变", font=CJK_FONT, font_size=18, color=WHITE_).move_to([4.7, -0.85, 0])

        self.play(FadeIn(panel), FadeIn(panel_title), run_time=0.8)
        self.play(FadeIn(eq_raman, shift=UP * 0.15), FadeIn(eq_raman_lab), run_time=1.2)
        self.wait(0.8)
        self.play(FadeIn(eq_ir, shift=UP * 0.15), FadeIn(eq_ir_lab), run_time=1.2)
        self.wait(0.6)

        # N₂ 示例:互补(两行,panel 下方,不超画布右缘)
        n2_note = VGroup(
            Text("同核双原子分子 N₂:偶极矩始终为零 → 红外静默", font=CJK_FONT, font_size=13, color=GREEN_A),
            Text("但极化率在变 → 拉曼可见", font=CJK_FONT, font_size=13, color=GREEN_A),
        ).arrange(DOWN, buff=0.1).move_to([4.7, -1.95, 0])
        self.play(FadeIn(n2_note, shift=UP * 0.15), run_time=1.2)
        self.wait(1.0)

        # ==== Phase 3: 应用卡片(左移,与右侧 app_note 留间隙)====
        apps = VGroup(
            Text("钻石鉴定", font=CJK_FONT, font_size=18, color=WHITE_),
            Text("石墨烯质量", font=CJK_FONT, font_size=18, color=WHITE_),
            Text("活细胞检测", font=CJK_FONT, font_size=18, color=WHITE_),
        ).arrange(RIGHT, buff=1.6).to_edge(DOWN, buff=0.45)
        cards = VGroup()
        for a in apps:
            card = RoundedRectangle(width=2.0, height=0.75, corner_radius=0.12, color=COL_B, stroke_width=1.5)
            a.move_to(card.get_center())
            cards.add(VGroup(card, a))
        cards.arrange(RIGHT, buff=0.5).move_to([-1.5, -2.9, 0])
        app_note = Text("一束绿光,无需标记,指纹立现", font=CJK_FONT, font_size=20, color=WHITE_).move_to([4.0, -2.9, 0])
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in cards], lag_ratio=0.3), run_time=1.6)
        self.play(FadeIn(app_note, shift=UP * 0.2), run_time=1.0)
        self.wait(0.8)

        self.wait(2.5)
