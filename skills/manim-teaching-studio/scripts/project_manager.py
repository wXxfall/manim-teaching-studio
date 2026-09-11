"""项目工作区管理:init / validate / status.

Run:
    python project_manager.py init <slug>
    python project_manager.py validate <project_path>
    python project_manager.py status <project_path>
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROJECTS = REPO_ROOT / "projects"

try:  # Windows 控制台 GBK 与 UTF-8 管道兼容
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

SCENE_SKELETON = '''"""场景名 — 一句话描述.

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
WHITE_ = "#ffffff"
COL_A = "#58b9ff"
COL_B = "#8be9fd"
ACCENT = "#ffd866"
ERR = "#ff6188"
GREEN_A = "#a6e22e"

FONT = "Segoe UI"
CJK_FONT = "Microsoft YaHei"


class SceneClassName(Scene):
    """场景 docstring:本场景的教学目标。"""

    def construct(self) -> None:
        self.camera.background_color = BG_COLOR

        title_cn = Text("标题", font=CJK_FONT, font_size=42, color=WHITE_)
        title = title_cn.to_edge(UP, buff=0.3).move_to([0, title_cn.get_y(), 0])
        self.play(FadeIn(title, shift=DOWN * 0.3), run_time=1.0)
        self.wait(1.0)
'''

DIRS = [
    "sources", "scenes", "prototypes", "legacy",
    "docs/scripts", "docs/review", "output", "backup",
    "render_log", "media",
]

REQUIRED_FILES = [
    "design_spec.md",
    "spec_lock.md",
    "docs/scripts/narration.md",
    "docs/scripts/shot_table.md",
]


def init_project(slug: str) -> Path:
    """创建 projects/<slug>_<YYYYMMDD>/ 骨架."""
    stamp = datetime.now().strftime("%Y%m%d")
    root = PROJECTS / f"{slug}_{stamp}"
    if root.exists():
        print(f"[错误] 已存在:{root}")
        sys.exit(1)
    for d in DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / "scenes" / "scene01_intro" / "main.py").parent.mkdir(parents=True)
    (root / "scenes" / "scene01_intro" / "main.py").write_text(SCENE_SKELETON, encoding="utf-8")
    (root / "README.md").write_text(
        f"# {slug}({stamp})\n\n由 project_manager.py 生成。\n"
        f"- 设计书:design_spec.md(策略师 Step 2 产出)\n"
        f"- 执行契约:spec_lock.md(策略师 Step 2 产出)\n"
        f"- 教学脚本:docs/scripts/(Step 3 产出)\n"
        f"- 场景代码:scenes/sceneXX_xxx/main.py(Step 5 产出)\n"
        f"- 审查报告:docs/review/(Step 4/6/8 产出)\n"
        f"- 成品视频:output/(Step 9 产出)\n",
        encoding="utf-8",
    )
    print(f"[完成] 已创建 {root}")
    print("       next: 策略师阶段(九项确认单 → design_spec.md + spec_lock.md)")
    return root


def validate_project(root: Path) -> bool:
    """供 resume-execute 分屏续跑做 sanity check."""
    ok = True
    for f in REQUIRED_FILES:
        if not (root / f).exists():
            print(f"[缺失] {root / f}")
            ok = False
    if ok:
        print(f"[通过] {root} 双 spec + 脚本齐备,可进入 Phase B(写代码)")
    return ok


def status_project(root: Path) -> None:
    """列产物状态表."""
    def mark(p: Path) -> str:
        return "✅" if p.exists() else "⬜"

    rows = [
        ("design_spec.md", mark(root / "design_spec.md")),
        ("spec_lock.md", mark(root / "spec_lock.md")),
        ("教学脚本 narration.md", mark(root / "docs/scripts/narration.md")),
        ("分镜预算 shot_table.md", mark(root / "docs/scripts/shot_table.md")),
        ("科学审查报告", mark(root / "docs/review/science_review.md")),
        ("画面审查报告", mark(root / "docs/review/visual_review.md")),
        ("时长报告", mark(root / "docs/review/duration_report.md")),
        ("输出视频", mark(root / "output") if any((root / "output").glob("*.mp4")) else "⬜"),
    ]
    print(f"== {root.name} ==")
    for name, m in rows:
        print(f"  {m} {name}")
    scenes = sorted((root / "scenes").glob("scene*")) if (root / "scenes").exists() else []
    print(f"  场景目录:{len(scenes)} 个")


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == "init":
        init_project(arg)
    else:
        root = Path(arg).resolve()
        if not root.exists():
            print(f"[错误] 目录不存在:{root}")
            sys.exit(1)
        if cmd == "validate":
            sys.exit(0 if validate_project(root) else 1)
        elif cmd == "status":
            status_project(root)
        else:
            print(__doc__)
            sys.exit(1)


if __name__ == "__main__":
    main()
