"""preview/server.py — Manim Teaching Studio 交互式画面预览服务器(复刻 ppt-master svg_editor 模式).

在浏览器里展示 scene_probe.py 生成的节点静帧,画布上每个元素可点击选中;
右侧边栏提供 位置/颜色/深浅/大小/时长/字号/层级 控件;底部"回炉重造"文本框
收集结构操作 + 自由文本,提交后落盘 <project>/docs/review/rework/request.json。
服务器不调用任何 AI;用户回对话说"应用修改",由主代理消费 request.json 改码。

Run:
    python preview/server.py <project_path> [--port 5051] [--no-browser] [--timeout 7200]

单实例:<project>/.live_preview.lock 记录 pid + 端口;端口默认 5051(避开 ppt-master 的 5050)。
前端每 2 秒轮询 /api/slides,发现 elements.json mtime 变化弹出刷新横幅(复刻 ppt-master)。
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

try:  # Windows 控制台 GBK 与 UTF-8 兼容
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

HERE = Path(__file__).resolve().parent
STATIC_DIR = HERE / "static"
DEFAULT_PORT = 5051
DEFAULT_TIMEOUT = 7200


def find_project(argv: list[str]) -> Path:
    p = argparse.ArgumentParser(description="Manim Teaching Studio 交互式画面预览服务器")
    p.add_argument("project", help="项目目录路径(如 projects/xxx_20260101)")
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--no-browser", action="store_true")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="空闲秒数后自动退出,0 禁用")
    args = p.parse_args(argv)
    project = Path(args.project).resolve()
    if not project.exists():
        raise SystemExit(f"[错误] 项目不存在:{project}")
    return args, project


def lock_path(project: Path) -> Path:
    return project / ".live_preview.lock"


def read_lock(project: Path) -> dict | None:
    lp = lock_path(project)
    if not lp.exists():
        return None
    try:
        return json.loads(lp.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def is_port_alive(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.3):
            return True
    except OSError:
        return False


def rework_path(project: Path) -> Path:
    return project / "docs/review/rework/request.json"


class PreviewServer:
    def __init__(self, project: Path):
        self.project = project
        self.preview_root = project / "docs/review/preview"
        self.app = Flask("manim-preview", static_folder=None)
        self._routes()
        self._last_activity = time.time()

    # ---------- 路由 ----------
    def _routes(self) -> None:
        app = self.app
        project = self.project

        @app.get("/")
        def index():
            return send_from_directory(STATIC_DIR, "index.html")

        @app.get("/static/<path:name>")
        def static_files(name: str):
            return send_from_directory(STATIC_DIR, name)

        @app.get("/preview/<scene>/<path:name>")
        def preview_files(scene: str, name: str):
            base = (self.preview_root / scene).resolve()
            target = (base / name).resolve()
            if base not in target.parents and target != base:
                return jsonify({"error": "非法路径"}), 403
            return send_from_directory(base, name)

        @app.get("/videos/<scene>/<name>")
        def video_files(scene: str, name: str):
            """低清渲染视频(总预览连续播放用;conditional=True 支持 Range 拖动进度)。"""
            safe_scene = "".join(c for c in scene if c.isalnum() or c in "_-")
            safe_name = "".join(c for c in name if c.isalnum() or c in "._-")
            if safe_scene != scene or safe_name != name:
                return jsonify({"error": "非法路径"}), 403
            base = (project / "scenes" / scene / "media/videos/main/480p15").resolve()
            target = (base / name).resolve()
            if base not in target.parents and target != base:
                return jsonify({"error": "非法路径"}), 403
            return send_from_directory(base, name, conditional=True)

        @app.get("/api/config")
        def api_config():
            self._touch()
            return jsonify({
                "project": project.name,
                "project_path": str(project),
                "scenes": self._load_index(),
            })

        @app.get("/api/slides")
        def api_slides():
            self._touch()
            return jsonify({"scenes": self._load_index()})

        @app.get("/api/scene/<scene>")
        def api_scene(scene: str):
            self._touch()
            data = self._load_elements(scene)
            if data is None:
                return jsonify({"error": f"场景 {scene} 无探针数据"}), 404
            return jsonify(data)

        @app.get("/api/rework")
        def api_rework_get():
            self._touch()
            return jsonify(self._load_rework())

        @app.post("/api/rework")
        def api_rework_post():
            """提交一个场景的修改:同场景重复提交 = 覆盖该场景条目,不同场景并列成队列。"""
            self._touch()
            body = request.get_json(silent=True) or {}
            scene = str(body.get("scene", ""))
            node = str(body.get("node", ""))
            ops = body.get("ops") or []
            free_text = str(body.get("free_text", "")).strip()
            targets = body.get("targets") or []
            if not scene or not (ops or free_text):
                return jsonify({"ok": False, "error": "缺少 scene 或内容"}), 400
            data = self._load_rework()
            items = [it for it in data.get("items", []) if it.get("scene") != scene]
            items.append({
                "scene": scene,
                "node": node,
                "created": datetime.now().isoformat(timespec="seconds"),
                "ops": [
                    {
                        "element": str(o.get("element", "")),
                        "op": str(o.get("op", "")),
                        **{k: o[k] for k in o if k not in ("element", "op")},
                        "note": str(o.get("note", "")),
                    }
                    for o in ops
                    if o.get("element")
                ],
                "free_text": free_text,
                "targets": [str(t) for t in targets],
            })
            rp = rework_path(project)
            rp.parent.mkdir(parents=True, exist_ok=True)
            rp.write_text(json.dumps({"pending": True, "items": items}, ensure_ascii=False, indent=2),
                          encoding="utf-8")
            return jsonify({"ok": True, "items": items, "path": str(rp)})

        @app.post("/api/rework/clear")
        def api_rework_clear():
            self._touch()
            rp = rework_path(project)
            scene = (request.args.get("scene") or "").strip()
            if scene:
                data = self._load_rework()
                items = [it for it in data.get("items", []) if it.get("scene") != scene]
                if items:
                    rp.parent.mkdir(parents=True, exist_ok=True)
                    rp.write_text(json.dumps({"pending": True, "items": items},
                                             ensure_ascii=False, indent=2), encoding="utf-8")
                elif rp.exists():
                    rp.unlink()
                return jsonify({"ok": True, "items": items})
            if rp.exists():
                rp.unlink()
            return jsonify({"ok": True, "items": []})

        @app.post("/api/shutdown")
        def api_shutdown():
            shutdown = request.environ.get("werkzeug.server.shutdown")
            if shutdown:
                shutdown()
                return jsonify({"ok": True})
            return jsonify({"ok": False, "error": "无法停止(非 werkzeug 运行)"}), 500

    # ---------- 数据加载 ----------
    def _touch(self) -> None:
        self._last_activity = time.time()

    def _load_index(self) -> list[dict]:
        idx = self.preview_root / "index.json"
        if not idx.exists():
            return []
        try:
            data = json.loads(idx.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return []
        scenes = []
        scenes_root = self.project / "scenes"
        for s in data.get("scenes", []):
            scene_dir = s.get("dir", "")
            elements_json = self.preview_root / scene_dir / "elements.json"
            mtime = elements_json.stat().st_mtime if elements_json.exists() else 0
            # 低清视频(总预览连续播放用)
            video = None
            cls = s.get("class", "")
            if scene_dir and cls:
                vf = scenes_root / scene_dir / "media/videos/main/480p15" / f"{cls}.mp4"
                if vf.exists():
                    video = f"/videos/{scene_dir}/{cls}.mp4"
            scenes.append({
                "dir": scene_dir,
                "class": cls,
                "duration": s.get("duration", 0),
                "nodes": s.get("nodes", 0),
                "error": s.get("error"),
                "elements_json": f"{scene_dir}/elements.json",
                "elements_mtime": mtime,
                "video": video,
            })
        return scenes

    def _load_elements(self, scene: str) -> dict | None:
        safe = "".join(c for c in scene if c.isalnum() or c in "_-")
        if safe != scene:
            return None
        f = self.preview_root / scene / "elements.json"
        if not f.exists():
            return None
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return None

    def _load_rework(self) -> dict:
        """读取待应用修改队列:{pending, items:[{scene, node, ops, free_text, targets, created}]}。"""
        rp = rework_path(self.project)
        if not rp.exists():
            return {"pending": False, "items": []}
        try:
            data = json.loads(rp.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {"pending": False, "items": []}
        items = data.get("items", [])
        return {"pending": bool(items), "items": items}

    # ---------- 运行 ----------
    def run(self, port: int, timeout: int, open_browser: bool) -> None:
        if timeout > 0:
            threading.Thread(target=self._idle_watch, args=(port, timeout), daemon=True).start()
        if open_browser:
            threading.Timer(1.2, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
        print(f"Manim 画面预览运行中 → http://127.0.0.1:{port}")
        print("点选元素 → 调右侧控件/写要求 → 提交修改 → 回到对话说「应用修改」")
        self.app.run(host="127.0.0.1", port=port, debug=False, threaded=True, use_reloader=False)

    def _idle_watch(self, port: int, timeout: int) -> None:
        while True:
            time.sleep(10)
            if time.time() - self._last_activity > timeout:
                print(f"[空闲超时 {timeout}s,自动退出]")
                try:
                    import urllib.request

                    urllib.request.urlopen(f"http://127.0.0.1:{port}/api/shutdown", timeout=2).read()
                except Exception:  # noqa: BLE001
                    os._exit(0)  # noqa: PLC3001


def main() -> None:
    args, project = find_project(sys.argv[1:])
    lp = read_lock(project)
    if lp and is_port_alive(int(lp.get("port", args.port))):
        print(f"[提示] 预览已在运行:http://127.0.0.1:{lp['port']}")
        return
    lock_path(project).write_text(
        json.dumps({"pid": os.getpid(), "port": args.port, "started": datetime.now().isoformat(timespec="seconds")}),
        encoding="utf-8",
    )
    try:
        PreviewServer(project).run(args.port, args.timeout, not args.no_browser)
    finally:
        lp2 = lock_path(project)
        if lp2.exists():
            lp2.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
