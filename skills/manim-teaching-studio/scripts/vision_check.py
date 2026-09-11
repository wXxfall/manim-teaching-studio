"""调用火山方舟(豆包)视觉 API 检查 manim 渲染帧(画面审查).

Run:
    python vision_check.py check <image_path> ["附加检查要求"] [--out report.md] [--model X]

API key 查找链(不硬编码):
    环境变量 ARK_API_KEY → 脚本 cwd/.env → 仓库根 .env → ~/.manim-teaching-studio/.env
模型默认 ARK_MODEL 环境变量或 .env,回退 doubao-seed-2-0-mini-260428。
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
DEFAULT_MODEL = "doubao-seed-2-0-mini-260428"
REPO_ROOT = Path(__file__).resolve().parents[3]

try:  # Windows 控制台 GBK 与 UTF-8 管道兼容
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

FIXED_PROMPT = (
    "这是一张科学教学动画(Manim 渲染)的截图。请仔细检查并用中文逐条回答:\n"
    "1. 画面整体布局是否平衡?是否有元素重叠或互相遮挡?\n"
    "2. 图中每个小图/分面板内:坐标轴、曲线、填充图形、说明文字是否清晰可辨?不同系列颜色是否分明?\n"
    "3. 面板元素(标题、公式、色点+标签+条形+数值)是否对齐?是否溢出面板边界?\n"
    "4. 任何元素是否被画布边缘裁剪?\n"
    "5. 是否有文字过小难以阅读?\n"
    "6. 顶部标题是否完整显示?\n"
    "7. 公式(LaTeX 渲染)是否出现错乱、缺字、符号重叠?\n"
    "没有问题的条目直接说\"正常\",有问题的指出具体位置和表现。"
)


def load_env() -> dict[str, str]:
    """查找链:环境变量 → cwd/.env → 仓库根 .env → ~/.manim-teaching-studio/.env."""
    env: dict[str, str] = {}
    candidates = [
        Path.cwd() / ".env",
        REPO_ROOT / ".env",
        Path.home() / ".manim-teaching-studio" / ".env",
    ]
    for p in candidates:
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env.setdefault(k.strip(), v.strip())
    env.update({k: v for k, v in os.environ.items() if k.startswith("ARK_")})
    return env


def check(image_path: str, extra: str = "", out: str | None = None, model: str | None = None) -> str:
    env = load_env()
    api_key = env.get("ARK_API_KEY", "")
    if not api_key:
        sys.exit("[错误] 未找到 ARK_API_KEY。配置方法见项目 README「API Key 配置」章节。")
    model = model or env.get("ARK_MODEL") or DEFAULT_MODEL

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    prompt = FIXED_PROMPT + ("\n额外要求:" + extra if extra else "")

    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"}},
            ],
        }],
        "max_tokens": 4096,
        "temperature": 0.1,
    }
    last_err = ""
    for attempt in (1, 2):
        try:
            req = urllib.request.Request(
                API_URL,
                data=json.dumps(payload).encode(),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode())
            result = data["choices"][0]["message"]["content"]
            if out:
                Path(out).write_text(result, encoding="utf-8")
            print(result)
            return result
        except Exception as e:  # noqa: BLE001
            last_err = str(e)
            if attempt == 1:
                time.sleep(3)
    sys.exit(f"[错误] 调用失败(重试 1 次后):{last_err}")


def main() -> None:
    if len(sys.argv) < 3 or sys.argv[1] != "check":
        print(__doc__)
        sys.exit(1)
    image = sys.argv[2]
    extra, out, model = "", None, None
    for i, arg in enumerate(sys.argv[3:], start=3):
        if arg == "--out" and i + 1 < len(sys.argv):
            out = sys.argv[i + 1]
        elif arg == "--model" and i + 1 < len(sys.argv):
            model = sys.argv[i + 1]
        elif not arg.startswith("--") and i > 3 and not (sys.argv[i - 1] in ("--out", "--model")):
            extra = arg
    check(image, extra, out, model)


if __name__ == "__main__":
    main()
