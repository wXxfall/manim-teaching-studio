"""scene_probe.py — 元素级画面探针(交互式画面预览的数据生产者).

确定性工具(不生成、不修改场景代码,只读代码 + 渲染取帧):

1. AST 静态分析 scenes/<dir>/main.py:
   - 提取 mobject 变量定义(变量名 → 行号)、`# ==== Phase N ====` 分段;
   - 按序累计 self.play / self.wait / self.add 的 run_time,得到精确动画时间线;
   - 判定每个元素变量的"入场事件"(第一次被动画引用的事件)。
2. 计算关键帧节点:
   - 每个入场事件结束后 +1.0s 为节点(透明度已拉满、画面稳定);
   - 若 1 秒后会撞上下一个事件,取间隙中点(用户已批准);
   - 相距 ≤0.5s 的节点合并(取组内最晚时刻);场景末帧永远是最后一个节点。
3. 探针渲染:
   - 加载场景类,重放 construct():节点之前的 play/wait 直接快进
     (begin → interpolate(1) → finish → clean_up_from_scene);
   - 包含节点时刻的动画用 update_to_time() 按帧率步进到该时刻,
     用相机直接输出无损 PNG(低清 480p / 高清 1080p,由 MANIM_LOW_RES 决定);
   - 同时用 camera.points_to_pixel_coords 计算每个可见元素的屏幕像素 bbox。
4. 产出(默认 <project>/docs/review/preview/):
   - <scene>/node_NN.png          节点无损静帧(Manim 相机亲自渲染,非视频抽帧)
   - <scene>/elements.json        时间线 + 节点 + 元素 bbox + 元素↔代码行号映射
   - index.json                   全场景索引(预览服务器消费)

Run:
    python scene_probe.py analyze <scene_main.py>            # 只做静态时间线+节点,JSON 打印
    python scene_probe.py probe <project_path> [--scene scene01_intro]
                                [--quality low|high] [--out <dir>]
    python scene_probe.py file <任意 main.py> [--class 类名]  # 任意布局的单文件 Manim 场景
                                [--quality low|high] [--out <dir>]

设计依据(Manim CE 0.19.1 源码):
- Scene.play → renderer.play → compile_animation_data → begin_animations → play_internal;
- update_to_time(t) = 逐动画 interpolate(t/run_time) + update_mobjects(dt);
- Animation._setup_scene 把 introducer 的 mobject 加进 scene,
  clean_up_from_scene 负责 remover 的移除——快进路径照搬这两个语义即可与真实渲染一致;
- 节点时刻的相机取帧:cam.reset() + cam.capture_mobjects(scene.mobjects+foreground)
  全量重绘一次(渲染器只增量重绘 moving,探针不做静态背景缓存)。
"""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

import numpy as np

try:  # Windows 控制台 GBK 与 UTF-8 兼容
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

# ---------- 常量 ----------
NODE_GAP_AFTER = 1.0          # 入场结束后等 1 秒再截图
NODE_MERGE_EPS = 0.5          # 相距 ≤0.5s 的节点合并
NODE_TIME_EPS = 0.05          # 节点不落在整段边界上
DEFAULT_RUN_TIME = 1.0        # self.play 缺省 run_time(Manim 默认值)
PIL_AVAILABLE = True

# 引入动画类(用于入场判定与 Transform 特殊映射)
TRANSFORM_ANIMS = {"Transform", "ReplacementTransform", "FadeTransform", "FadeTransformPieces"}


def _import_manim():
    """导入 manim 并收集全部 Mobject 子类名(供 AST 判定 mobject 创建调用)."""
    import manim
    names = set()
    for n in dir(manim):
        obj = getattr(manim, n, None)
        if isinstance(obj, type):
            try:
                if issubclass(obj, manim.Mobject):
                    names.add(n)
            except TypeError:  # noqa: PERF203
                pass
    names.update({"Mobject", "VMobject", "always_redraw"})
    return manim, names


# ============================================================
# 1. AST 静态分析
# ============================================================

