"""从渲染好的 mp4 抽关键帧(画面审查用).

Run:
    python extract_frames.py extract <mp4> --out <dir> [--times 0.15,0.5,0.85]
    python extract_frames.py extract <mp4> --out <dir> --phases phase.json
    python extract_frames.py duration <mp4>          # 仅打印时长(秒)

--times:时间点比例(0~1)。--phases:JSON 文件,{"phases": [{"name": "phase1", "t": 8.0}]},t 为绝对秒。
输出命名:sceneXX_phaseN.jpg 或 sceneXX_t0.15.jpg。
时长通过解析 `ffmpeg -i` 的 stderr 获得(不依赖 ffprobe)。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ffmpeg 查找链:PATH → FFMPEG_DIR 环境变量(指向含 ffmpeg 的目录)
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


def ffprobe_duration(mp4: Path) -> float:
    """从 `ffmpeg -i` 的 stderr 解析 Duration(纯 ffmpeg 依赖)."""
    out = subprocess.run(
        [find_ffmpeg(), "-i", str(mp4)],
        capture_output=True, text=True,
    )
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", out.stderr)
    if not m:
        print(f"[错误] 无法解析时长:{out.stderr.strip()[:200] or mp4}")
        sys.exit(1)
    h, mnt, s = m.groups()
    return int(h) * 3600 + int(mnt) * 60 + float(s)


def extract(mp4: Path, out_dir: Path, times: list[tuple[str, float]], as_fraction: bool = False) -> None:
    ffmpeg = find_ffmpeg()
    out_dir.mkdir(parents=True, exist_ok=True)
    total = ffprobe_duration(mp4)
    print(f"视频时长:{total:.2f}s")
    for name, t in times:
        t_abs = t * total if as_fraction else t
        t_clamped = max(0.1, min(t_abs, max(0.1, total - 0.1)))
        out = out_dir / f"{name}.jpg"
        subprocess.run(
            [ffmpeg, "-y", "-ss", f"{t_clamped:.2f}", "-i", str(mp4), "-frames:v", "1", "-q:v", "2", str(out)],
            capture_output=True,
        )
        print(f"  {out.name}  <- t={t_clamped:.2f}s {'✅' if out.exists() else '❌'}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "duration":
        print(f"{ffprobe_duration(Path(sys.argv[2])):.2f}")
        return
    if cmd != "extract" or len(sys.argv) < 5:
        print(__doc__)
        sys.exit(1)
    mp4 = Path(sys.argv[2]).resolve()
    out_dir = Path(sys.argv[4]).resolve()
    times: list[tuple[str, float]] = []
    as_fraction = True
    if "--times" in sys.argv:
        i = sys.argv.index("--times")
        for j, v in enumerate(sys.argv[i + 1].split(",")):
            times.append((f"t{v}", float(v)))
    elif "--phases" in sys.argv:
        i = sys.argv.index("--phases")
        data = json.loads(Path(sys.argv[i + 1]).read_text(encoding="utf-8"))
        for p in data.get("phases", []):
            times.append((p["name"], float(p["t"])))
        as_fraction = False
    else:
        times = [("t0.25", 0.25), ("t0.5", 0.5), ("t0.85", 0.85)]
    extract(mp4, out_dir, times, as_fraction=as_fraction)


if __name__ == "__main__":
    main()
