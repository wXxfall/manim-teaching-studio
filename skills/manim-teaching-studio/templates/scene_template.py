"""场景名 — 一句话描述.

Run:
    MANIM_LOW_RES=1 manim -pql main.py SceneClassName   # 低清预览(画面审查用)
    manim -pqh main.py SceneClassName                   # 1080p60 高清成片
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
WHITE_ = "#ffffff"  # 注意:不用 WHITE(与 manim 常量冲突)
COL_A = "#58b9ff"  # 主蓝(A 区 / 入射)
COL_B = "#8be9fd"  # 青(B 区 / 透射)
ACCENT = "#ffd866"  # 强调黄(结论 / 标题)
ERR = "#ff6188"  # 红(势垒 / 经典限制)
GREEN_A = "#a6e22e"  # 绿(透射 / 反射 / 对比)

FONT = "Segoe UI"  # 英文/公式
CJK_FONT = "Microsoft YaHei"  # 中文

# 透明度层级
OP_SUBTITLE = 0.55  # 副标题
OP_FADED = 0.35  # 推导中间步骤
OP_FILL = 0.18  # 区域填充


class SceneClassName(Scene):
    """场景类 docstring:一句话说明本场景的教学目标。

    时长预算:{N}s(spec_lock ## scenes 的 duration_budget)
    """

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR

        # ---- 标题 ----
        title_cn = Text("中文标题", font=CJK_FONT, font_size=42, color=WHITE_).set_name("中文标题")
        title_en = Text("English Title", font=FONT, font_size=28, color=WHITE_).set_opacity(OP_SUBTITLE).set_name("英文标题")
        title = VGroup(title_cn, title_en).arrange(RIGHT, buff=0.4, aligned_edge=DOWN).to_edge(UP, buff=0.3)
        self.play(FadeIn(title, shift=DOWN * 0.3), run_time=1.0)
        self.wait(0.5)

        # ==== Phase 1:xx ====
        # 每个将被动画引入的可见 mobject 都要 set_name("中文名")(画面预览点选元素用;
        # 探针优先 set_name、其次变量名;VGroup 容器不必命名,子元素逐个命名)。
        # 示例:
        # wave = DashedLine(...).set_name("入射波")
        # self.play(Create(wave), run_time=1.2)

        # ==== Phase 2:xx ====
        # ...

        self.wait(1.5)
