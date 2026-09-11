"""Manim 画面预览 · 启动器(浅色液态玻璃风格 GUI,可切换黑夜模式)

双击运行:弹出窗口 → 点击选择或拖入 manim 的 .py 文件 / 工程文件夹 → 点「分析」
→ 自动生成探针数据(元素入场后 1 秒节点图 + 元素坐标)→ 自动拉起预览服务器并打开浏览器。
支持:磁盘占用显示、刷新数据、删除数据、退出时提醒是否保留数据。

依赖:PySide6(pip install PySide6);未安装时自动降级为 tkinter 简化界面。
探针/服务器复用 skills/manim-teaching-studio 下的 scene_probe.py 与 preview/server.py。
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SKILL_SCRIPTS = REPO_ROOT / "skills/manim-teaching-studio/scripts"
PREVIEW_SERVER = REPO_ROOT / "skills/manim-teaching-studio/preview/server.py"
PROBE = SKILL_SCRIPTS / "scene_probe.py"
DEFAULT_PORT = 5051
PREVIEW_SUBDIR = Path("docs/review/preview")

# 配色(浅色参考 Linear/shadcn 系;黑夜沿用深蓝紫玻璃)
PALETTES = {
    "light": dict(
        text="#1c2333", dim="#5d6b8a", card="rgba(255, 255, 255, 0.86)",
        card_border="rgba(23, 30, 60, 0.14)", input_bg="rgba(255, 255, 255, 0.95)",
        input_border="rgba(23, 30, 60, 0.22)", btn_bg="rgba(255, 255, 255, 0.92)",
        btn_border="rgba(23, 30, 60, 0.22)", drop_bg="rgba(245, 248, 253, 0.9)",
        drop_border="rgba(77, 107, 254, 0.4)", log_bg="#0d1424", log_fg="#aab6d8",
        title="#4d6bfe",
    ),
    "dark": dict(
        text="#e9edf9", dim="#8d99bd", card="rgba(18, 26, 48, 0.82)",
        card_border="rgba(150, 172, 255, 0.22)", input_bg="rgba(10, 16, 30, 0.85)",
        input_border="rgba(150, 172, 255, 0.28)", btn_bg="rgba(28, 39, 68, 0.9)",
        btn_border="rgba(150, 172, 255, 0.3)", drop_bg="rgba(14, 21, 40, 0.6)",
        drop_border="rgba(150, 172, 255, 0.35)", log_bg="#080d1a", log_fg="#aab6d8",
        title="#a9bfff",
    ),
}


def build_qss(p: dict) -> str:
    return f"""
