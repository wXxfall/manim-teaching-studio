---
name: manim-teaching-studio
description: >
  面向大学物理教学的 Manim 动画视频制作流水线。策略师九项确认产出设计书(design_spec.md)
  与机器可读执行契约(spec_lock.md),模拟大学物理教授做五维度科学审查,执行者逐场景手写
  Manim 代码,低清渲染后用火山方舟视觉 API 做画面审查,三个 ⛔ BLOCKING 确认点硬停等用户
  显式确认,高清渲染 1080p60 后 ffprobe 时长校验、ffmpeg 拼接成片。默认约 3 分钟(可调)、
  3b1b 深色配色、中文旁白、每场景独立目录。Use when 用户要求"制作物理教学视频/动画"、
  "物理概念可视化"、"Manim 教学动画"、"大学物理/量子力学/电磁学/光学等课程动画"、
  "3 分钟视频/科普短片",或想把某个物理概念、公式、实验做成讲解动画,即便用户没提
  "Manim" 或 "skill" 二字。边界:本 skill 负责制作流程、物理内容正确性与科学/画面双重
  质量门;3b1b 视觉语言与 Manim 技法细节(公式编排、配色美学、构图)由 manim-3b1b-style
  skill 承担,二者互补不重复。
---

# Manim 教学工作室(manim-teaching-studio)

> 面向大学生的物理教学 Manim 动画视频制作流水线:策略师(九项确认)→ 科学审查(模拟物理教授)→ 执行者(逐场景手写代码)→ 画面审查(视觉 API)→ 时长校验 → 拼接交付。

**核心流水线**:`素材(可选 topic-research)→ 项目初始化 → 策略师[⛔确认单] → 教学脚本 → 科学审查[⛔] → 场景代码生成 → 低清渲染+画面审查[⛔] → 高清渲染 → 时长校验 → 拼接交付`

> [!CAUTION]
> ## 🚨 全局执行纪律(最高优先级,违反任何一条即执行失败)
>
> 1. **严格串行** — 步骤必须按序执行,上一步产出是下一步输入;相邻非 BLOCKING 步骤在满足前置条件后可连续推进,不必等用户说"继续"。
> 2. **⛔ BLOCKING = 硬停** — 标记 ⛔ 的步骤必须完全停下,等待用户显式确认或修改,**不得替用户做任何决定**。
> 3. **禁止跨阶段打包** — 策略师阶段不得写场景代码;脚本未经科学审查不得写代码;低清画面未经确认不得高清渲染。
> 4. **🚧 GATE 前置条件** — 每步开头列出的前置条件必须先验证再开工。
> 5. **禁止投机执行** — 禁止"预准备"后续步骤的内容。
> 6. **禁止子代理生成场景代码** — Step 5 写代码依赖完整上下文,必须由当前主代理逐场景端到端完成,委托子代理或脚本批量生成一律禁止。
> 7. **逐场景连续生成** — 场景代码按编号连续逐个写,禁止"每批 N 个"式分组。
> 8. **每场景写前重读 spec_lock.md** — 颜色/字体/公式/参数一律来自该文件,不得凭记忆或自造(防上下文压缩漂移);同时按该场景的 scene_rhythm 标签选择布局密度。
> 9. **禁脚本批量生成场景代码** — 脚本只能做检查/渲染/抽帧等确定性工作(manim_lint.py 是检查器不是生成器)。

> [!IMPORTANT]
> ## 🌐 语言与兼容规则
>
> - **始终用中文回复用户**;画面文字/旁白默认中文(确认单 f 项可改)。
> - 写/改 Manim 代码前,先读本 skill 的 `references/manim-style-guide.md` 相关章节(已吸收全局约束要求的「Manim Cupe v2.0」manim_readme.md 全部内容)。
> - 本 skill 是视频制作工作流,不是通用应用脚手架:不建 tests/.worktrees/CI/分支流程。

## 脚本索引(${SKILL_DIR} 即本 skill 目录)

