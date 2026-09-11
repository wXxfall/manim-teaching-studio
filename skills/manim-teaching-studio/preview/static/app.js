/* Manim Teaching Studio 画面预览 · 前端逻辑(vanilla JS,复刻 ppt-master svg_editor 交互模式) */
"use strict";

const state = {
  project: null,
  scenes: [],          // [{dir, class, duration, nodes, error, elements_mtime}]
  sceneData: null,     // 当前场景 elements.json
  sceneDir: null,
  node: null,          // 当前节点 {id, time, image, introduced, elements}
  selected: new Set(), // 选中的元素 id
  ops: [],             // 当前场景待提交的结构操作
  opsByScene: {},      // 各场景未提交操作(切换场景不丢失)
  freeByScene: {},     // 各场景回炉文本(切换场景不丢失)
  submitted: [],       // 已落盘提交队列(来自服务器)
  zoom: 1,
  pollTimer: null,
  lastMtime: 0,
  playlist: [],        // 总预览播放列表 [{dir, video, class}]
  playIdx: 0,
  suppressClick: false,
};

const $ = (sel) => document.querySelector(sel);

/* ---------------- 基础请求 ---------------- */
async function api(path, options) {
  const res = await fetch(path, options);
  return res.json();
}

/* ---------------- 场景 / 节点加载 ---------------- */
async function init() {
  const cfg = await api("/api/config");
  state.project = cfg.project;
  $("#project-name").textContent = cfg.project;
  // 有探针数据的场景(elements_json)或失败场景(error)都保留展示
  state.scenes = (cfg.scenes || []).filter((s) => !s.error || s.elements_json !== undefined);
  if (!state.scenes.length) {
    $("#scene-list").innerHTML =
      '<div class="scene-item err">暂无探针数据<br>请先运行:<br>python scene_probe.py probe &lt;项目&gt;</div>';
    return;
  }
  renderScenes();
  await selectScene(state.scenes[0].dir);
  startPolling();
  bindControls();
  loadReworkState();
}

function renderScenes() {
  const box = $("#scene-list");
  box.innerHTML = "";
  for (const s of state.scenes) {
    const el = document.createElement("div");
    el.className = "scene-item" + (s.dir === state.sceneDir ? " active" : "") + (s.error ? " err" : "");
    const local = (state.opsByScene[s.dir] || []).length;
    const submitted = state.submitted.filter((it) => it.scene === s.dir).length;
    const badge = local || submitted
      ? `<span class="scene-badge${submitted ? " done" : ""}">${submitted ? "✓" : ""}${local + submitted} 项修改</span>`
      : "";
    el.innerHTML = `<div class="scene-head"><span>${s.dir}</span>${badge}</div>
      <div class="meta">${s.class || ""} · ${s.duration ?? 0}s · ${s.nodes ?? 0} 节点${s.error ? " · 失败" : ""}</div>`;
    el.onclick = () => selectScene(s.dir);
    box.appendChild(el);
  }
}

async function selectScene(dir) {
  const switched = state.sceneDir !== null && state.sceneDir !== dir;
  if (switched) {
    // 跨场景保存:未提交操作与回炉文本按场景归档,切换回来不丢失
    state.opsByScene[state.sceneDir] = state.ops;
    state.freeByScene[state.sceneDir] = $("#rework-text").value;
  }
  state.sceneDir = dir;
  state.selected.clear();
  state.node = null;
  state.ops = state.opsByScene[dir] || [];
  $("#rework-text").value = state.freeByScene[dir] || "";
  renderChips();
  renderScenes();
  const data = await api(`/api/scene/${encodeURIComponent(dir)}`);
  if (data.error) {
    $("#node-list").innerHTML = `<div class="scene-item err">${data.error}</div>`;
    return;
  }
  state.sceneData = data;
  state.lastMtime = state.scenes.find((s) => s.dir === dir)?.elements_mtime || 0;
  renderNodes();
  const first = data.nodes?.[0];
  if (first) selectNode(first);
}

function renderNodes() {
  const box = $("#node-list");
  box.innerHTML = "";
  for (const n of state.sceneData.nodes || []) {
    const el = document.createElement("div");
    el.className = "node-item" + (state.node && state.node.id === n.id ? " active" : "");
    const dot = n.introduced?.length ? '<span class="dot" title="本节点新出现元素"></span>' : "";
    el.innerHTML = `${dot}<img src="/preview/${encodeURIComponent(state.sceneDir)}/${encodeURIComponent(n.image)}" loading="lazy">
      <div class="cap"><span>${n.id}</span><span>${n.time}s</span></div>`;
    el.onclick = () => selectNode(n);
    box.appendChild(el);
  }
}

