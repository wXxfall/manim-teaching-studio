---
description: 启动浏览器画面预览编辑器,并应用用户提交的"回炉重造"修改(仿 ppt-master live-preview)
---

# Live Preview Workflow(画面预览与回炉)

> **目的**:(1) 预览服务未运行时启动浏览器画面编辑器;(2) Step 6 画面审查阶段应用用户提交的 `request.json` 修改。
> **复刻自** ppt-master 的 `skills/ppt-master/workflows/live-preview.md`,把「SVG 注解」换成「Manim 元素注解」。

## 何时运行

- **启动预览(Step 1)** — 用户想"看看画面/预览/打开预览",或画面审查阶段要把交互式预览呈给用户。典型场景:低清渲染+探针完成后,或用户想手动点选元素提修改。
- **应用修改(Step 2)** — 用户提交了浏览器修改并给出信号。触发语:"应用修改" / "apply my annotations" / "应用注解" / 引用浏览器提示语(`✅ 已落盘 … — 回到对话说「应用修改」`)等等价表达。

## 何时不运行

- 预览服务已在运行 → 直接给出 URL,不要重复启动。
- 用户直接在对话里给了精确修改(如"scene02 的标题右移一点")→ 按主流水线直接改码,不必走浏览器。
- 探针数据不存在(`docs/review/preview/index.json` 缺失)→ 先跑探针再开预览。

---

## Step 1:启动 / 重开编辑器

**前置**:该项目探针数据已生成(否则先跑:

```bash
python ${SKILL_DIR}/scripts/scene_probe.py probe <project_path> --quality low
```

启动服务:

```bash
python ${SKILL_DIR}/preview/server.py <project_path> [--port 5051] [--no-browser]
```

服务器绑定 `127.0.0.1:5051`(默认,避开 ppt-master 的 5050),自动打开浏览器。打印 `Manim 画面预览运行中 → http://127.0.0.1:5051` 后,用一句话告诉用户:

- 预览地址 `http://127.0.0.1:5051`
- 点选画布元素 → 右侧控件调 位置/颜色/深浅/大小/时长/字号/层级 → 底部文本框写其他要求 → 点「提交修改(落盘)」→ 回到对话说「应用修改」
- 跳过浏览器直接口述修改也可以

端口冲突 → `--port <other>` 并报告新 URL。单实例锁:`<project>/.live_preview.lock`(记录 pid+端口,二次启动会提示已在运行)。

## Step 2:应用提交的修改

🚧 **GATE**:`<project>/docs/review/rework/request.json` 存在且 `items` 非空(队列格式:`{pending, items:[{scene, node, ops, free_text, targets, created}]}`,每个场景一条,同场景重复提交 = 覆盖该场景条目)。没有则告知用户无待应用修改。

触发:用户发出上述信号。

1. 读 request.json:

   ```bash
   python -c "import json;print(json.dumps(json.load(open('<project>/docs/review/rework/request.json',encoding='utf-8')),ensure_ascii=False,indent=2))"
   ```

   内容 = 提交队列(可能跨多个场景)。**按场景逐条应用**:每条 = 目标场景 + 节点 + 结构化操作列表(`ops`:element/op/参数/note)+ 自由文本(`free_text`)+ 目标(`targets` = 元素 id 列表,或 `["scene"]` 表示场景级要求)。**ops 直接当待办清单用,free_text 由主代理理解后改写代码,targets 指示自由文本针对哪些元素**。

2. **主代理亲自改码**(SKILL.md 纪律 #6/#9:禁止子代理/脚本改场景代码):
   - `shift(dx,dy)` → 在元素构造行追加/调整 `.shift(RIGHT*dx + UP*dy)`(注意 next_to/to_edge 相对定位会自动跟随,改完必须重渲染核对);
   - `set_color` → 改 `color=` 参数或追加 `.set_color()`(颜色值必须仍出自 spec_lock `## colors`,否则 lint 拦);
   - `set_opacity` → 追加 `.set_opacity(value)`;
   - `scale` → 追加 `.scale(value)`;
   - `set_run_time` → 改该元素**入场 play** 的 `run_time=`(与 shot_table 预算核对,总时长别超 target);
   - `set_font_size`(仅 Text)→ 改 `font_size=`;
   - `set_z_index` → 追加 `.set_z_index(value)`。
   - `free_text` → 主代理按执行者角色理解要求、外科式修改对应 Phase 的代码(遵守 manim-style-guide 全部避坑项)。

3. 验证与回显:

   ```bash
   python ${SKILL_DIR}/scripts/manim_lint.py lint <project_path> --spec <project_path>/spec_lock.md   # 0 error
   bash ${SKILL_DIR}/scripts/render_all.sh <project_path> --quality low --only <scene_dir>            # 或 MANIM_LOW_RES=1 manim -ql
   python ${SKILL_DIR}/scripts/scene_probe.py probe <project_path> --scene <scene_dir> --quality low # 重探针(合并进 index.json)
   ```

4. 告诉用户:修改已应用、探针已更新,浏览器右上角会弹「探针数据已更新」横幅,点「重新加载」看新画面;预览服务仍在运行。
5. 循环:用户继续提交 → 重复 1-4;用户说"好了/确认"或直接确认画面 → 清空 request(前端「清空」按钮或删文件),回到主流水线 Step 6 后续。

---

## 备注(编辑器不变量,SKILL.md Step 6 引用)

- **UI**:中文界面。左侧场景列表+节点缩略图(黄点=该节点新出现的元素);中间画布(缩放 50%/100%/150%,线条类元素覆盖层自动加高便于点击);右侧选中元素面板(位置步长 0.1/0.25/0.5、六色板+自定义取色、透明度滑杆、大小/时长/字号/层级按钮、代码行号引用);底部回炉栏(操作 chips 可删 + 自由文本 + 提交/清空)。
- **选中**:点击选中、Ctrl/Cmd+点击多选、Esc 取消、点空白取消;控件操作作用于全部选中元素。
- **提交**:POST `/api/rework` 落盘 `docs/review/rework/request.json`(只写文件,不调 AI);「清空」同时清本地与磁盘。
- **刷新**:前端每 2 秒轮询 `/api/slides`,`elements.json` mtime 变化即弹横幅。
- **停止条件**:浏览器「退出预览」、空闲超时(默认 7200s,`--timeout 0` 禁用)、或外部杀进程。锁文件只在进程退出时删除。
- **端口**:默认 5051,`--port` 覆盖。