def root_name(node: ast.AST) -> str | None:
    """取表达式链最左端的变量名:laser.copy() → 'laser';a.animate.shift(...) → 'a'."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return root_name(node.value)
    if isinstance(node, ast.Call):
        return root_name(node.func)
    return None


def call_anim_name(node: ast.expr) -> str | None:
    """取动画调用名:FadeIn(...) → 'FadeIn';manim.Indicate(...) → 'Indicate'."""
    if isinstance(node, ast.Call):
        return call_anim_name(node.func)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def collect_arg_vars(arg: ast.expr, var_names: set[str]) -> list[str]:
    """从一个 play 参数里收集被动画的 mobject 变量名(仅已赋值的变量;忽略 keyword 与颜色常量)。

    FadeIn(title_cn) → ['title_cn']
    ShowPassingFlash(laser.copy().set_color(WHITE_)) → ['laser'](WHITE_ 不是已赋值 mobject 变量)
    AnimationGroup(FadeIn(a), FadeIn(b)) → ['a', 'b']
    """
    if isinstance(arg, ast.Name):
        return [arg.id] if arg.id in var_names else []
    if isinstance(arg, ast.Attribute):
        r = root_name(arg)
        return [r] if r and r in var_names else []
    if isinstance(arg, ast.Call):
        vars_: list[str] = []
        # 链式方法调用的根变量(laser.copy().set_color(...) 的根是 laser)
        r = root_name(arg.func)
        if r and r in var_names:
            vars_.append(r)
        for sub in arg.args:
            vars_ += collect_arg_vars(sub, var_names)
        return vars_
    return []


# ---------- 常量求值 / 名称替换(辅助函数内联与常量循环展开用) ----------

_UNRESOLVED = object()


class _NameSubst(ast.NodeTransformer):
    """按 mapping 替换 Name(支持字符串改名与 ast 节点替换),跳过嵌套函数参数遮蔽。"""

    def __init__(self, rename: dict[str, str], consts: dict[str, ast.expr]):
        self.rename = rename
        self.consts = consts
        self._shadow: list[set[str]] = []

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if node.id in self._shadow_current():
            return node
        if node.id in self.consts:
            return self.consts[node.id]
        if node.id in self.rename:
            return ast.copy_location(ast.Name(id=self.rename[node.id], ctx=node.ctx), node)
        return node

    def _shadow_current(self) -> set[str]:
        out: set[str] = set()
        for s in self._shadow:
            out |= s
        return out

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self._shadow.append({a.arg for a in node.args.args})
        self.generic_visit(node)
        self._shadow.pop()
        return node

    def visit_Lambda(self, node: ast.Lambda) -> ast.AST:
        self._shadow.append({a.arg for a in node.args.args})
        self.generic_visit(node)
        self._shadow.pop()
        return node


def _subst(stmt: ast.AST, rename: dict[str, str] | None = None, consts: dict[str, ast.expr] | None = None) -> ast.AST:
    # NodeTransformer.generic_visit 会原地修改输入树,必须深拷贝隔离
    if not rename and not consts:
        return copy.deepcopy(stmt)
    return _NameSubst(rename or {}, consts or {}).visit(copy.deepcopy(stmt))


def resolve_const(node: ast.expr, const_table: dict) -> object:
    """把 AST 常量表达式求值为 Python 值(仅字面量/名称/容器/负数)。"""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return const_table.get(node.id, _UNRESOLVED)
    if isinstance(node, (ast.List, ast.Tuple)):
        vals = [resolve_const(e, const_table) for e in node.elts]
        if any(v is _UNRESOLVED for v in vals):
            return _UNRESOLVED
        return tuple(vals) if isinstance(node, ast.Tuple) else list(vals)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        v = resolve_const(node.operand, const_table)
        return -v if isinstance(v, (int, float)) else _UNRESOLVED
    return _UNRESOLVED


def bind_pattern(target: ast.expr, value) -> dict[str, object] | None:
    """把循环目标模式(可嵌套元组解包)与迭代值绑定,返回 {名字: Python 值}。"""
    if isinstance(target, ast.Name):
        return {target.id: value}
    if isinstance(target, (ast.Tuple, ast.List)):
        if not isinstance(value, (list, tuple)) or len(target.elts) != len(value):
            return None
        bindings: dict[str, object] = {}
        for t, v in zip(target.elts, value):
            sub = bind_pattern(t, v)
            if sub is None:
                return None
            bindings.update(sub)
        return bindings
    return None


def resolve_iter(node: ast.expr, const_table: dict) -> list | None:
    """解析可静态展开的循环迭代序列;返回 Python 值列表或 None(不可展开)。"""
    if isinstance(node, (ast.List, ast.Tuple)):
        vals = [resolve_const(e, const_table) for e in node.elts]
        return vals if all(v is not _UNRESOLVED for v in vals) else None
    if isinstance(node, ast.Name):
        v = const_table.get(node.id, _UNRESOLVED)
        return list(v) if isinstance(v, (list, tuple)) else None
    if isinstance(node, ast.Call) and call_anim_name(node.func) == "enumerate" and node.args:
        inner = resolve_iter(node.args[0], const_table)
        return None if inner is None else list(enumerate(inner))
    if isinstance(node, ast.Call) and call_anim_name(node.func) == "range" and node.args:
        args = [resolve_const(a, const_table) for a in node.args]
        if 1 <= len(args) <= 3 and all(isinstance(a, int) and not isinstance(a, bool) for a in args):
            return list(range(*args))  # type: ignore[arg-type]
    return None


def collect_assigned_names(stmts: list[ast.stmt]) -> set[str]:
    """收集一段语句里被赋值的名字(不含嵌套函数体),用于循环迭代重命名。"""
    out: set[str] = set()

    def walk(s: ast.stmt) -> None:
        if isinstance(s, ast.Assign):
            for t in s.targets:
                if isinstance(t, ast.Name):
                    out.add(t.id)
        elif isinstance(s, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            for sub in getattr(s, "body", []):
                walk(sub)
            for sub in getattr(s, "orelse", []) or []:
                walk(sub)
            if isinstance(s, ast.Try):
                for h in getattr(s, "handlers", []):
                    for sub in h.body:
                        walk(sub)

    for s in stmts:
        walk(s)
    return out


def _body_has_events(stmts: list[ast.stmt]) -> bool:
    """检查语句段内是否含 self.play / self.wait 调用(用于决定是否警告循环无法展开)。"""

    def check(s: ast.stmt) -> bool:
        if isinstance(s, ast.Expr) and isinstance(s.value, ast.Call):
            fn = s.value.func
            if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name) and fn.value.id == "self":
                if fn.attr in ("play", "wait"):
                    return True
        for child in ast.iter_child_nodes(s):
            if isinstance(child, ast.stmt) and check(child):
                return True
        return False

    return any(check(s) for s in stmts)


def _return_names(fn: ast.FunctionDef) -> list[str]:
    for s in fn.body:
        if isinstance(s, ast.Return) and s.value is not None:
            if isinstance(s.value, ast.Name):
                return [s.value.id]
            if isinstance(s.value, (ast.Tuple, ast.List)):
                return [e.id for e in s.value.elts if isinstance(e, ast.Name)]
    return []


def analyze_scene(main_py: Path) -> dict:
    """静态分析场景代码,返回时间线、元素变量表、节点表(与渲染无关,纯读代码)。"""
    manim, mobject_classes = _import_manim()
    source = main_py.read_text(encoding="utf-8")
    tree = ast.parse(source)
    scene_cls = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = {b.id for b in node.bases if isinstance(b, ast.Name)}
            if "Scene" in bases:
                scene_cls = node
                break
    if scene_cls is None:
        raise SystemExit(f"[错误] {main_py}:找不到 Scene 子类")
    ctor = next((n for n in scene_cls.body if isinstance(n, ast.FunctionDef) and n.name == "construct"), None)
    if ctor is None:
        raise SystemExit(f"[错误] {main_py}:{scene_cls.name} 无 construct()")

    var_lines: dict[str, int] = {}
    phases: list[tuple[int, str]] = []  # (起始行, 段落名)
    events: list[dict] = []
    warnings: list[str] = []

    # 模块级常量表(供循环展开时求值 PEAKS/ACCENT 之类常量名)
    const_table: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            val = resolve_const(node.value, const_table)
            if val is not _UNRESOLVED:
                const_table[node.targets[0].id] = val
    # 类内辅助函数(含 play/wait 的嵌套函数,调用处内联)
    helpers = {
        n.name: n for n in scene_cls.body
        if isinstance(n, ast.FunctionDef) and n.name != "construct"
    }

    ctx = {
        "helpers": helpers,
        "const_table": const_table,
        "var_lines": var_lines,
        "events": events,
        "mobject_classes": mobject_classes,
        "warnings": warnings,
    }
    for stmt in ctor.body:
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
            m = re.match(r"^\s*=+\s*Phase\s*(\S+)\s*(.*?)\s*=*$", stmt.value.value)
            if m:
                phases.append((stmt.lineno, (m.group(1) + " " + m.group(2)).strip()))
        _expand_stmt(stmt, ctx, 0)

    # ---- 累计时间线 ----
    t = 0.0
    for ev in events:
        ev["start"] = round(t, 3)
        dur = ev.get("duration", 0.0)
        ev["end"] = round(t + dur, 3)
        t = ev["end"]
    total = round(t, 3)

    # ---- 入场事件 ----
    seen: set[str] = set()
    for i, ev in enumerate(events):
        introduced = [v for v in ev["vars"] if v not in seen]
        seen.update(ev["vars"])
        ev["introduced"] = introduced
        ev["is_entrance"] = bool(introduced)

    # ---- 节点计算 ----
    candidates: list[tuple[float, int, list[str]]] = []
    for i, ev in enumerate(events):
        if not ev["is_entrance"]:
            continue
        nxt = events[i + 1] if i + 1 < len(events) else None
        if nxt is None:
            node_t = ev["end"] + NODE_GAP_AFTER
        else:
            gap = nxt["start"] - ev["end"]
            node_t = ev["end"] + min(NODE_GAP_AFTER, max(NODE_TIME_EPS / 2, gap / 2))
        node_t = round(node_t, 3)
        if total > NODE_TIME_EPS:
            node_t = min(node_t, total - NODE_TIME_EPS)
        if node_t > 0:
            candidates.append((node_t, i, list(ev["introduced"])))
    candidates.sort(key=lambda c: c[0])

    nodes: list[dict] = []
    clusters: list[dict] = []
    for t_node, ev_idx, introduced in candidates:
        if clusters and t_node - clusters[-1]["t_max"] <= NODE_MERGE_EPS:
            clusters[-1]["t_max"] = t_node
            clusters[-1]["introduced"] += [v for v in introduced if v not in clusters[-1]["introduced"]]
            clusters[-1]["from_events"].append(ev_idx)
        else:
            clusters.append({"t_max": t_node, "introduced": list(introduced), "from_events": [ev_idx]})
    for k, cl in enumerate(clusters, 1):
        nodes.append({
            "id": f"node_{k:02d}",
            "time": round(cl["t_max"], 3),
            "introduced": cl["introduced"],
            "from_events": cl["from_events"],
        })
    if not nodes or total - nodes[-1]["time"] > NODE_MERGE_EPS:
        nodes.append({"id": f"node_{len(nodes)+1:02d}", "time": total, "introduced": [], "from_events": []})

    # ---- 元素变量表 ----
    elements_by_var = {
        v: {"line": ln, "phase": _phase_at(phases, ln)} for v, ln in var_lines.items()
    }
    for i, ev in enumerate(events):
        for v in ev["vars"]:
            if v in elements_by_var:
                elements_by_var[v].setdefault("entrance", {
                    "event": i, "line": ev["line"], "anim": ev["anims"][0] if ev["anims"] else "",
                    "run_time": ev.get("run_time", 0.0),
                    "end": ev["end"],
                })

    return {
        "scene_class": scene_cls.name,
        "source": str(main_py),
        "duration": total,
        "events": events,
        "nodes": nodes,
        "elements_by_var": elements_by_var,
        "phases": [p[1] for p in phases],
        "warnings": warnings,
    }


def _expand_stmt(stmt: ast.stmt, ctx: dict, depth: int) -> None:
    """按执行顺序走查语句:内联辅助函数、展开常量循环、展平复合语句,叶子交给 _handle_statement。"""
    if depth > 12:
        ctx["warnings"].append(f"第 {getattr(stmt, 'lineno', '?')} 行:嵌套过深,停止内联展开")
        return
    if isinstance(stmt, ast.FunctionDef):
        # construct 内的嵌套辅助函数:登记供后续调用点内联
        if stmt.name not in ctx["helpers"]:
            ctx["helpers"][stmt.name] = stmt
        return
    if isinstance(stmt, (ast.Return, ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)):
        return

    # --- 常量赋值登记(construct 局部常量,供后续循环展开求值) ---
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
        val = resolve_const(stmt.value, ctx["const_table"])
        if val is not _UNRESOLVED:
            ctx["const_table"][stmt.targets[0].id] = val

    # --- 类内辅助函数调用:内联函数体,返回值变量改名为调用处目标名 ---
    call_targets: list[str] = []
    if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
        fname = call_anim_name(stmt.value.func)
        if fname in ctx["helpers"]:
            # 支持 `up1, down1, note1 = path(...)` 元组解包目标
            for t in stmt.targets:
                if isinstance(t, ast.Name):
                    call_targets.append(t.id)
                elif isinstance(t, (ast.Tuple, ast.List)):
                    call_targets += [e.id for e in t.elts if isinstance(e, ast.Name)]
            helper = ctx["helpers"][fname]
            rets = _return_names(helper)
            rename = dict(zip(rets, call_targets))
            for t in call_targets:
                ctx["var_lines"].setdefault(t, stmt.lineno)
            for s in helper.body:
                _expand_stmt(_subst(s, rename), ctx, depth + 1)
            return
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        fname = call_anim_name(stmt.value.func)
        if fname in ctx["helpers"]:
            for s in ctx["helpers"][fname].body:
                _expand_stmt(s, ctx, depth + 1)
            return

    # --- 常量循环展开(仅当迭代序列可静态求值) ---
    if isinstance(stmt, ast.For):
        values = resolve_iter(stmt.iter, ctx["const_table"])
        if values is not None:
            assigned = collect_assigned_names(stmt.body)
            for k, val in enumerate(values):
                bindings = bind_pattern(stmt.target, val)
                if bindings is None:
                    ctx["warnings"].append(f"第 {stmt.lineno} 行:循环目标解包失败,按一轮展开")
                    for s in stmt.body:
                        _expand_stmt(s, ctx, depth + 1)
                    return
                consts = {n: ast.Constant(v) for n, v in bindings.items()}
                rename: dict[str, str] = {}
                if k > 0:
                    for nm in assigned:
                        if nm not in bindings:
                            rename[nm] = f"{nm}#it{k}"
                for s in stmt.body:
                    _expand_stmt(_subst(s, rename, consts), ctx, depth + 1)
            return
        if _body_has_events(stmt.body):
            ctx["warnings"].append(f"第 {stmt.lineno} 行:for 循环无法静态展开,时间线按一轮估算,可能失真")

    # --- 其余复合语句:按分支顺序展开(if/else 二选一执行,静态按代码顺序遍历) ---
    if isinstance(stmt, (ast.If, ast.While, ast.With, ast.Try)):
        for sub in getattr(stmt, "body", []):
            _expand_stmt(sub, ctx, depth + 1)
        for sub in getattr(stmt, "orelse", []) or []:
            _expand_stmt(sub, ctx, depth + 1)
        if isinstance(stmt, ast.Try):
            for h in getattr(stmt, "handlers", []):
                for sub in h.body:
                    _expand_stmt(sub, ctx, depth + 1)
        if isinstance(stmt, (ast.For, ast.While, ast.With, ast.Try)):
            for sub in getattr(stmt, "finalbody", []) or []:
                _expand_stmt(sub, ctx, depth + 1)
        return

    _handle_statement(stmt, ctx["events"], ctx["var_lines"], ctx["mobject_classes"])


def _phase_at(phases: list[tuple[int, str]], line: int) -> str:
    name = ""
    for ln, pname in phases:
        if ln <= line:
            name = pname
        else:
            break
    return name


def _handle_statement(stmt: ast.stmt, events: list[dict], var_lines: dict[str, int], mobject_classes: set[str]) -> None:
    """把一条语句归入三类事件:play / wait / add,并登记元素变量定义行。"""
    if isinstance(stmt, ast.Assign):
        for target in stmt.targets:
            if isinstance(target, ast.Name):
                # 任何函数调用赋值的名字都登记为候选元素变量:
                # 覆盖 Text(...)/Square(...) 等 mobject 类,以及 make_ambulance()/pitch_waves()
                # 等模块级辅助函数返回的 mobject(否则这类元素只能拿到内存地址 id)。
                # 非 mobject 变量被登记也无害:只参与"play 参数过滤",不产生副作用。
                if isinstance(stmt.value, ast.Call) or _is_mobject_expr(stmt.value, mobject_classes):
                    var_lines[target.id] = stmt.lineno
        return
    if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
        return
    call = stmt.value
    if not isinstance(call.func, ast.Attribute) or not isinstance(call.func.value, ast.Name):
        return
    if call.func.value.id != "self":
        return
    method = call.func.attr
    if method not in ("play", "wait", "add"):
        return

    if method == "wait":
        dur = DEFAULT_RUN_TIME
        if call.args and isinstance(call.args[0], ast.Constant) and isinstance(call.args[0].value, (int, float)):
            dur = float(call.args[0].value)
        events.append({"kind": "wait", "line": stmt.lineno, "duration": dur, "vars": [], "anims": [], "run_time": dur})
        return

    vars_: list[str] = []
    anims: list[str] = []
    for arg in call.args:
        anims.append(call_anim_name(arg) or "")
        vars_ += collect_arg_vars(arg, set(var_lines))
    run_time = DEFAULT_RUN_TIME
    for kw in call.keywords:
        if kw.arg == "run_time" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, (int, float)):
            run_time = float(kw.value.value)
    if method == "add":
        events.append({"kind": "add", "line": stmt.lineno, "duration": 0.0, "vars": vars_, "anims": [], "run_time": 0.0})
    else:
        events.append({"kind": "play", "line": stmt.lineno, "duration": run_time, "vars": vars_, "anims": anims, "run_time": run_time})


def _is_mobject_expr(expr: ast.expr, mobject_classes: set[str]) -> bool:
    """判断表达式是否为 mobject 创建调用(允许 .shift/.set_opacity 等链式调用)。"""
    cur: ast.expr = expr
    while isinstance(cur, ast.Call):
        name = call_anim_name(cur.func)
        if name in mobject_classes:
            return True
        cur = cur.func
        if isinstance(cur, ast.Attribute):
            # Text(...).set_opacity(...):外层 Call 的 func 是 Attribute,继续向内找
            cur = cur.value
        else:
            break
    return False


# ============================================================
# 2. 探针渲染
# ============================================================

class ProbePlayback:
    """接管 self.play / self.wait:按节点精确步进,其余快进,并收集元素实例映射。"""

    def __init__(self, scene, analysis: dict, out_dir: Path, pixel_size: tuple[int, int]):
        self.scene = scene
        # 驱动只消费 play/wait(运行时调用一一对应);add 事件零时长,已在静态时间线里参与节点计算
        self.events = [e for e in analysis["events"] if e["kind"] in ("play", "wait")]
        self.nodes = sorted(analysis["nodes"], key=lambda n: n["time"])
        self.out_dir = out_dir
        self.pixel_size = pixel_size
        self.event_index = 0
        self.var_instances: dict[str, object] = {}
        self._inst_ids: set[int] = set()
        self.captured: list[dict] = []
        self.warnings: list[str] = []
        self._pending = list(self.nodes)

    # ---- self.play 接管 ----
    def play(self, *args, **kwargs) -> None:
        if self.event_index >= len(self.events):
            self.warnings.append("运行时 play/wait 调用数超过静态时间线,时间线可能失真")
            return
        ev = self.events[self.event_index]
        self.event_index += 1
        start_t = self.scene.time
        self.scene.compile_animation_data(*args, **kwargs)
        dur = float(self.scene.get_run_time(self.scene.animations))
        end_t = start_t + dur
        self._map_vars(ev)

        in_window = [n for n in self._pending if start_t - 1e-6 <= n["time"] < end_t - 1e-6]
        if not in_window:
            self._fast_forward(end_t)
            return

        self.scene.begin_animations()
        last_t = 0.0
        for node in in_window:
            target = node["time"] - start_t
            self._step_to(target, last_t)
            last_t = target
            self._capture(node)
            self._pending.remove(node)
        if last_t < dur - 1e-9:
            self._step_to(dur, last_t)
        for anim in self.scene.animations:
            anim.finish()
            anim.clean_up_from_scene(self.scene)
        self.scene.renderer.time = end_t
        self.scene.update_mobjects(0)

    # ---- self.wait 接管(Scene.wait 原实现是 self.play(Wait(...)),这里等价处理) ----
    def wait(self, duration: float = 1.0, stop_condition=None, frozen_frame=None) -> None:
        from manim import Wait
        if stop_condition is not None:
            self.warnings.append(f"wait(stop_condition=...) 探针按固定时长 {duration}s 处理")
        self.play(Wait(run_time=duration, frozen_frame=frozen_frame))

    # ---- 快进一个事件 ----
    def _fast_forward(self, end_t: float) -> None:
        self.scene.begin_animations()
        for anim in self.scene.animations:
            anim.finish()
            anim.clean_up_from_scene(self.scene)
        self.scene.renderer.time = end_t
        self.scene.update_mobjects(0)

    # ---- 步进到事件内相对时刻 t ----
    def _step_to(self, t: float, last_t: float) -> None:
        fps = max(1, int(self.scene.camera.frame_rate))
        n_steps = max(1, int(round((t - last_t) * fps)))
        for i in range(1, n_steps + 1):
            ti = last_t + (t - last_t) * i / n_steps
            self.scene.update_to_time(ti)
        if t - last_t > 1e-9:
            self.scene.update_to_time(t)

    # ---- 事件变量 → 运行时 mobject 实例映射 ----
    def _map_vars(self, ev: dict) -> None:
        vars_ = ev.get("vars", [])
        anims = list(self.scene.animations)
        if not vars_ or not anims:
            return
        # Transform 类动画:首变量 → mobject,次变量 → target_mobject
        if len(vars_) >= 2 and anims and any(a in TRANSFORM_ANIMS for a in ev.get("anims", [])):
            a0 = anims[0]
            if len(vars_) >= 1 and a0.mobject is not None:
                self.var_instances[vars_[0]] = a0.mobject
                self._inst_ids.add(id(a0.mobject))
            if len(vars_) >= 2:
                tgt = getattr(a0, "target_mobject", None) or (a0.target_mobject if hasattr(a0, "target_mobject") else None)
                if tgt is not None:
                    self.var_instances[vars_[1]] = tgt
                    self._inst_ids.add(id(tgt))
            return
        if len(vars_) == len(anims):
            for v, a in zip(vars_, anims):
                self._bind(v, a.mobject)
            return
        if len(vars_) == 1 and len(anims) == 1:
            self._bind(vars_[0], anims[0].mobject)
            return
        # 兜底:按顺序把未绑定的动画实例分给变量
        for v in vars_:
            for a in anims:
                if a.mobject is not None and id(a.mobject) not in self._inst_ids:
                    self._bind(v, a.mobject)
                    break

    def _bind(self, var: str, mobject) -> None:
        if mobject is None or var in self.var_instances:
            return
        self.var_instances[var] = mobject
        self._inst_ids.add(id(mobject))

    # ---- 节点取帧 + 元素数据 ----
    def _capture(self, node: dict) -> None:
        scene, cam = self.scene, self.scene.camera
        mobs = list(scene.mobjects) + list(scene.foreground_mobjects)
        try:
            cam.reset()
            cam.capture_mobjects(mobs, include_submobjects=True)
            img = cam.get_image()
        except Exception as exc:  # noqa: BLE001
            self.warnings.append(f"{node['id']} 取帧失败:{exc}")
            return
        fname = f"{node['id']}.png"
        img.save(self.out_dir / fname)
        elements = self._describe_elements()
        node.setdefault("capture_time", node["time"])
        self.captured.append({
            "id": node["id"],
            "time": node["time"],
            "image": fname,
            "introduced": node.get("introduced", []),
            "elements": elements,
        })

    # ---- 可见元素清单(只收有变量名或显式 set_name 的元素) ----
    def _describe_elements(self) -> list[dict]:
        cam = self.scene.camera
        family = self.scene.get_mobject_family_members()
        inst_to_var = {id(m): v for v, m in self.var_instances.items()}
        out: list[dict] = []
        for m in family:
            var, parent = self._find_var(m, inst_to_var)
            explicit = getattr(m, "name", "") or ""
            is_default = explicit in ("", m.__class__.__name__)
            if not var and is_default:
                continue
            pts_list = self._nondegenerate_points(m)
            if not pts_list:
                continue
            try:
                all_px = np.vstack([
                    cam.points_to_pixel_coords(fam, pts) for fam, pts in pts_list
                ])
                x0, y0 = all_px.min(axis=0)
                x1, y1 = all_px.max(axis=0)
                bbox = [int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))]
            except Exception:  # noqa: BLE001
                continue
            color, opacity = "", None
            try:
                if float(m.get_fill_opacity()) > 0:
                    color = str(m.get_fill_color().to_hex())
                elif float(m.get_stroke_opacity()) > 0:
                    color = str(m.get_stroke_color().to_hex())
            except Exception:  # noqa: BLE001
                pass
            try:
                opacity = round(float(m.get_fill_opacity()), 3)
            except Exception:  # noqa: BLE001
                pass
            name = explicit if not is_default else var
            out.append({
                "id": var or f"m{id(m):x}",
                "name": name,
                "type": m.__class__.__name__,
                "bbox": bbox,
                "color": color,
                "opacity": opacity,
                "z": int(getattr(m, "z_index", 0)),
                "parent": parent,
            })
        return out

    @staticmethod
    def _nondegenerate_points(m) -> list[tuple]:
        """取家族成员自身的点集,剔除退化成员(所有点重合,如未开始绘制的箭头尖)。

        Create(lag_ratio=1.0) 在低 alpha 时会让箭头尖 submobject 的所有点退化成同一个
        点并停在末端——若直接聚合 get_all_points(),未画出的部分会被算进 bbox。
        """
        pts_list: list[tuple] = []
        for fam in m.get_family():
            pts = getattr(fam, "points", None)
            if pts is None or len(pts) == 0:
                continue
            if len(pts) > 1 and np.allclose(pts, pts[0]):
                continue
            pts_list.append((fam, pts))
        return pts_list

    def _find_var(self, m, inst_to_var: dict[int, str]) -> tuple[str | None, str | None]:
        if id(m) in inst_to_var:
            return inst_to_var[id(m)], None
        for inst, var in self.var_instances.items():
            try:
                if m in inst.get_family():
                    return None, var
            except Exception:  # noqa: BLE001
                continue
        return None, None


def _find_scene_class(module, fallback_name: str | None) -> type | None:
    """优先用 spec_lock 声明的类名,否则自动发现模块内定义的 Scene 子类。"""
    import manim
    if fallback_name:
        cls = getattr(module, fallback_name, None)
        if isinstance(cls, type) and issubclass(cls, manim.Scene):
            return cls
    for name, obj in vars(module).items():
        if isinstance(obj, type) and issubclass(obj, manim.Scene) and obj.__module__ == module.__name__:
            return obj
    return None


def _load_scene_module(main_py: Path, scene_dir: str):
    """以独立模块名加载场景代码(其顶层 config 赋值即 env-gate,须先设 MANIM_LOW_RES)。"""
    spec = importlib.util.spec_from_file_location(f"probe_{scene_dir}", main_py)
    if spec is None or spec.loader is None:
        raise SystemExit(f"[错误] 无法加载 {main_py}")
    sys.path.insert(0, str(main_py.parent))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def probe_scene(main_py: Path, out_dir: Path, quality: str, class_hint: str | None) -> dict:
    os.environ["MANIM_LOW_RES"] = "1" if quality == "low" else "0"
    analysis = analyze_scene(main_py)
    module = _load_scene_module(main_py, main_py.parent.name)
    scene_cls = _find_scene_class(module, class_hint or analysis.get("scene_class"))
    if scene_cls is None:
        raise SystemExit(f"[错误] {main_py}:找不到可实例化的 Scene 类")

    scene = scene_cls()
    pixel_size = (int(scene.camera.pixel_width), int(scene.camera.pixel_height))
    out_dir.mkdir(parents=True, exist_ok=True)
    playback = ProbePlayback(scene, analysis, out_dir, pixel_size)

    # 接管 play/wait(实例属性遮蔽类方法)
    scene.play = playback.play  # type: ignore[method-assign]
    scene.wait = playback.wait  # type: ignore[method-assign]

    # 与正常渲染一样先调用 setup()(Scene.setup 默认空实现,直接调用无害)
    scene.setup()
    scene.construct()

    # 处理剩余节点(场景末帧等边界节点)
    for node in list(playback._pending):
        playback._capture(node)
        playback._pending.remove(node)
    scene.tear_down()

    captured = playback.captured
    payload = {
        "scene": main_py.parent.name,
        "class": scene_cls.__name__,
        "source": str(main_py),
        "duration": analysis["duration"],
        "pixel_size": pixel_size,
        "nodes": captured,
        "elements_by_var": analysis["elements_by_var"],
        "timeline": [{
            "kind": e["kind"], "line": e["line"], "start": e["start"], "end": e["end"],
            "vars": e["vars"], "anims": e["anims"], "run_time": e.get("run_time", 0.0),
        } for e in analysis["events"]],
        "warnings": analysis["warnings"] + playback.warnings,
    }
    (out_dir / "elements.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[完成] {main_py.parent.name}:{scene_cls.__name__} "
          f"时长 {analysis['duration']}s,{len(captured)} 节点,{pixel_size[0]}x{pixel_size[1]}")
    for w in playback.warnings:
        print(f"  [警告] {w}")
    return payload


# ============================================================
# 3. 项目级调度
# ============================================================

def parse_spec_lock(project: Path) -> dict[str, str]:
    """从 spec_lock.md ## scenes 节解析 dir → class(宽松正则,失败返回空表)。"""
    mapping: dict[str, str] = {}
    spec = project / "spec_lock.md"
    if not spec.exists():
        return mapping
    text = spec.read_text(encoding="utf-8")
    for line in text.splitlines():
        m_dir = re.search(r"dir\s*=\s*([\w-]+)", line)
        m_cls = re.search(r"class\s*=\s*(\w+)", line)
        if m_dir and m_cls:
            mapping[m_dir.group(1)] = m_cls.group(1)
    return mapping