function selectNode(n) {
  state.node = n;
  state.selected.clear();
  renderNodes();
  $("#node-image").src = `/preview/${encodeURIComponent(state.sceneDir)}/${encodeURIComponent(n.image)}`;
  $("#current-loc").textContent = `${state.sceneDir} · ${n.id} · t=${n.time}s`;
  renderOverlays();
  updateSelectionPanel();
  applyZoom();
}

/* ---------------- 画布覆盖层 ---------------- */
function renderOverlays() {
  const layer = $("#overlay-layer");
  layer.innerHTML = "";
  const els = state.node?.elements || [];
  const introduced = new Set(state.node?.introduced || []);
  // 后面画的盖住前面的:按 z 升序绘制,点击命中时取最上层
  const sorted = [...els].sort((a, b) => (a.z ?? 0) - (b.z ?? 0));
  for (const e of sorted) {
    const [x0, y0, x1, y1] = e.bbox;
    let w = Math.max(x1 - x0, 1);
    let h = Math.max(y1 - y0, 1);
    if (h < 6) { h = 6; } // 线条类元素加高便于点击
    const ov = document.createElement("div");
    ov.className = "element-overlay" + (introduced.has(e.id) ? " introduced" : "");
    ov.dataset.id = e.id;
    ov.style.left = `${x0}px`;
    ov.style.top = `${Math.max(y0 - (h - (y1 - y0)) / 2, 0)}px`;
    ov.style.width = `${w}px`;
    ov.style.height = `${h}px`;
    ov.title = `${e.id}(${e.name || e.type})\n拖拽可直接移动`;
    ov.addEventListener("click", (ev) => {
      ev.stopPropagation();
      if (state.suppressClick) {
        state.suppressClick = false;
        return;
      }
      if (ev.ctrlKey || ev.metaKey) {
        if (state.selected.has(e.id)) state.selected.delete(e.id);
        else state.selected.add(e.id);
      } else {
        state.selected.clear();
        state.selected.add(e.id);
      }
      refreshSelectionUI();
    });
    ov.addEventListener("mousedown", (ev) => {
      if (ev.button === 0) startDrag(ev, e);
    });
    layer.appendChild(ov);
  }
  applyGhostPreview();
  // 点击空白取消选择(只挂一次)
  const frame = layer.parentElement;
  if (!frame.dataset.blankBound) {
    frame.dataset.blankBound = "1";
    frame.addEventListener("click", (ev) => {
      if (ev.target === $("#node-image") || ev.target === layer) {
        state.selected.clear();
        refreshSelectionUI();
      }
    });
  }
}

/* ---------------- 鼠标拖拽移动元素(松手生成 shift 操作,自动累加) ---------------- */
function startDrag(ev, e) {
  const layer = $("#overlay-layer");
  const zoom = state.zoom || 1;
  // 按下即选中(与点击语义一致);已选中的多选元素一起拖
  if (!state.selected.has(e.id)) {
    if (!ev.ctrlKey && !ev.metaKey) state.selected.clear();
    state.selected.add(e.id);
    refreshSelectionUI();
  }
  const els = state.node?.elements || [];
  const byId = Object.fromEntries(els.map((x) => [x.id, x]));
  const ids = [...state.selected].filter((id) => byId[id]);
  const startX = ev.clientX, startY = ev.clientY;
  let moved = { x: 0, y: 0 };
  let dragging = false;
  const pxu = (state.sceneData?.pixel_size?.[1] ?? 480) / 8;
  // 已提交操作产生的幽灵位移/缩放:拖拽从幽灵位置继续,不跳回原位
  const priors = {};
  for (const id of ids) {
    let dx = 0, dy = 0, s = 1;
    for (const o of state.ops.filter((o) => o.element === id)) {
      if (o.op === "shift") { dx += o.dx || 0; dy += o.dy || 0; }
      else if (o.op === "scale") s *= o.value || 1;
    }
    priors[id] = { x: dx * pxu, y: -dy * pxu, s };
  }
  const ovs = ids.map((id) => layer.querySelector(`.element-overlay[data-id="${CSS.escape(id)}"]`)).filter(Boolean);

  const onMove = (me) => {
    const dx = (me.clientX - startX) / zoom;
    const dy = (me.clientY - startY) / zoom;
    if (!dragging && Math.hypot(dx, dy) < 3) return;
    dragging = true;
    moved = { x: dx, y: dy };
    for (const ovl of ovs) {
      const pr = priors[ovl.dataset.id] || { x: 0, y: 0, s: 1 };
      ovl.style.transform = `translate(${pr.x + dx}px, ${pr.y + dy}px)${pr.s !== 1 ? ` scale(${pr.s})` : ""}`;
      ovl.classList.add("dragging");
    }
  };
  const onUp = () => {
    document.removeEventListener("mousemove", onMove);
    document.removeEventListener("mouseup", onUp);
    for (const ovl of ovs) ovl.classList.remove("dragging");
    if (!dragging) return;
    state.suppressClick = true; // 拖拽后抑制合成 click
    const round3 = (v) => Math.round(v * 1000) / 1000;
    const dxu = round3(moved.x / pxu);
    const dyu = round3(-moved.y / pxu);
    for (const id of ids) {
      addOp(id, "shift", { dx: dxu, dy: dyu },
        `拖拽移动 ${dxu > 0 ? "右" : dxu < 0 ? "左" : ""}${Math.abs(dxu)} ${dyu > 0 ? "上" : dyu < 0 ? "下" : ""}${Math.abs(dyu)}`.trim());
    }
  };
  document.addEventListener("mousemove", onMove);
  document.addEventListener("mouseup", onUp);
}