| 脚本 | 用途 | 步骤 |
|---|---|---|
| `scripts/project_manager.py init <slug>` | 创建 `projects/<slug>_<YYYYMMDD>/` 骨架 | 1 |
| `scripts/project_manager.py validate <path>` | 分屏续跑 sanity check | resume |
| `scripts/project_manager.py status <path>` | 产物状态表 | 任意 |
| `scripts/manim_lint.py lint <path> [--spec spec_lock.md]` | 场景代码静态规范检查(0 error 才过关) | 5 |
| `scripts/render_all.sh <path> --quality low\|high [--only sceneXX]` | 批量渲染+日志+rc+实测时长 | 6/7 |
| `scripts/extract_frames.py extract <mp4> --out <dir> [--times 0.25,0.5,0.85]` | 抽关键帧(机器预筛) | 6 |
| `scripts/vision_check.py check <帧图> ["附加要求"] [--out 报告]` | 豆包视觉 API 逐帧审查 | 6 |
| `scripts/scene_probe.py probe <path> [--scene X] [--quality low\|high]` | 元素级探针:入场后 1s 节点无损 PNG + 元素 bbox + 元素↔代码映射 → `docs/review/preview/` | 6 |
| `scripts/scene_probe.py file <任意 main.py> [--class X] [--out dir]` | 任意布局单文件探针(对任意 Manim 工程接入预览 UI,可多次叠加) | 任意 |
| `scripts/scene_probe.py analyze <main.py>` | 只做静态时间线+节点(调试) | 6 |
| `preview/server.py <path> [--port 5051]` | 浏览器画面预览编辑器(127.0.0.1:5051) | 6 |
| `scripts/make_video.py <path> [--merged]` | 编号复制+合并成片+源码备份 | 9 |

## 引用文件索引(按需读,不全文加载)

| 文件 | 何时读 |
|---|---|
| `references/strategist.md` | Step 2/3(九项确认单、双文件与脚本撰写规范) |
| `references/science-reviewer.md` | Step 4(五维度 rubric、P0/P1/P2) |
| `references/executor.md` | Step 5(写码纪律、数值验证要求) |
| `references/visual-reviewer.md` | Step 6(抽帧、审查、A/B/C 分级) |
| `references/manim-style-guide.md` | Step 5 写码时按需读对应章节(§1 架构/§2 模板/§3 避坑/§4 布局动画/§5 物理验证/§6 渲染/§7 清单) |
| `templates/spec_lock_reference.md` | 策略师填 spec_lock 时 |
| `templates/design_spec_reference.md` | 策略师填 design_spec 时 |
| `templates/shot_table.md` | 策略师填分镜预算表时 |
| `templates/science_review_template.md` | 科学审查员写报告时 |

## 独立工作流

| 工作流 | 触发 |
|---|---|
| `workflows/topic-research.md` | 用户只给主题名、无任何素材(Step 0,先搜集再回 Step 1) |
| `workflows/resume-execute.md` | 新会话"继续生成 projects/<x>"(Phase B 续跑,Step 5 起) |
| `workflows/live-preview.md` | 画面预览:启动浏览器编辑器 / 用户提交修改后说"应用修改"(Step 6,仿 ppt-master) |

---

## 主流水线

### Step 0(条件):topic-research

🚧 **GATE**:用户只给了主题名或一句话要求,没有文件/链接/实质描述。

按 `workflows/topic-research.md` 搜集教材/讲义/百科素材,产出 `sources/research.md`,完成后回 Step 1。

### Step 1:项目初始化

🚧 **GATE**:有主题+素材(对话中的实质描述亦可;或 Step 0 已完成)。

```bash
python ${SKILL_DIR}/scripts/project_manager.py init <slug>
```

有外部素材文件(PDF/图片等)时移入 `<project>/sources/` 并记录来源。

**✅ 检查点:骨架创建成功,scenes/scene01_intro/main.py 模板就位。**

### Step 2:策略师 — 九项确认单(⛔ BLOCKING #1)

🚧 **GATE**:Step 1 完成。

切换为策略师角色:读 `references/strategist.md`。

⛔ **BLOCKING**:把九项视频确认单(a 主题与教学定位 / b 目标时长默认 180s 可调 / c 分辨率帧率 / d 视觉风格配色 / e 字体 / f 语言字幕 / g 公式深度 / h 类比+数值模拟深度 / i 审查与交付方式)**一次性打包**呈现,每项带推荐值与理由,等用户显式确认或修改。禁止逐条询问;末尾附 💡 分屏提示行。

用户确认后(可连续推进):产出 `design_spec.md`(十一节,骨架见 templates)与 `spec_lock.md`(十节,机器可读,不得携带 blockquote 注释),落盘项目根。

**✅ 检查点:双文件落盘且与确认单最终值逐项一致。**

### Step 3:教学脚本 + 分镜预算表

🚧 **GATE**:双文件落盘。

