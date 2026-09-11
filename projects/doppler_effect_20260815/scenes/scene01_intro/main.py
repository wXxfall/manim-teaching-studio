"""scene01 开场:救护车鸣笛驶近音调变高、驶离变低,1842 预言 / 1845 实验验证.

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


def make_ambulance() -> VGroup:
    """程序化救护车侧视图(车头朝右,预览注解「重画一版」):
    白色车身 + 蓝色急救条 + 驾驶室窗 + 红十字 + 警灯辉光 + 双轮毂车轮。"""
    body = RoundedRectangle(width=2.8, height=0.95, corner_radius=0.3, color=WHITE_, stroke_width=3)
    cabin = Rectangle(width=1.05, height=0.6, color=WHITE_, stroke_width=3)
    cabin.move_to(body.get_center() + RIGHT * 0.55 + UP * 0.3)
    cross_v = Rectangle(width=0.13, height=0.46, color=ERR, fill_color=ERR, fill_opacity=1.0, stroke_width=0)
    cross_h = Rectangle(width=0.46, height=0.13, color=ERR, fill_color=ERR, fill_opacity=1.0, stroke_width=0)
    cross = VGroup(cross_v, cross_h).move_to(body.get_center() + LEFT * 0.78)
    lamp = RoundedRectangle(width=0.34, height=0.18, corner_radius=0.07,
                            color=ACCENT, fill_color=ACCENT, fill_opacity=1.0, stroke_width=0)
    lamp.move_to(body.get_top() + UP * 0.13)
    wheel_l = Circle(radius=0.17, color=WHITE_, stroke_width=3)
    wheel_l.move_to(body.get_bottom() + LEFT * 0.6 + DOWN * 0.15)
    wheel_r = wheel_l.copy().move_to(body.get_bottom() + RIGHT * 0.6 + DOWN * 0.15)
    stripe = Rectangle(width=1.7, height=0.16, color=COL_A, fill_color=COL_A, fill_opacity=0.9, stroke_width=0)
    stripe.move_to(body.get_center() + LEFT * 0.15 + DOWN * 0.12)
    win = Rectangle(width=0.82, height=0.34, color=COL_B, fill_color=COL_B, fill_opacity=0.5, stroke_width=2)
    win.move_to(cabin.get_center() + RIGHT * 0.05 + UP * 0.03)
    glow = Annulus(inner_radius=0.09, outer_radius=0.24, color=ACCENT, fill_opacity=0.25, stroke_width=0)
    glow.move_to(lamp.get_center())
    hub_l = Circle(radius=0.05, color=WHITE_, fill_color=WHITE_, fill_opacity=1.0, stroke_width=0)
    hub_l.move_to(wheel_l.get_center())
    hub_r = hub_l.copy().move_to(wheel_r.get_center())
    return VGroup(body, cabin, cross, lamp, wheel_l, wheel_r, stripe, win, glow, hub_l, hub_r)


def pitch_waves(center: np.ndarray, side: int, n: int, dr: float, r0: float, color) -> VGroup:
    """音波示意弧组:side=1 朝右(驶近),side=-1 朝左(驶离);dr 是弧间距(小=波密)。"""
    arcs = VGroup()
    for i in range(n):
        r = r0 + i * dr
        if side > 0:
            arc = Arc(radius=r, start_angle=-PI / 3, angle=2 * PI / 3, color=color, stroke_width=3)
        else:
            arc = Arc(radius=r, start_angle=2 * PI / 3, angle=2 * PI / 3, color=color, stroke_width=3)
        arc.shift(center)
        arcs.add(arc)
    return arcs


class IntroScene(Scene):
    """开场:现象对比(驶近音高 / 驶离音低)+ 历史一笔。"""

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR

        # ==== Phase 1: 标题 ====
        title_cn = Text("多普勒效应", font=CJK_FONT, font_size=46, color=WHITE_).set_name("标题·中文")
        title_en = Text("Doppler Effect", font=FONT, font_size=30, color=WHITE_).set_opacity(0.55).set_name("标题·英文")
        title = VGroup(title_cn, title_en).arrange(RIGHT, buff=0.4, aligned_edge=DOWN).to_edge(UP, buff=0.35)
        title.move_to([0, title_cn.get_y(), 0])  # to_edge(UP) 只改 Y,水平居中必须显式
        title_cn.shift(UP * 0.5)  # 预览注解:中文标题上移 0.5
        title_en.shift(LEFT * 1.73 + DOWN * 1.12)  # 预览注解:拖拽移动

        self.play(FadeIn(title_cn, shift=DOWN * 0.3), run_time=1.0)
        self.wait(1.2)
        self.play(FadeIn(title_en, shift=DOWN * 0.3), run_time=0.8)
        self.wait(1.4)

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

        # ==== Phase 3: 救护车 + 音调高低示意 ====
        ambulance = make_ambulance().move_to([0, -0.45, 0]).set_name("救护车")
        ambulance.shift(LEFT * 0.13 + UP * 0.03)  # 预览注解:拖拽移动
        siren = ambulance[3].get_center()  # 警灯中心 = 声源点

        self.play(FadeIn(ambulance, shift=UP * 0.2), run_time=1.5)
        self.wait(1.0)

        # 驶近一侧(右):波密音高;驶离一侧(左):波疏音低
        waves_high = pitch_waves(siren, +1, n=6, dr=0.28, r0=0.55, color=ERR).set_name("驶近音波·高")
        waves_high.shift(RIGHT * 0.1 + DOWN * 1.25)  # 预览注解:拖拽移动
        waves_low = pitch_waves(siren, -1, n=3, dr=0.85, r0=0.55, color=GREEN_A).set_name("驶离音波·低")
        waves_low.shift(LEFT * 0.13 + DOWN * 0.9)  # 预览注解:拖拽移动
        self.play(Create(waves_high), Create(waves_low), run_time=1.4)
        self.wait(1.0)

        lab_high = Text("驶近 · 音调高", font=CJK_FONT, font_size=22, color=ERR)
        lab_high.next_to(waves_high, RIGHT, buff=0.25).shift(DOWN * 0.1).set_name("标注·驶近")
        lab_high.shift(LEFT * 0.02 + DOWN * 0.57)  # 预览注解:拖拽移动
        lab_low = Text("驶离 · 音调低", font=CJK_FONT, font_size=22, color=GREEN_A)
        lab_low.next_to(waves_low, LEFT, buff=0.25).shift(DOWN * 0.1).set_name("标注·驶离")
        lab_low.shift(LEFT * 0.37 + DOWN * 0.4)  # 预览注解:拖拽移动
        self.play(FadeIn(lab_high, shift=UP * 0.15), FadeIn(lab_low, shift=UP * 0.15), run_time=1.0)
        self.wait(1.0)

        # ==== Phase 4: 历史一笔 ====
        note = Text(
            "1842 多普勒预言 · 1845 Buys Ballot 用火车与号手验证",
            font=CJK_FONT, font_size=20, color=WHITE_,
        ).set_opacity(0.75).to_edge(DOWN, buff=0.35).set_name("历史注释")

        self.play(FadeIn(note, shift=UP * 0.2), run_time=1.2)
        self.wait(1.0)

        # 结尾留白(shot_table wait 预算内)
        self.wait(3.2)