/* ---------------- 即时幽灵预览(不需重渲染) ---------------- */
function applyGhostPreview() {
  if (!state.node) return;
  const layer = $("#overlay-layer");
  layer.querySelectorAll(".ghost-arrow").forEach((a) => a.remove());
  const els = state.node.elements || [];
  const byId = Object.fromEntries(els.map((e) => [e.id, e]));
  const overlays = [...layer.querySelectorAll(".element-overlay")];
  if (!overlays.length) return;

  // 按有效 z 重排(后 append = 盖在上层),层级操作即时可见
  const effZ = (id) => {
    const zOp = [...state.ops].reverse().find((o) => o.element === id && o.op === "set_z_index");
    return zOp ? zOp.value : (byId[id]?.z ?? 0);
  };
  overlays.sort((a, b) => effZ(a.dataset.id) - effZ(b.dataset.id));
  overlays.forEach((ov) => layer.appendChild(ov));

  // 位置/大小/颜色/深浅 即时预览(虚线框 = 提交重渲染后的大致效果)
  const pxu = (state.sceneData?.pixel_size?.[1] ?? 480) / 8; // 画布高度 8 Manim 单位
  for (const ov of overlays) {
    const id = ov.dataset.id;
    const e = byId[id];
    if (!e) continue;
    const ops = state.ops.filter((o) => o.element === id);
    if (!ops.length) continue;
    let dx = 0, dy = 0, s = 1, color = null, opacity = null;
    for (const o of ops) {
      if (o.op === "shift") { dx += o.dx || 0; dy += o.dy || 0; }
      else if (o.op === "scale") s *= o.value || 1;
      else if (o.op === "set_color") color = o.value;
      else if (o.op === "set_opacity") opacity = o.value;
    }
    const tdx = dx * pxu, tdy = -dy * pxu;
    ov.style.transform = [tdx || tdy ? `translate(${tdx}px, ${tdy}px)` : "", s !== 1 ? `scale(${s})` : ""]
      .filter(Boolean).join(" ");
    ov.style.transformOrigin = "center";
    ov.classList.add("ghosted");
    if (color) ov.style.borderColor = color;
    if (opacity !== null) ov.style.opacity = String(Math.min(1, Math.max(0.15, opacity)));
    // 位移虚线箭头:原位置 → 新位置
    if (tdx || tdy) {
      const [x0, y0, x1, y1] = e.bbox;
      const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
      const nx = cx + tdx, ny = cy + tdy;
      const dist = Math.hypot(nx - cx, ny - cy);
      if (dist > 1) {
        const arr = document.createElement("div");
        arr.className = "ghost-arrow";
        arr.style.left = `${cx}px`;
        arr.style.top = `${cy}px`;
        arr.style.width = `${dist}px`;
        arr.style.transformOrigin = "0 50%";
        arr.style.transform = `rotate(${Math.atan2(ny - cy, nx - cx)}rad)`;
        layer.appendChild(arr);
      }
    }
  }
}