产出 `docs/scripts/narration.md`(分节脚本,每节「## 标题 — 约 XX 秒」,先故事→再公式→最后澄清)与 `docs/scripts/shot_table.md`(逐场景起止秒/预算/run_time 上限/wait 预算/句数)。硬约束:预算之和 ≤ target_duration;句数×5s ≥ 场景预算;每个类比标注边界分析位置。

**✅ 检查点:每节带秒数预算,shot_table 合计 ≤ 目标时长。**

### Step 4:科学审查(⛔ BLOCKING #2)

🚧 **GATE**:脚本+预算表就绪。

切换为科学审查员角色:读 `references/science-reviewer.md`,以大学物理教授视角按五维度 rubric(物理准确性/教学逻辑/数学严谨性/类比边界/表达与时长)审查脚本,产出 `docs/review/science_review.md`(逐条附行号+优先级)。循环:修订→复审最多 3 轮;终止=无 P0 且 P1 已处理或豁免;3 轮后仍有 P0 硬停与用户讨论。

⛔ **BLOCKING**:把「教学脚本(关键节选)+ 审查报告(汇总表+关键条目)」打包呈用户,等显式确认或修改意见。确认后方可写代码。

**✅ 检查点:科学审查通过且用户确认。**

### Step 5:场景代码生成(执行者)

🚧 **GATE**:BLOCKING #2 通过。

切换为执行者角色:读 `references/executor.md`。**每个场景写前必读 `<project>/spec_lock.md`**(纪律 #8),逐场景连续手写 `scenes/<dir>/main.py`;spec_lock `## physics` 要求数值验证的场景先在 `prototypes/` 验证(分步傅里叶等,守恒自检);每场景写完立即:

```bash
python ${SKILL_DIR}/scripts/manim_lint.py lint <project_path> --spec <project_path>/spec_lock.md   # 0 error
cd <project_path>/scenes/<dir> && MANIM_LOW_RES=1 manim -pql main.py <Class>                      # 低清预览无重叠漂移
```

**✅ 检查点:全部场景 lint 0 error + 低清预览通过。**

### Step 6:低清批量渲染 + 画面审查(⛔ BLOCKING #3)

🚧 **GATE**:全部场景代码就绪。

读 `references/visual-reviewer.md`:

1. `bash ${SKILL_DIR}/scripts/render_all.sh <project_path> --quality low`
2. 元素级探针:`python ${SKILL_DIR}/scripts/scene_probe.py probe <project_path> --quality low` —— 对每个元素**入场动画结束后 1 秒**的节点,用 Manim 相机亲自渲染无损 PNG(非视频抽帧),并导出每个可见元素的屏幕 bbox 与「元素变量 ↔ 代码行号」映射到 `docs/review/preview/`
3. 机器预筛(保留):`scripts/extract_frames.py` 按 phase 边界抽帧 + `scripts/vision_check.py` 逐帧七条清单审查
4. **交互式预览(⛔#3 的用户界面)**:`python ${SKILL_DIR}/preview/server.py <project_path>` 启动 127.0.0.1:5051,用户在浏览器画布上点选元素、右侧边栏调 位置/颜色/深浅/大小/时长/字号/层级、底部"回炉重造"文本框写要求 → 提交落盘 `docs/review/rework/request.json`;用户回对话说"应用修改" → 按 `workflows/live-preview.md` 主代理改码 → lint → 重渲染该场景 → 重探针 → 浏览器自动刷新
5. 汇总 `docs/review/visual_review.md`(A 必须修 / B 建议修 / C 记录);A 级修复循环单场景最多 2 轮,超限 Needs-Manual。

⛔ **BLOCKING**:把「审查汇总表 + **画面预览地址 http://127.0.0.1:5051**(可点选元素直接改)+ 抽帧图路径 + Needs-Manual 条目」打包呈用户,等确认或修改意见。确认后进高清;有修改则按 `workflows/live-preview.md` 应用 → 重跑该场景低清+重探针 → 复审 → 再确认。

**✅ 检查点:A 级清零(或裁决)且用户确认画面。**

### Step 7:高清渲染

🚧 **GATE**:BLOCKING #3 通过。

```bash
bash ${SKILL_DIR}/scripts/render_all.sh <project_path> --quality high
```

**✅ 检查点:全部场景 rc=0,`render_log/durations.tsv` 有每场景实测时长。**

### Step 8:时长校验

🚧 **GATE**:高清产物就绪。

汇总 `docs/review/duration_report.md`:每场景实测 vs shot_table 预算对照表 + 总时长 vs target_duration。总时长 > 110% 时按优先级压缩:减 wait 留白 → 加速慢动画 → 与用户协商删节(**删任何物理内容必须用户确认**);>115% 必报用户讨论。合并片时长用 ffprobe 复核。

**✅ 检查点:总时长 ≤ 目标×110% 或已协商。**

### Step 9:拼接交付

🚧 **GATE**:时长校验完成。

```bash
python ${SKILL_DIR}/scripts/make_video.py <project_path> --merged
```

产出 `output/<NN>_<dir>.mp4`(分场景)+ `output/<slug>_final.mp4`(合并片)+ `backup/<timestamp>/`(源码存档)。交付报告:成品清单+总时长+审查结论摘要。

**✅ 检查点:成品可播放,总时长复核,源码已备份。**
