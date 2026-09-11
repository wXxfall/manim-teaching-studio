"""成品收集与交付:编号复制 + 可选合并成片 + 源码备份.

Run:
    python make_video.py <project_path> [--merged] [--quality 1080p60]

按 spec_lock.md ## scenes 的场景顺序,从 scenes/<dir>/media/videos/main/<quality>/<Class>.mp4
复制到 output/<NN>_<dir>.mp4;--merged 时 ffmpeg concat 拼接 output/<slug>_final.mp4 并打印总时长;
同时把源码(scenes/*.py、双 spec、docs/)存档到 backup/<timestamp>/。
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

try:  # Windows 控制台 GBK 与 UTF-8 管道兼容
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass


def find_ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    ff_dir = os.environ.get("FFMPEG_DIR")
    if ff_dir and (Path(ff_dir) / "ffmpeg.exe").exists():
        return str(Path(ff_dir) / "ffmpeg.exe")
    print("[错误] 未找到 ffmpeg:请加入 PATH,或设置环境变量 FFMPEG_DIR 指向含 ffmpeg 的目录")
    sys.exit(1)


def parse_scenes(spec: Path) -> list[tuple[str, str, str]]:
    """返回 [(sceneNN, dir, class), ...]."""
    scenes = []
    in_scenes = False
    for line in spec.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_scenes = line.strip() == "## scenes"
            continue
        if in_scenes and line.startswith("- scene"):
            key = line.split(":")[0].replace("- ", "").strip()
            m_dir = line[line.find("dir=") + 4:].split(",")[0].strip()
            m_cls = line[line.find("class=") + 6:].split(",")[0].strip()
            scenes.append((key, m_dir, m_cls))
    return scenes


def ffprobe_duration(mp4: Path) -> float:
    """从 `ffmpeg -i` 的 stderr 解析 Duration(不依赖 ffprobe)."""
    out = subprocess.run(
        [find_ffmpeg(), "-i", str(mp4)],
        capture_output=True, text=True,
    )
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", out.stderr)
    if not m:
        return 0.0
    h, mnt, s = m.groups()
    return int(h) * 3600 + int(mnt) * 60 + float(s)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    project = Path(sys.argv[1]).resolve()
    merged = "--merged" in sys.argv
    quality = sys.argv[sys.argv.index("--quality") + 1] if "--quality" in sys.argv else "1080p60"
    spec = project / "spec_lock.md"
    if not spec.exists():
        print(f"[错误] 未找到 {spec}")
        sys.exit(1)

    scenes = parse_scenes(spec)
    output = project / "output"
    output.mkdir(exist_ok=True)
    final_files: list[Path] = []
    total = 0.0

    for key, sdir, scls in scenes:
        src = project / "scenes" / sdir / "media" / "videos" / "main" / quality / f"{scls}.mp4"
        if not src.exists():
            print(f"[警告] {key} 缺 {src}(请先渲染)")
            continue
        dst = output / f"{key}_{sdir}.mp4"
        shutil.copy2(src, dst)
        dur = ffprobe_duration(dst)
        total += dur
        final_files.append(dst)
        print(f"  {dst.name}  {dur:.2f}s")

    print(f"分场景合计:{total:.2f}s")

    if merged and final_files:
        ffmpeg = find_ffmpeg()
        concat_list = project / "render_log" / "concat_list.txt"
        concat_list.parent.mkdir(exist_ok=True)
        concat_list.write_text(
            "\n".join(f"file '{f.as_posix()}'" for f in final_files), encoding="utf-8",
        )
        final = output / f"{project.name}_final.mp4"
        subprocess.run(
            [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(final)],
            capture_output=True,
        )
        final_dur = ffprobe_duration(final)
        print(f"[合并] {final.name}  {final_dur:.2f}s")

    # 源码备份
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = project / "backup" / stamp
    backup.mkdir(parents=True)
    for item in ["design_spec.md", "spec_lock.md", "docs"]:
        src = project / item
        if src.exists():
            if src.is_dir():
                shutil.copytree(src, backup / item)
            else:
                shutil.copy2(src, backup / item)
    scenes_bak = backup / "scenes"
    scenes_bak.mkdir()
    for py in (project / "scenes").rglob("*.py"):
        rel = py.relative_to(project / "scenes")
        (scenes_bak / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(py, scenes_bak / rel)
    print(f"[备份] {backup}")


if __name__ == "__main__":
    main()