function refreshSelectionUI() {
  document.querySelectorAll(".element-overlay").forEach((ov) => {
    ov.classList.toggle("selected", state.selected.has(ov.dataset.id));
  });
  applyGhostPreview();
  updateSelectionPanel();
}

function applyZoom() {
  const z = state.zoom;
  const frame = $("#canvas-frame");
  const img = $("#node-image");
  frame.style.transform = `scale(${z})`;
  img.style.width = `${state.sceneData?.pixel_size?.[0] ?? 854}px`;
  img.style.height = `${state.sceneData?.pixel_size?.[1] ?? 480}px`;
  document.querySelectorAll(".zoom-group button").forEach((b) =>
    b.classList.toggle("active", Number(b.dataset.zoom) === z)
  );
}

/* ---------------- 右侧面板 ---------------- */
function updateSelectionPanel() {
  const list = $("#sel-list");
  const ctrl = $("#controls");
  const hint = $("#no-sel-hint");
  list.innerHTML = "";
  const els = state.node?.elements || [];
  const byId = Object.fromEntries(els.map((e) => [e.id, e]));
  const selEls = [...state.selected].map((id) => byId[id]).filter(Boolean);
  $("#sel-count").textContent = selEls.length ? `(${selEls.length})` : "";

  if (!selEls.length) {
    ctrl.classList.add("hidden");
    hint.classList.remove("hidden");
    updateReworkContext([]);
    return;
  }
  hint.classList.add("hidden");
  ctrl.classList.remove("hidden");

  for (const e of selEls) {
    const row = document.createElement("div");
    row.className = "sel-item";
    row.innerHTML = `<span class="swatch-dot" style="background:${e.color || "#888"}"></span>
      <span class="nm">${e.name || e.id}</span><span class="tp">${e.type}</span>`;
    list.appendChild(row);
  }

  const first = selEls[0];
  const anyText = selEls.some((e) => e.type === "Text");
  $("#font-size-group").classList.toggle("hidden", !anyText);
  $("#opacity-range").value = String(first.opacity ?? 1);
  $("#opacity-val").textContent = `=${first.opacity ?? 1}`;
  $("#color-pick").value = first.color || "#ffffff";

  const ref = $("#code-ref");
  const meta = state.sceneData?.elements_by_var?.[first.id];
  if (meta) {
    const entrance = meta.entrance
      ? `入场:第 ${meta.entrance.line} 行 · run_time ${meta.entrance.run_time}s`
      : "";
    ref.innerHTML = `<b>${first.id}</b><br>代码第 ${meta.line} 行${meta.phase ? " · " + meta.phase : ""}<br>${entrance}`;
  } else {
    ref.innerHTML = `<b>${first.id}</b><br>无代码行号映射`;
  }
  updateReworkContext(selEls);
}

/* 回炉文本框语境:选中元素 → 元素级;否则 → 场景级 */
function updateReworkContext(selEls) {
  const box = $("#rework-text");
  const ctx = $("#rework-context");
  if (selEls && selEls.length) {
    const names = selEls.slice(0, 3).map((e) => e.name || e.id).join("、") + (selEls.length > 3 ? " 等" : "");
    ctx.textContent = `元素:${names}`;
    box.placeholder = `对 ${names} 的要求,例如「往上移一点,加粗一些」…`;
  } else {
    ctx.textContent = `场景:${state.sceneDir || ""}`;
    box.placeholder = `对场景 ${state.sceneDir || ""} 的整体要求,例如「标题和公式不要重叠」…`;
  }
}

/* ---------------- 控件 → 操作 ---------------- */
function addOp(element, op, extra, note) {
  const existing = state.ops.find((o) => o.element === element && o.op === op);
  if (!existing) {
    state.ops.push({ element, op, ...extra, note });
    renderChips();
    return;
  }
  // 同元素同类型操作:可累加型(位移/缩放/字号)逐次叠加,绝对值型(颜色/透明度/层级/时长)覆盖
  if (op === "shift") {
    existing.dx = (existing.dx || 0) + (extra.dx || 0);
    existing.dy = (existing.dy || 0) + (extra.dy || 0);
    const parts = [];
    if (existing.dx) parts.push(`${existing.dx > 0 ? "右" : "左"} ${Math.abs(existing.dx).toFixed(2)}`);
    if (existing.dy) parts.push(`${existing.dy > 0 ? "上" : "下"} ${Math.abs(existing.dy).toFixed(2)}`);
    existing.note = `累计移动 ${parts.join("、")}`;
  } else if (op === "scale") {
    existing.value = +(existing.value * extra.value).toFixed(3);
    existing.note = `累计缩放 ×${existing.value}`;
  } else if (op === "set_font_size") {
    existing.delta = (existing.delta || 0) + (extra.delta || 0);
    existing.note = `字号累计 ${existing.delta > 0 ? "+" : ""}${existing.delta}`;
  } else {
    Object.assign(existing, extra, { note });
  }
  renderChips();
}

