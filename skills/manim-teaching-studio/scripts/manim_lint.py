"""场景代码静态规范检查(不执行代码,正则+括号配对).

Run:
    python manim_lint.py lint <project_path> [--spec <spec_lock.md>] [--json]

检查项(error 级,rc!=0):
    ① config 三行缺失(pixel_height/pixel_width/frame_rate)
    ② 硬编码 HEX 颜色不在 spec_lock ## colors 白名单
    ③ 中文 Text 调用缺 font= 参数
    ④ 文件头 docstring 缺 "Run:" 运行命令
    ⑤ construct() 内未设置背景色
    ⑥ 未 import manim
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HEX_RE = re.compile(r"#[0-9a-fA-F]{6}\b")
TEXT_RE = re.compile(r"Text\(\s*(?:r?f?)([\"'])(.*?)\1", re.DOTALL)
CJK_RE = re.compile(r"[一-鿿]")
CONFIG_RE = re.compile(r"config\.(pixel_height|pixel_width|frame_rate)")
DOC_RE = re.compile(r"\bRun:\s*\n\s*(?:MANIM_LOW_RES=1\s+)?manim", re.MULTILINE)

try:  # Windows 控制台 GBK 与 UTF-8 管道兼容
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass


def find_matching_paren(text: str, open_idx: int) -> int:
    """返回与 text[open_idx] 的 '(' 配对的 ')' 位置(无则 -1)."""
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def parse_hex_whitelist(spec_path: Path) -> set[str]:
    """从 spec_lock.md ## colors 节收集白名单 HEX."""
    whitelist: set[str] = set()
    if not spec_path or not spec_path.exists():
        return whitelist
    in_colors = False
    for line in spec_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_colors = line.strip() == "## colors"
            continue
        if in_colors and line.startswith("- "):
            for m in HEX_RE.findall(line):
                whitelist.add(m.upper())
    return whitelist


def lint_file(path: Path, hex_whitelist: set[str]) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    errors: list[dict] = []

    def err(rule: str, msg: str, line: int) -> None:
        errors.append({"file": str(path), "rule": rule, "line": line, "msg": msg, "level": "error"})

    # ⑥ import manim
    if not re.search(r"^\s*(from manim import|import manim)", text, re.MULTILINE):
        err("import-manim", "未 import manim", 1)

    # ① config 三行
    for key in ("pixel_height", "pixel_width", "frame_rate"):
        if not re.search(rf"config\.{key}\s*=", text):
            err("config", f"缺 config.{key} 行(env-gate 三行)", 1)

    # ② 硬编码 HEX
    if hex_whitelist:
        for m in HEX_RE.finditer(text):
            hexv = m.group(0).upper()
            if hexv not in hex_whitelist:
                line = text[: m.start()].count("\n") + 1
                err("hardcoded-color", f"硬编码颜色 {hexv} 不在 spec_lock ## colors 白名单", line)

    # ③ 中文 Text 缺 font=
    for m in TEXT_RE.finditer(text):
        inner = m.group(2)
        if not CJK_RE.search(inner):
            continue
        call_end = find_matching_paren(text, m.end())
        if call_end == -1:
            continue
        call = text[m.start():call_end + 1]
        if "font=" not in call:
            line = text[: m.start()].count("\n") + 1
            err("cjk-font", "中文 Text 调用缺 font=CJK_FONT 参数", line)

    # ④ docstring 缺 Run 命令
    if not DOC_RE.search(text):
        err("docstring", "文件头 docstring 缺 Run: 运行命令", 1)

    # ⑤ construct 背景色
    m = re.search(r"def\s+construct\s*\(", text)
    if m:
        body = text[m.end():m.end() + 1500]
        if "background_color" not in body:
            err("bg-color", "construct() 内未设置 camera.background_color", text[: m.start()].count("\n") + 1)
    else:
        err("construct", "未找到 construct() 方法", 1)

    return errors


def lint_project(root: Path, spec_path: Path | None) -> tuple[list[dict], list[dict]]:
    scenes_dir = root / "scenes"
    files = sorted(scenes_dir.glob("scene*/main.py")) if scenes_dir.exists() else []
    whitelist = parse_hex_whitelist(spec_path) if spec_path else set()
    errors, warnings = [], []
    if not files:
        errors.append({"file": str(scenes_dir), "rule": "no-scenes", "line": 0,
                       "msg": "scenes/ 下没有任何 scene*/main.py", "level": "error"})
    for f in files:
        for e in lint_file(f, whitelist):
            (errors if e["level"] == "error" else warnings).append(e)
    return errors, warnings


def main() -> None:
    if len(sys.argv) < 3 or sys.argv[1] != "lint":
        print(__doc__)
        sys.exit(1)
    root = Path(sys.argv[2]).resolve()
    spec_path: Path | None = None
    use_json = "--json" in sys.argv
    if "--spec" in sys.argv:
        i = sys.argv.index("--spec")
        spec_path = Path(sys.argv[i + 1]).resolve()

    errors, warnings = lint_project(root, spec_path)
    if use_json:
        print(json.dumps({"errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
    else:
        for e in errors:
            print(f"[ERROR] {e['file']}:{e['line']}  {e['msg']}")
        for w in warnings:
            print(f"[WARN ] {w['file']}:{w['line']}  {w['msg']}")
        print(f"\n检查 {len(errors) + len(warnings)} 项:error {len(errors)},warning {len(warnings)}")
        print("✅ 0 error" if not errors else "❌ 存在 error,修复后再继续")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