* {{ font-family: "Times New Roman", "SimSun", "宋体", serif; font-size: 13px; color: {p['text']}; }}
QWidget#Root {{ background: transparent; }}
QFrame#Card {{ background: {p['card']}; border: 1px solid {p['card_border']}; border-radius: 14px; }}
QLabel#Title {{ font-size: 15px; font-weight: 700; color: {p['title']}; background: transparent; border: none; }}
QLabel#Sub {{ color: {p['dim']}; background: transparent; border: none; font-size: 11px; }}
QLabel#StatKey {{ color: {p['dim']}; background: transparent; border: none; }}
QLabel#StatVal {{ color: {p['text']}; background: transparent; border: none; font-weight: 600; }}
QPushButton {{
  background: {p['btn_bg']};
  border: 1px solid {p['btn_border']};
  border-radius: 9px; padding: 8px 14px; color: {p['text']};
}}
QPushButton:hover {{ border-color: #4d6bfe; color: #4d6bfe; }}
QPushButton:pressed {{ background: rgba(77, 107, 254, 0.18); }}
QPushButton#Primary {{
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop:0 #4d6bfe, stop:1 #6d4ff7);
  border: none; color: white; font-weight: 700; border-radius: 9px; padding: 10px 22px;
}}
QPushButton#Primary:hover {{ background: #5d7bff; color: white; }}
QPushButton#Primary:disabled {{ background: #aab4d8; color: #6b7280; }}
QPushButton#Danger:hover {{ border-color: #e5484d; color: #e5484d; }}
QLineEdit, QComboBox {{
  background: {p['input_bg']};
  border: 1px solid {p['input_border']};
  border-radius: 9px; padding: 8px 10px; color: {p['text']};
}}
QComboBox QAbstractItemView {{
  background: {p['input_bg']}; border: 1px solid {p['input_border']};
  selection-background-color: rgba(77, 107, 254, 0.3); color: {p['text']};
}}
QFrame#DropZone {{ background: {p['drop_bg']}; border: 2px dashed {p['drop_border']}; border-radius: 16px; }}
QFrame#DropZone[drag="true"] {{ border: 2px dashed #4d6bfe; background: rgba(77, 107, 254, 0.12); }}
QPlainTextEdit {{
  background: {p['log_bg']};
  border: 1px solid {p['card_border']};
  border-radius: 10px; color: {p['log_fg']};
  font-family: Consolas, "Microsoft YaHei"; font-size: 12px;
}}
QScrollBar:vertical {{ background: transparent; width: 8px; }}
QScrollBar::handle:vertical {{ background: rgba(120, 135, 190, 0.3); border-radius: 4px; min-height: 24px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QMessageBox {{ background: {p['card']}; }}
QMessageBox QLabel {{ color: {p['text']}; }}
QMessageBox QPushButton {{ min-width: 70px; }}
"""


def is_port_alive(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.3):
            return True
    except OSError:
        return False


def dir_size(path: Path) -> tuple[int, int]:
    """返回 (字节数, 文件数)。"""
    total, n = 0, 0
    if not path.exists():
        return 0, 0
    for f in path.rglob("*"):
        if f.is_file():
            try:
                total += f.stat().st_size
                n += 1
            except OSError:
                pass
    return total, n


def fmt_size(n: int) -> str:
    if n >= 1024 * 1024:
        return f"{n / 1024 / 1024:.2f} MB"
    if n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} B"


def run_probe(path: Path, quality: str, on_line) -> bool:
    """执行探针;路径为 .py → file 模式,目录 → probe 模式(无 scenes 布局时退化为逐文件)。"""
    cmd: list[str] | None = None
    if path.is_file() and path.suffix == ".py":
        cmd = [sys.executable, str(PROBE), "file", str(path), "--quality", quality]
    elif path.is_dir():
        scenes = path / "scenes"
        has_layout = scenes.exists() and any(
            (scenes / d / "main.py").exists() for d in [p.name for p in scenes.iterdir()]
        )
        if has_layout:
            cmd = [sys.executable, str(PROBE), "probe", str(path), "--quality", quality]
        else:
            pys = sorted(path.glob("*.py"))
            if not pys:
                on_line("[错误] 目录下没有找到场景 .py 文件")
                return False
            ok = True
            for py in pys:
                on_line(f"--- 探针 {py.name} ---")
                if not run_probe(py, quality, on_line):
                    ok = False
            return ok
    if cmd is None:
        on_line("[错误] 请选择 manim 场景 .py 文件或工程文件夹")
        return False
    env = dict(os.environ, MANIM_LOW_RES="1" if quality == "low" else "0")
    on_line("$ " + " ".join(f'"{c}"' if " " in c else c for c in cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            env=env, encoding="utf-8", errors="replace")
    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.rstrip()
        if line:
            on_line(line)
    proc.wait()
    return proc.returncode == 0


def probe_out_root_for(path: Path) -> Path:
    if path.is_file():
        return path.parent / "docs/review/preview"
    return path / "docs/review/preview"


def project_dir_for(path: Path) -> Path:
    if path.is_file():
        return path.parent
    return path


class Stats:
    def __init__(self):
        self.project: Path | None = None
        self.out_root: Path | None = None

    def set_project(self, path: Path) -> None:
        self.project = project_dir_for(path)
        self.out_root = probe_out_root_for(path)

    def compute(self) -> tuple[int, int, int, int]:
        if self.out_root is None or not self.out_root.exists():
            return 0, 0, 0, 0
        size, files = dir_size(self.out_root)
        scenes, nodes = 0, 0
        idx = self.out_root / "index.json"
        if idx.exists():
            try:
                data = json.loads(idx.read_text(encoding="utf-8"))
                for s in data.get("scenes", []):
                    scenes += 1
                    nodes += int(s.get("nodes") or 0)
            except Exception:  # noqa: BLE001
                pass
        return size, files, scenes, nodes


def try_pyside6(stats: Stats) -> int:
    try:  # noqa: PLC0415
        from PySide6.QtCore import Qt, QTimer
        from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath
        from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout, QLabel,
                                       QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit,
                                       QPushButton, QVBoxLayout, QWidget, QFileDialog)
    except ImportError:
        return 1

    class Main(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.resize(560, 640)
            self.drag_pos = None
            self.path: Path | None = None
            self.server_proc: subprocess.Popen | None = None
            self.line_queue: list[str] = []
            self.running = False
            self.dark = False

            root = QWidget()
            root.setObjectName("Root")
            self.setCentralWidget(root)
            lay = QVBoxLayout(root)
            lay.setContentsMargins(18, 14, 18, 18)
            lay.setSpacing(12)

            # 标题栏
            bar = QHBoxLayout()
            title = QLabel("🎬 Manim Teaching Studio · 预览启动器")
            title.setObjectName("Title")
            bar.addWidget(title)
            bar.addStretch(1)
            self.btn_theme = QPushButton("🌙")
            self.btn_theme.setFixedSize(32, 30)
            self.btn_theme.setToolTip("切换白天/黑夜模式")
            self.btn_theme.clicked.connect(self.toggle_theme)
            bar.addWidget(self.btn_theme)
            btn_close = QPushButton("✕")
            btn_close.setFixedSize(30, 30)
            btn_close.clicked.connect(self.close)
            bar.addWidget(btn_close)
            lay.addLayout(bar)

            # 拖放区
            self.drop = QFrame()
            self.drop.setObjectName("DropZone")
            self.drop.setAcceptDrops(True)
            dlay = QVBoxLayout(self.drop)
            dlay.setContentsMargins(16, 22, 16, 22)
            dlab = QLabel("点击选择,或把 manim 的 .py 文件 / 工程文件夹拖到这里")
            dlab.setAlignment(Qt.AlignCenter)
            dlab.setStyleSheet("font-size: 13px; color: #4d6bfe; background: transparent;")
            dlay.addWidget(dlab)
            self.drop.mousePressEvent = lambda e: self.pick_file()
            lay.addWidget(self.drop)

            # 路径 + 质量
            row = QHBoxLayout()
            self.path_edit = QLineEdit()
            self.path_edit.setPlaceholderText("未选择文件…")
            self.path_edit.setReadOnly(True)
            btn_browse = QPushButton("浏览…")
            btn_browse.clicked.connect(self.pick_file)
            self.quality = QComboBox()
            self.quality.addItems(["低清 480p(快)", "高清 1080p(慢)"])
            row.addWidget(self.path_edit, 1)
            row.addWidget(self.quality)
            row.addWidget(btn_browse)
            lay.addLayout(row)

            # 主按钮
            brow = QHBoxLayout()
            self.btn_go = QPushButton("✦ 分析并启动预览")
            self.btn_go.setObjectName("Primary")
            self.btn_go.clicked.connect(self.analyze)
            self.btn_refresh = QPushButton("刷新数据")
            self.btn_refresh.clicked.connect(lambda: self.analyze(skip_server=True))
            self.btn_del = QPushButton("删除数据")
            self.btn_del.setObjectName("Danger")
            self.btn_del.clicked.connect(self.delete_data)
            self.btn_open = QPushButton("打开预览")
            self.btn_open.clicked.connect(lambda: webbrowser.open(f"http://127.0.0.1:{DEFAULT_PORT}"))
            self.btn_stop = QPushButton("停止服务器")
            self.btn_stop.clicked.connect(self.stop_server)
            brow.addWidget(self.btn_go, 1)
            brow.addWidget(self.btn_refresh)
            brow.addWidget(self.btn_del)
            lay.addLayout(brow)
            brow2 = QHBoxLayout()
            brow2.addWidget(self.btn_open)
            brow2.addWidget(self.btn_stop)
            brow2.addStretch(1)
            lay.addLayout(brow2)

            # 统计卡
            card = QFrame()
            card.setObjectName("Card")
            clay = QHBoxLayout(card)
            clay.setContentsMargins(14, 10, 14, 10)
            self.stat_size = QLabel("磁盘占用:—")
            self.stat_files = QLabel("文件:—")
            self.stat_scenes = QLabel("场景:—")
            self.stat_nodes = QLabel("节点图:—")
            self.stat_server = QLabel("服务器:未运行")
            for w in (self.stat_size, self.stat_files, self.stat_scenes, self.stat_nodes, self.stat_server):
                w.setObjectName("StatVal")
                clay.addWidget(w)
            lay.addWidget(card)

            # 日志(字体保持不变:Consolas + 微软雅黑,终端风格)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setMaximumBlockCount(4000)
            lay.addWidget(self.log, 1)

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.pump)
            self.timer.start(200)
            self.refresh_stats()
            self.refresh_server_status()
            self.logln("就绪。选择一个 manim 场景文件或工程文件夹后点「分析并启动预览」。")

        # ---------- 液态玻璃背景 ----------
        def paintEvent(self, event) -> None:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            rect = self.rect().adjusted(1, 1, -1, -1)
            grad = QLinearGradient(0, 0, rect.width(), rect.height())
            if self.dark:
                grad.setColorAt(0.0, QColor(16, 24, 46, 246))
                grad.setColorAt(0.55, QColor(10, 16, 32, 250))
                grad.setColorAt(1.0, QColor(22, 18, 52, 248))
                border = QColor(150, 172, 255, 70)
            else:
                grad.setColorAt(0.0, QColor(255, 255, 255, 250))
                grad.setColorAt(0.6, QColor(243, 246, 253, 252))
                grad.setColorAt(1.0, QColor(246, 240, 255, 250))
                border = QColor(120, 135, 190, 60)
            path = QPainterPath()
            path.addRoundedRect(rect, 18, 18)
            p.fillPath(path, grad)
            p.setPen(border)
            p.drawPath(path)

        def toggle_theme(self) -> None:
            self.dark = not self.dark
            QApplication.instance().setStyleSheet(build_qss(PALETTES["dark" if self.dark else "light"]))
            self.btn_theme.setText("☀️" if self.dark else "🌙")
            self.update()

        def mousePressEvent(self, event) -> None:
            if event.button() == Qt.LeftButton:
                self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

        def mouseMoveEvent(self, event) -> None:
            if self.drag_pos is not None and event.buttons() & Qt.LeftButton:
                self.move(event.globalPosition().toPoint() - self.drag_pos)

        def mouseReleaseEvent(self, event) -> None:
            self.drag_pos = None

        def dragEnterEvent(self, event) -> None:
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
                self.drop.setProperty("drag", "true")
                self.drop.style().unpolish(self.drop)
                self.drop.style().polish(self.drop)

        def dragLeaveEvent(self, event) -> None:
            self.drop.setProperty("drag", "false")
            self.drop.style().unpolish(self.drop)
            self.drop.style().polish(self.drop)

        def dropEvent(self, event) -> None:
            self.drop.setProperty("drag", "false")
            self.drop.style().unpolish(self.drop)
            self.drop.style().polish(self.drop)
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    self.set_path(Path(url.toLocalFile()))
                    return

        # ---------- 逻辑 ----------
        def pick_file(self) -> None:
            f, _ = QFileDialog.getOpenFileName(self, "选择 manim 场景文件", "", "Manim Python (*.py);;所有文件 (*)")
            if f:
                self.set_path(Path(f))

        def set_path(self, p: Path) -> None:
            self.path = p
            self.path_edit.setText(str(p))
            stats.set_project(p)
            self.refresh_stats()

        def logln(self, line: str) -> None:
            self.line_queue.append(line)

        def pump(self) -> None:
            while self.line_queue:
                self.log.appendPlainText(self.line_queue.pop(0))

        def analyze(self, skip_server: bool = False) -> None:
            if self.path is None:
                QMessageBox.warning(self, "提示", "请先选择 manim 场景 .py 文件或工程文件夹")
                return
            if self.running:
                return
            self.running = True
            self.btn_go.setEnabled(False)
            self.btn_refresh.setEnabled(False)
            quality = "low" if self.quality.currentIndex() == 0 else "high"
            self.logln("")
            self.logln("=" * 46)
            self.logln(f"[分析] {self.path} ({quality})")

            def work():
                ok = run_probe(self.path, quality, self.logln)
                if ok:
                    self.logln("[完成] 探针数据已生成")
                else:
                    self.logln("[失败] 探针未完成,详见上方日志")
                if ok and not skip_server:
                    self.start_server()
                self.running = False
                self.btn_go.setEnabled(True)
                self.btn_refresh.setEnabled(True)
                self.refresh_stats()
                self.refresh_server_status()

            threading.Thread(target=work, daemon=True).start()

        def start_server(self) -> None:
            if is_port_alive(DEFAULT_PORT):
                self.logln(f"[提示] 端口 {DEFAULT_PORT} 已有服务在运行,直接复用")
                self.refresh_server_status()
                return
            project = project_dir_for(self.path)
            self.logln(f"[启动] 预览服务器 → http://127.0.0.1:{DEFAULT_PORT} (项目 {project.name})")
            self.server_proc = subprocess.Popen(
                [sys.executable, str(PREVIEW_SERVER), str(project),
                 "--no-browser", "--timeout", "0"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            for _ in range(60):
                if is_port_alive(DEFAULT_PORT):
                    self.logln("[就绪] 服务器已启动,即将打开浏览器")
                    webbrowser.open(f"http://127.0.0.1:{DEFAULT_PORT}")
                    self.refresh_server_status()
                    return
                time.sleep(0.5)
            self.logln("[警告] 服务器启动超时,请检查日志或端口占用")

        def stop_server(self) -> None:
            if not is_port_alive(DEFAULT_PORT):
                self.logln("[提示] 服务器未在运行")
                self.refresh_server_status()
                return
            try:
                import urllib.request

                urllib.request.urlopen(
                    urllib.request.Request(f"http://127.0.0.1:{DEFAULT_PORT}/api/shutdown", method="POST"),
                    timeout=3,
                ).read()
                self.logln("[已停止] 预览服务器")
            except Exception:  # noqa: BLE001
                self.logln("[警告] 无法优雅停止服务器(可结束 python 进程)")
            self.refresh_server_status()

        def delete_data(self) -> None:
            if self.path is None:
                return
            out = probe_out_root_for(self.path)
            if not out.exists():
                QMessageBox.information(self, "提示", "没有探针数据可删除")
                return
            size, files, scenes, nodes = stats.compute()
            ans = QMessageBox.question(
                self, "删除数据",
                f"确定删除探针数据?\n{out}\n\n占用 {fmt_size(size)} · {files} 个文件 · {scenes} 场景 · {nodes} 节点图",
            )
            if ans == QMessageBox.Yes:
                import shutil

                shutil.rmtree(out, ignore_errors=True)
                self.logln(f"[已删除] {out}")
                self.refresh_stats()

        def refresh_stats(self) -> None:
            size, files, scenes, nodes = stats.compute()
            self.stat_size.setText(f"磁盘占用:{fmt_size(size)}")
            self.stat_files.setText(f"文件:{files}")
            self.stat_scenes.setText(f"场景:{scenes}")
            self.stat_nodes.setText(f"节点图:{nodes}")

        def refresh_server_status(self) -> None:
            alive = is_port_alive(DEFAULT_PORT)
            self.stat_server.setText(f"服务器:{'运行中 :' + str(DEFAULT_PORT) if alive else '未运行'}")

        def closeEvent(self, event) -> None:
            out = probe_out_root_for(self.path) if self.path else None
            if out is not None and out.exists():
                size, files, scenes, nodes = stats.compute()
                box = QMessageBox(self)
                box.setWindowTitle("退出前 · 数据怎么办")
                box.setText(f"是否保留本次生成的探针数据?\n({out}\n占用 {fmt_size(size)} · {files} 个文件 · {scenes} 场景 · {nodes} 节点图)\n\n保留=下次直接打开预览;删除=释放磁盘。")
                keep = box.addButton("保留数据并退出", QMessageBox.AcceptRole)
                delete = box.addButton("删除数据并退出", QMessageBox.DestructiveRole)
                box.addButton("取消", QMessageBox.RejectRole)
                box.exec()
                if box.clickedButton() is delete:
                    import shutil

                    shutil.rmtree(out, ignore_errors=True)
                elif box.clickedButton() is not keep:
                    event.ignore()
                    return
            event.accept()

    app = QApplication(sys.argv)
    app.setStyleSheet(build_qss(PALETTES["light"]))
    win = Main()
    win.show()
    if os.environ.get("LAUNCHER_SMOKE"):
        QTimer.singleShot(2000, app.quit)
    return app.exec()


def try_tkinter(stats: Stats) -> int:
    """PySide6 缺失时的极简降级界面(无拖拽)。"""
    import tkinter as tk
    from tkinter import filedialog, messagebox

    root = tk.Tk()
    root.title("Manim Teaching Studio · 预览启动器(简化版)")
    root.geometry("560x430")
    root.configure(bg="#f5f7fc")
    tk.Label(root, text="请先 pip install PySide6 获得完整液态玻璃界面与拖拽支持",
             fg="#5d6b8a", bg="#f5f7fc").pack(pady=(10, 4))

    path_var = tk.StringVar()
    tk.Entry(root, textvariable=path_var, bg="#ffffff", fg="#1c2333",
             insertbackground="#1c2333").pack(fill="x", padx=14)

    def pick():
        f = filedialog.askopenfilename(filetypes=[("Manim Python", "*.py"), ("All", "*.*")])
        if f:
            path_var.set(f)
            stats.set_project(Path(f))

    tk.Button(root, text="选择 manim 场景文件…", command=pick, bg="#4d6bfe",
              fg="white", activebackground="#5d7bff").pack(pady=8)

    status = tk.StringVar(value="服务器:未运行 · 磁盘占用:—")
    tk.Label(root, textvariable=status, fg="#4d6bfe", bg="#f5f7fc").pack(pady=2)
    log = tk.Text(root, height=12, bg="#0d1424", fg="#aab6d8", insertbackground="#fff")
    log.pack(fill="both", expand=True, padx=14, pady=8)

    def ln(s):
        log.insert("end", s + "\n")
        log.see("end")

    def analyze():
        if not path_var.get():
            messagebox.showwarning("提示", "请先选择文件")
            return
        p = Path(path_var.get())
        ln("=" * 40)
        run_probe(p, "low", ln)
        if not is_port_alive(DEFAULT_PORT):
            subprocess.Popen([sys.executable, str(PREVIEW_SERVER), str(project_dir_for(p)),
                              "--no-browser", "--timeout", "0"])
            ln("[启动] 预览服务器…")
        size, files, scenes, nodes = stats.compute()
        status.set(f"服务器:{'运行中' if is_port_alive(DEFAULT_PORT) else '启动中'} · "
                   f"占用 {fmt_size(size)} · {files} 文件 · {scenes} 场景 · {nodes} 节点图")
        webbrowser.open(f"http://127.0.0.1:{DEFAULT_PORT}")

    tk.Button(root, text="✦ 分析并启动预览", command=analyze, bg="#4d6bfe",
              fg="white", activebackground="#5d7bff").pack(pady=6)
    root.mainloop()
    return 0


def main() -> None:
    stats = Stats()
    rc = try_pyside6(stats)
    if rc == 1:
        rc = try_tkinter(stats)
    sys.exit(rc)


if __name__ == "__main__":
    main()