function bindControls() {
  // 位置按钮:步长来自下拉框
  document.querySelectorAll("[data-op='shift']").forEach((btn) => {
    btn.addEventListener("click", () => {
      const step = Number($("#shift-step").value || 0.1);
      const dx = Number(btn.dataset.dx) * (step / 0.1);
      const dy = Number(btn.dataset.dy) * (step / 0.1);
      const dir = dx > 0 ? "右" : dx < 0 ? "左" : dy > 0 ? "上" : "下";
      forEachSelected((e) => addOp(e.id, "shift", { dx, dy }, `移动${dir} ${step}`));
    });
  });

  // 颜色
  document.querySelectorAll("[data-op='set_color']").forEach((btn) => {
    btn.addEventListener("click", () => {
      forEachSelected((e) => addOp(e.id, "set_color", { value: btn.dataset.value }, `改色 ${btn.dataset.value}`));
    });
  });
  $("#color-pick").addEventListener("input", (ev) => {
    forEachSelected((e) => addOp(e.id, "set_color", { value: ev.target.value }, `改色 ${ev.target.value}`));
  });

  // 透明度
  $("#opacity-range").addEventListener("input", (ev) => {
    const v = Number(ev.target.value);
    $("#opacity-val").textContent = `=${v}`;
    forEachSelected((e) => addOp(e.id, "set_opacity", { value: v }, `透明度 ${v}`));
  });

  // 大小 / 时长 / 字号 / 层级
  document.querySelectorAll("[data-op='scale']").forEach((btn) =>
    btn.addEventListener("click", () => {
      const v = Number(btn.dataset.value);
      forEachSelected((e) => addOp(e.id, "scale", { value: v }, `缩放 ×${v}`));
    })
  );
  document.querySelectorAll("[data-op='set_run_time']").forEach((btn) =>
    btn.addEventListener("click", () => {
      const delta = Number(btn.dataset.value);
      forEachSelected((e) => {
        // 累加:以当前已设值为基准,再次点击继续增减
        const cur = state.ops.find((o) => o.element === e.id && o.op === "set_run_time");
        const meta = state.sceneData?.elements_by_var?.[e.id]?.entrance;
        const base = cur?.value ?? meta?.run_time ?? 1.0;
        const v = Math.max(0.2, Math.round((base + delta) * 10) / 10);
        addOp(e.id, "set_run_time", { value: v }, `入场时长 ${v}s`);
      });
    })
  );
  document.querySelectorAll("[data-op='set_font_size']").forEach((btn) =>
    btn.addEventListener("click", () => {
      const delta = Number(btn.dataset.value);
      forEachSelected((e) => {
        if (e.type !== "Text") return;
        addOp(e.id, "set_font_size", { delta }, `字号 ${delta > 0 ? "+" : ""}${delta}`);
      });
    })
  );
  document.querySelectorAll("[data-op='set_z_index']").forEach((btn) =>
    btn.addEventListener("click", () => {
      const delta = Number(btn.dataset.value);
      forEachSelected((e) => {
        const v = (e.z ?? 0) + delta;
        addOp(e.id, "set_z_index", { value: v }, `层级 → ${v}`);
      });
    })
  );

  // 主题切换(白天/黑夜)
  $("#theme-btn").addEventListener("click", () => {
    const cur = document.documentElement.getAttribute("data-theme") || "light";
    applyTheme(cur === "light" ? "dark" : "light");
  });

  // PPT 式排版对齐
  document.querySelectorAll("[data-align]").forEach((btn) =>
    btn.addEventListener("click", () => doAlign(btn.dataset.align))
  );

  // 总预览:连续播放全部场景视频
  $("#play-all-btn").addEventListener("click", () => openPlaylist(0));
  $("#video-close").addEventListener("click", closePlaylist);
  $("#video-prev").addEventListener("click", () => playlistStep(-1));
  $("#video-next").addEventListener("click", () => playlistStep(1));
  $("#player").addEventListener("ended", () => playlistStep(1));

  // 缩放
  document.querySelectorAll(".zoom-group button").forEach((btn) =>
    btn.addEventListener("click", () => {
      state.zoom = Number(btn.dataset.zoom);
      applyZoom();
    })
  );

  // 键盘
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") {
      state.selected.clear();
      refreshSelectionUI();
    }
  });

  // 回炉提交/清空/已提交清单
  $("#submit-btn").addEventListener("click", submitRework);
  $("#submitted-btn").addEventListener("click", toggleSubmitPanel);
  $("#submit-panel-close").addEventListener("click", toggleSubmitPanel);
  $("#clear-btn").addEventListener("click", async () => {
    // 清空 = 当前场景的未提交操作 + 文本 + 该场景的已落盘条目
    state.ops = [];
    state.opsByScene[state.sceneDir] = [];
    state.freeByScene[state.sceneDir] = "";
    $("#rework-text").value = "";
    renderChips();
    const r = await api(`/api/rework/clear?scene=${encodeURIComponent(state.sceneDir)}`, { method: "POST" });
    state.submitted = r.items || [];
    renderScenes();
    renderSubmitPanel();
    setStatus(`已清空 ${state.sceneDir} 的修改(未提交 + 已落盘)`, "");
  });
  $("#exit-btn").addEventListener("click", async () => {
    await api("/api/shutdown", { method: "POST" }).catch(() => {});
    setStatus("预览已退出,可关闭本页", "");
  });
}