def probe_project(project: Path, only_scene: str | None, quality: str, out_root: Path) -> None:
    scenes_root = project / "scenes"
    if not scenes_root.exists():
        raise SystemExit(f"[错误] 无 scenes 目录:{project}")
    class_map = parse_spec_lock(project)
    scene_dirs = sorted(d.name for d in scenes_root.iterdir() if (d / "main.py").exists())
    if only_scene:
        scene_dirs = [d for d in scene_dirs if d == only_scene]
        if not scene_dirs:
            raise SystemExit(f"[错误] 场景不存在:{only_scene}")

    # 与已有 index.json 合并(单场景重探针不丢其他场景的条目)
    idx_path = out_root / "index.json"
    old_scenes: dict[str, dict] = {}
    if idx_path.exists():
        try:
            old = json.loads(idx_path.read_text(encoding="utf-8"))
            old_scenes = {s["dir"]: s for s in old.get("scenes", []) if "dir" in s}
        except Exception:  # noqa: BLE001
            old_scenes = {}
    index = {"project": project.name, "quality": quality, "scenes": []}
    for d in scene_dirs:
        main_py = scenes_root / d / "main.py"
        out_dir = out_root / d
        try:
            payload = probe_scene(main_py, out_dir, quality, class_map.get(d))
            old_scenes[d] = {
                "dir": d,
                "class": payload["class"],
                "duration": payload["duration"],
                "nodes": len(payload["nodes"]),
                "elements_json": f"{d}/elements.json",
                "pixel_size": payload["pixel_size"],
            }
        except Exception as exc:  # noqa: BLE001
            print(f"[失败] {d}:{exc}")
            old_scenes[d] = {"dir": d, "error": str(exc)}
    index["scenes"] = [old_scenes[d] for d in sorted(old_scenes)]
    out_root.mkdir(parents=True, exist_ok=True)
    idx_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for s in index["scenes"] if "error" not in s)
    print(f"\n===== 探针完成:{ok}/{len(index['scenes'])} 场景,输出 {out_root} =====")