function forEachSelected(fn) {
  if (!state.selected.size) return;
  const els = state.node?.elements || [];
  const byId = Object.fromEntries(els.map((e) => [e.id, e]));
  for (const id of state.selected) {
    const e = byId[id];
    if (e) fn(e);
  }
}

/* ---------------- 主题(白天/黑夜) ---------------- */
function applyTheme(t) {
  document.documentElement.setAttribute("data-theme", t);
  $("#theme-btn").textContent = t === "dark" ? "☀️" : "🌙";
  try { localStorage.setItem("mts-theme", t); } catch { /* 忽略 */ }
}

/* ---------------- PPT 式排版对齐(生成 shift 操作,可幽灵预览/提交重渲染) ---------------- */
function doAlign(kind) {
  const els = state.node?.elements || [];
  const byId = Object.fromEntries(els.map((e) => [e.id, e]));
  const sel = [...state.selected].map((id) => byId[id]).filter(Boolean);
  if (!sel.length) return;
  const u = (state.sceneData?.pixel_size?.[1] ?? 480) / 8; // 画布高度 8 Manim 单位
  const w = state.sceneData?.pixel_size?.[0] ?? 854;
  const h = state.sceneData?.pixel_size?.[1] ?? 480;
  const round3 = (v) => Math.round(v * 1000) / 1000;
  const boxes = sel.map((e) => ({
    e, b: e.bbox, cx: (e.bbox[0] + e.bbox[2]) / 2, cy: (e.bbox[1] + e.bbox[3]) / 2,
  }));
  const uni = {
    x0: Math.min(...boxes.map((x) => x.b[0])),
    x1: Math.max(...boxes.map((x) => x.b[2])),
    y0: Math.min(...boxes.map((x) => x.b[1])),
    y1: Math.max(...boxes.map((x) => x.b[3])),
  };
  const notes = {
    left: "左对齐", hcenter: "水平居中", right: "右对齐", "canvas-h": "画布水平居中",
    top: "顶端对齐", vcenter: "垂直居中", bottom: "底端对齐", "canvas-v": "画布垂直居中",
  };

  if (kind === "dist-h" || kind === "dist-v") {
    if (boxes.length < 3) {
      setStatus("分布需要至少选中 3 个元素(Ctrl+点击多选)", "err");
      return;
    }
    if (kind === "dist-h") {
      const sorted = [...boxes].sort((a, b) => a.cx - b.cx);
      for (let i = 0; i < sorted.length; i++) {
        const tx = sorted[0].cx + ((sorted[sorted.length - 1].cx - sorted[0].cx) * i) / (sorted.length - 1);
        const dx = (tx - sorted[i].cx) / u;
        if (Math.abs(dx) > 0.001) addOp(sorted[i].e.id, "shift", { dx: round3(dx), dy: 0 }, "横向分布");
      }
    } else {
      const sorted = [...boxes].sort((a, b) => a.cy - b.cy);
      for (let i = 0; i < sorted.length; i++) {
        const ty = sorted[0].cy + ((sorted[sorted.length - 1].cy - sorted[0].cy) * i) / (sorted.length - 1);
        const dy = -(ty - sorted[i].cy) / u;
        if (Math.abs(dy) > 0.001) addOp(sorted[i].e.id, "shift", { dx: 0, dy: round3(dy) }, "纵向分布");
      }
    }
    return;
  }

  const isY = ["top", "vcenter", "bottom", "canvas-v"].includes(kind);
  const refMap = { left: "x0", hcenter: "cx", right: "x1", "canvas-h": "cx" };
  const tgtMap = { left: uni.x0, hcenter: uni.cx, right: uni.x1, "canvas-h": w / 2 };
  const refMapY = { top: "y0", vcenter: "cy", bottom: "y1", "canvas-v": "cy" };
  const tgtMapY = { top: uni.y0, vcenter: uni.cy, bottom: uni.y1, "canvas-v": h / 2 };
  for (const x of boxes) {
    let dx = 0, dy = 0;
    if (isY) {
      const ref = x[refMapY[kind]];
      dy = -(tgtMapY[kind] - ref) / u;
    } else {
      const ref = x[refMap[kind]];
      dx = (tgtMap[kind] - ref) / u;
    }
    if (Math.abs(dx) > 0.001 || Math.abs(dy) > 0.001) {
      addOp(x.e.id, "shift", { dx: round3(dx), dy: round3(dy) }, notes[kind]);
    }
  }
}

/* ---------------- 底部回炉栏 ---------------- */
function renderChips() {
  const box = $("#op-chips");
  box.innerHTML = "";
  $("#ops-count").textContent = state.ops.length ? `(${state.ops.length} 项)` : "";
  if (!state.ops.length) {
    box.innerHTML = '<span class="chips-empty">点选元素并用右侧控件 / 拖拽调整,操作会显示在这里</span>';
  }
  for (const op of state.ops) {
    const chip = document.createElement("span");
    chip.className = "op-chip";
    chip.innerHTML = `<span>${op.element} · ${op.note}</span><span class="x" data-i="${state.ops.indexOf(op)}">×</span>`;
    chip.querySelector(".x").onclick = () => {
      state.ops.splice(state.ops.indexOf(op), 1);
      renderChips();
    };
    box.appendChild(chip);
  }
  applyGhostPreview(); // 增删操作即时反映到画布幽灵预览
}

async function submitRework() {
  const freeText = $("#rework-text").value.trim();
  if (!state.ops.length && !freeText) {
    setStatus("先调整控件或填写要求再提交", "err");
    return;
  }
  // 提交语境:选中了元素 → 元素级;否则场景级
  const targets = state.selected.size ? [...state.selected] : ["scene"];
  const btn = $("#submit-btn");
  btn.disabled = true;
  btn.textContent = "提交中…";
  const res = await api("/api/rework", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      scene: state.sceneDir,
      node: state.node?.id || "",
      ops: state.ops,
      free_text: freeText,
      targets,
    }),
  });
  btn.disabled = false;
  btn.textContent = "提交落盘";
  if (res.ok) {
    state.submitted = res.items || [];
    state.opsByScene[state.sceneDir] = state.ops;
    state.freeByScene[state.sceneDir] = freeText;
    renderScenes();
    renderSubmitPanel();
    setStatus(`✅ ${state.sceneDir} 已落盘(${state.ops.length} 项操作${freeText ? " + 自由文本" : ""});回到对话说「应用修改」将应用全部 ${state.submitted.length} 项`, "");
    // 提交成功脉冲动画
    $("#submitted-btn").classList.add("pulse");
    setTimeout(() => $("#submitted-btn").classList.remove("pulse"), 900);
  } else {
    setStatus("提交失败:" + (res.error || "未知错误"), "err");
  }
}