def probe_file(main_py: Path, class_name: str | None, quality: str, out_root: Path) -> None:
    """探针任意单个 Manim 场景文件(不要求本仓库的 scenes/<dir>/main.py 布局)。

    场景名取文件名主干;输出 <out_root>/<stem>/elements.json + node PNG,
    并合并更新 <out_root>/index.json(可与多次调用叠加)。
    """
    scene_name = main_py.stem or "scene"
    out_dir = out_root / scene_name
    try:
        payload = probe_scene(main_py, out_dir, quality, class_name)
    except Exception as exc:  # noqa: BLE001
        print(f"[失败] {scene_name}:{exc}")
        sys.exit(1)
    idx_path = out_root / "index.json"
    old_scenes: dict[str, dict] = {}
    if idx_path.exists():
        try:
            old = json.loads(idx_path.read_text(encoding="utf-8"))
            old_scenes = {s["dir"]: s for s in old.get("scenes", []) if "dir" in s}
        except Exception:  # noqa: BLE001
            old_scenes = {}
    old_scenes[scene_name] = {
        "dir": scene_name,
        "class": payload["class"],
        "duration": payload["duration"],
        "nodes": len(payload["nodes"]),
        "elements_json": f"{scene_name}/elements.json",
        "pixel_size": payload["pixel_size"],
    }
    out_root.mkdir(parents=True, exist_ok=True)
    idx_path.write_text(
        json.dumps({"project": scene_name, "quality": quality,
                    "scenes": [old_scenes[d] for d in sorted(old_scenes)]},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[完成] {scene_name}:{payload['class']} 时长 {payload['duration']}s,"
          f"{len(payload['nodes'])} 节点,输出 {out_root}")


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "analyze":
        analysis = analyze_scene(Path(sys.argv[2]))
        print(json.dumps({
            "scene_class": analysis["scene_class"],
            "duration": analysis["duration"],
            "nodes": analysis["nodes"],
            "events": analysis["events"],
            "elements_by_var": analysis["elements_by_var"],
            "warnings": analysis["warnings"],
        }, ensure_ascii=False, indent=2))
        return
    if cmd == "file":
        main_py = Path(sys.argv[2]).resolve()
        class_name, quality = None, "low"
        out_root = main_py.parent / "docs/review/preview"
        if "--class" in sys.argv:
            class_name = sys.argv[sys.argv.index("--class") + 1]
        if "--quality" in sys.argv:
            quality = sys.argv[sys.argv.index("--quality") + 1]
        if "--out" in sys.argv:
            out_root = Path(sys.argv[sys.argv.index("--out") + 1])
        probe_file(main_py, class_name, quality, Path(out_root))
        return
    if cmd != "probe":
        print(__doc__)
        sys.exit(1)
    project = Path(sys.argv[2]).resolve()
    only_scene, quality, out_root = None, "low", project / "docs/review/preview"
    if "--scene" in sys.argv:
        only_scene = sys.argv[sys.argv.index("--scene") + 1]
    if "--quality" in sys.argv:
        quality = sys.argv[sys.argv.index("--quality") + 1]
    if "--out" in sys.argv:
        out_root = Path(sys.argv[sys.argv.index("--out") + 1])
    probe_project(project, only_scene, quality, Path(out_root))


if __name__ == "__main__":
    main()