/* ---------------- 已提交清单(可视化) ---------------- */
function renderSubmitPanel() {
  $("#submitted-count").textContent = state.submitted.length;
  const box = $("#submit-list");
  box.innerHTML = "";
  if (!state.submitted.length) {
    box.innerHTML = '<div class="submit-empty">还没有提交的修改。在各场景点选元素调参数,点「提交落盘」。</div>';
    return;
  }
  for (const it of state.submitted) {
    const row = document.createElement("div");
    row.className = "submit-item";
    const opsTxt = (it.ops || []).map((o) => `${o.element}·${o.note}`).join("; ");
    const freeTxt = it.free_text ? ` · 要求:「${it.free_text.length > 40 ? it.free_text.slice(0, 40) + "…" : it.free_text}」` : "";
    row.innerHTML = `
      <div class="submit-head">
        <span class="submit-scene">${it.scene}</span>
        <span class="submit-node">${it.node || ""} · ${it.ops?.length || 0} 项操作${freeTxt}</span>
        <button class="submit-del" data-scene="${it.scene}">✕</button>
      </div>
      <div class="submit-ops">${opsTxt || "仅自由文本"}</div>`;
    row.querySelector(".submit-del").onclick = async (ev) => {
      ev.stopPropagation();
      const r = await api(`/api/rework/clear?scene=${encodeURIComponent(it.scene)}`, { method: "POST" });
      state.submitted = r.items || [];
      renderSubmitPanel();
      renderScenes();
    };
    box.appendChild(row);
  }
}

function toggleSubmitPanel() {
  const p = $("#submit-panel");
  p.classList.toggle("hidden");
  if (!p.classList.contains("hidden")) renderSubmitPanel();
}

async function loadReworkState() {
  const res = await api("/api/rework");
  state.submitted = res.items || [];
  const items = state.submitted;
  if (items.length) {
    // 按场景恢复未应用的操作与文本(服务端队列 = 各场景最后一次提交)
    const merged = {};
    for (const it of items) {
      merged[it.scene] = { ops: it.ops || [], free_text: it.free_text || "" };
    }
    for (const [scene, v] of Object.entries(merged)) {
      state.opsByScene[scene] = v.ops;
      state.freeByScene[scene] = v.free_text;
    }
    state.ops = state.opsByScene[state.sceneDir] || [];
    $("#rework-text").value = state.freeByScene[state.sceneDir] || "";
    renderChips();
    renderScenes();
    renderSubmitPanel();
    setStatus(`已恢复 ${items.length} 项未应用的提交(可继续编辑;回到对话说「应用修改」)`, "");
  } else {
    // 磁盘上已无待应用修改(已被主代理应用并清空)→ 清掉本地状态
    state.ops = [];
    state.opsByScene = {};
    state.freeByScene = {};
    renderChips();
    applyGhostPreview();
    renderScenes();
    renderSubmitPanel();
  }
}

function setStatus(msg, cls) {
  const el = $("#rework-status");
  el.textContent = msg;
  el.className = cls;
}

/* ---------------- 总预览:连续播放全部场景视频 ---------------- */
function playlistVideos() {
  return (state.scenes || []).filter((s) => s.video).map((s) => ({ dir: s.dir, class: s.class, video: s.video }));
}

function openPlaylist(i) {
  state.playlist = playlistVideos();
  if (!state.playlist.length) {
    setStatus("暂无渲染好的视频(先运行低清渲染)", "err");
    return;
  }
  state.playIdx = Math.min(Math.max(i, 0), state.playlist.length - 1);
  $("#video-modal").classList.remove("hidden");
  playCurrent();
}

function playCurrent() {
  const it = state.playlist[state.playIdx];
  if (!it) return;
  const v = $("#player");
  v.src = it.video;
  $("#video-title").textContent = `连续预览 ${state.playIdx + 1}/${state.playlist.length} · ${it.dir}(${it.class})`;
  v.play().catch(() => {});
}

function playlistStep(d) {
  const next = state.playIdx + d;
  if (next < 0 || next >= state.playlist.length) {
    closePlaylist();
    return;
  }
  state.playIdx = next;
  playCurrent();
}

function closePlaylist() {
  const v = $("#player");
  v.pause();
  v.removeAttribute("src");
  v.load();
  $("#video-modal").classList.add("hidden");
}

/* ---------------- 轮询:探针数据变化 → 刷新横幅 ---------------- */
function startPolling() {
  clearInterval(state.pollTimer);
  state.pollTimer = setInterval(async () => {
    try {
      const res = await api("/api/slides");
      const s = res.scenes?.find((x) => x.dir === state.sceneDir);
      if (s && s.elements_mtime && s.elements_mtime !== state.lastMtime) {
        $("#reload-banner").classList.remove("hidden");
      }
    } catch {
      /* 服务器暂时不可达,忽略 */
    }
  }, 2000);
}

$("#reload-btn").addEventListener("click", () => {
  $("#reload-banner").classList.add("hidden");
  selectScene(state.sceneDir);
  loadReworkState();
});

// 初始主题:白天(浅色)为默认,用户切换后记住选择
applyTheme(localStorage.getItem("mts-theme") || "light");

init();
