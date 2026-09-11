# 工程解析:manim-teaching-studio 的构造与技术流程

> 本文档面向想**理解、修改或扩展**本项目的读者(AI 会话与人类开发者均可)。
> 使用层面的说明见 [README.md](README.md),制作流程的权威定义见 [skills/manim-teaching-studio/SKILL.md](skills/manim-teaching-studio/SKILL.md)。

## 1. 一句话定位

把「一个物理主题」变成「一条 ≤3 分钟、科学正确、画面干净的 1080p60 Manim 教学视频」的 **Claude Code skill**。它复刻了 ppt-master 的工程方法论(串行流水线、BLOCKING 确认点、质量门、机器可读契约),但产出物是 Manim 代码与渲染视频,并额外承担**物理正确性**责任。

## 2. 设计目标(按优先级)

1. **科学正确**:物理内容经过「模拟大学物理教授」的审查,错误表述(如"借能量还能量"式隧穿科普)被明文禁止。
2. **画面干净**:渲染帧经外部视觉模型逐帧审查,布局重叠、文字过小、元素裁剪等低级问题在低清阶段就被拦截。
3. **用户掌控节奏**:三个 ⛔ 硬停点,重大决策(视频规格、教学脚本、画面效果)必须用户显式确认,AI 不得替用户决定。
4. **token 经济**:大模型上下文是昂贵资源,整个工程按「渐进式披露 + 脚本代读」设计,详见 §8。
5. **可续跑**:Phase A(确认+脚本+科学审查)与 Phase B(写码+渲染+交付)可在不同会话中分段完成,状态全部落在磁盘上。

## 3. 目录树全解析

```
manim-teaching-studio/                    # 仓库根(不单独 git init,随外层仓库管理)
├── CLAUDE.md                             # Claude Code 入口:强制先读 SKILL.md;API key 安全红线
├── README.md                             # 安装、环境依赖、API Key 配置(面向用户)
├── ARCHITECTURE.md                       # 本文档:构造与技术流程解析
├── .gitignore                            # 排除 .env / __pycache__ / media / *.mp4 / render_log / backup 等
├── .env.example                          # ARK_API_KEY / ARK_MODEL 占位模板
├── .env                                  # 本机私有:视觉 API key(不入 git,按查找链读取)
├── projects/                             # 用户工作区,每个视频一个 <slug>_<YYYYMMDD>/ 目录
└── skills/manim-teaching-studio/         # skill 本体(通过 junction/软链挂到用户级 skills 目录)
    ├── SKILL.md                          # ★ 权威流水线:9 条全局纪律 + 9 步流程 + 两个索引表
    ├── workflows/                        # 独立工作流(不属主流水线,按触发条件单跑)
    │   ├── topic-research.md             # 只给主题名时:范围确认 → 联网搜集教材 → sources/research.md
    │   ├── resume-execute.md             # 分屏续跑:新会话从磁盘恢复状态,直接进 Step 5
    │   └── live-preview.md               # 画面预览与回炉:启动浏览器编辑器 / 应用 request.json(仿 ppt-master)
    ├── references/                       # 角色规范(渐进式披露,按需加载,默认不全读)
    │   ├── strategist.md                 # 策略师:九项确认单(打包式+推荐值)、双文件与脚本撰写规范
    │   ├── science-reviewer.md           # 科学审查员:五维度 rubric、P0/P1/P2 优先级、3 轮循环上限
    │   ├── executor.md                   # 执行者:逐场景手写纪律、元素 set_name 命名、先数值模拟后动画
    │   ├── visual-reviewer.md            # 画面审查员:机器预筛 + 交互式预览双轨、A/B/C 分级、单场景 2 轮修复上限
    │   └── manim-style-guide.md          # Manim 实战规范(吸收 manim_readme.md 全文:配色/避坑/物理验证)
    ├── templates/                        # 产物骨架(策略师/执行者照此填写)
    │   ├── design_spec_reference.md      # 设计书骨架(十一节,人类可读)
    │   ├── spec_lock_reference.md        # 执行契约骨架(十节,机器可读;blockquote 是作者期注释,不得进产物)
    │   ├── scene_template.py             # 场景代码骨架(env-gate config + 配色常量 + 标题模式 + set_name 示范)
    │   ├── shot_table.md                 # 分镜时长预算表模板
    │   └── science_review_template.md    # 科学审查报告模板
    ├── preview/                          # 交互式画面预览(浏览器编辑器,仿 ppt-master svg_editor)
    │   ├── server.py                     # Flask 本地服务器 127.0.0.1:5051(单实例锁+空闲超时+注解落盘)
    │   └── static/{index.html, app.js, style.css}  # 画布点选 + 右侧控件 + 底部回炉重造框
    └── scripts/                          # 工具脚本(全部 Python 标准库,仅 render_all.sh 用 bash)
        ├── project_manager.py            # init <slug> / validate <path> / status <path>
        ├── manim_lint.py                 # 场景代码静态规范检查(6 项,0 error 才过关)
        ├── extract_frames.py             # 按比例或 phase 时间点抽帧;时长解析(不依赖 ffprobe)
        ├── vision_check.py               # 豆包视觉 API 逐帧审查(七条固定清单 + 附加要求)
        ├── scene_probe.py                # ★ 元素级探针:AST 时间线 → 入场后 1s 节点 → 相机无损 PNG + 元素 bbox + 代码映射
        ├── render_all.sh                 # 批量渲染 low/high,日志 + rc + 实测时长汇总
        └── make_video.py                 # 编号复制 + ffmpeg 拼接成片 + 源码备份
```

**每个视频项目的内部结构**(由 `project_manager.py init` 生成):

```
projects/<slug>_<YYYYMMDD>/
├── design_spec.md        # 人类可读设计书(策略师 Step 2 产出)
├── spec_lock.md          # 机器可读执行契约(执行者每场景写前必读)
├── sources/              # 外部素材(PDF/图片/论文)
├── scenes/sceneXX_xxx/main.py   # 每场景独立目录 + 独立 main.py(Manim 惯例)
├── prototypes/           # 数值验证(分步傅里叶、守恒自检等,先于动画代码)
├── docs/scripts/         # narration.md(分节脚本+秒数)+ shot_table.md(分镜预算)
├── docs/review/          # science_review.md + visual_review.md + duration_report.md + frames/
├── render_log/           # 渲染日志 + durations.tsv(每场景 rc 与实测时长)
├── output/               # <NN>_<dir>.mp4 分场景 + <slug>_final.mp4 合并片
├── backup/<timestamp>/   # 交付时源码自动存档
└── media/                # Manim 渲染中间产物(缓存)
```

## 4. 技术流程总览(9 步串行流水线)

```
 [0] topic-research ──(只给主题名时才走)──→ sources/research.md
        │
 [1] 项目初始化 ── project_manager.py init ──→ 骨架目录
 [2] 策略师 ── 读 strategist.md ──→ ⛔#1 九项确认单 → design_spec.md + spec_lock.md
 [3] 教学脚本 ──→ docs/scripts/narration.md + shot_table.md(秒数预算)
 [4] 科学审查 ── 读 science-reviewer.md ──→ science_review.md ── ⛔#2 打包呈用户
 [5] 场景代码 ── 读 executor.md,每场景前重读 spec_lock.md,逐场景手写 main.py
                 └─ 每场景立即:manim_lint 0 error + 低清预览
 [6] 低清渲染+画面审查 ── render_all.sh low → scene_probe(元素探针) + vision_check(机器预筛)
                 └─→ preview/server.py 交互式预览(点元素修改/回炉) → visual_review.md ── ⛔#3 打包呈用户(A 级清零才放行)
 [7] 高清渲染 ── render_all.sh high ──→ 1080p60 + durations.tsv
 [8] 时长校验 ── duration_report.md(实测 vs 预算,>110% 触发压缩)
 [9] 拼接交付 ── make_video.py ──→ output/*.mp4 + backup/ 存档
```

**三个 ⛔ BLOCKING 硬停**是本流水线的心脏:

| # | 位置 | 呈给用户的内容 | 放行条件 |
|---|---|---|---|
| 1 | Step 2 | 九项确认单(主题/时长/分辨率/配色/字体/语言/公式深度/类比深度/交付方式,带推荐值一次打包) | 用户显式确认或修改 |
| 2 | Step 4 | 教学脚本关键节选 + 科学审查报告汇总 | 用户显式确认 |
| 3 | Step 6 | 画面审查汇总表 + 抽帧图 + Needs-Manual 条目 | A 级清零且用户确认 |

设计意图:视频规格、教学内容、画面效果是**用户品味与责任**所在,AI 的正确做法是给出专业推荐值然后停下等确认——而非"边做边问"或"做完才报"。

## 5. 核心机制详解

### 5.1 双文件机制(design_spec + spec_lock)

| | design_spec.md | spec_lock.md |
|---|---|---|
| 读者 | 人 | 机器(执行阶段的 AI 会话) |
| 形式 | 十一节散文式设计书 | 十节结构化条目 |
| 内容 | 为什么:教学定位、风格动机、类比取舍 | 是什么:颜色 HEX 值、字体名、每场景类型与秒数、逐条锁定公式、物理禁区 |
| 生命周期 | 策略师阶段写,之后归档 | 执行者**每场景写代码前必读**(纪律 #8) |

分离动机:上下文压缩会让模型"凭记忆"写代码。spec_lock 是一份小体积、全事实、零修辞的契约——每场景重读它,颜色/字体/公式/参数就不会漂移。lint 脚本用它的 `## colors` 节做硬编码颜色白名单比对,是真正的"机器可读"。

### 5.2 科学审查(模拟大学物理教授)

- **五维度 rubric**:物理准确性 / 教学逻辑 / 数学严谨性 / 类比边界 / 表达与时长。
- **优先级**:P0 = 物理错误(阻塞,必须修);P1 = 表述不精确(默认修订,可用户豁免);P2 = 优化建议(可记录不修)。
- **循环**:修订→复审,最多 3 轮;终止条件 = 无 P0 且 P1 已处理或豁免;3 轮后仍有 P0 硬停与用户讨论。
- **审查对象是脚本而不是代码**:物理错误在文字阶段拦截,比在代码里发现便宜一个数量级。

### 5.3 画面审查链路(机器预筛 + 交互式预览双轨)

```
render_all.sh --quality low   →  480×854@15 低清 mp4(渲染快)
        │
        ├─ 机器预筛:extract_frames.py 按 phase 边界抽帧 → vision_check.py 豆包七条清单逐帧审查
        │
        └─ 交互式预览:scene_probe.py probe → docs/review/preview/(节点无损 PNG + elements.json)
              → preview/server.py(127.0.0.1:5051 浏览器画布:点选元素 → 右侧控件 → 回炉重造框)
              → 用户提交 → docs/review/rework/request.json
              → 用户说「应用修改」→ 主代理改码(纪律 #6/#9)→ lint → 重渲染+重探针 → 浏览器自动刷新
        ↓
visual-reviewer 汇总          →  visual_review.md:A(必须修)/ B(建议修)/ C(记录)
        ↓
A 级修复循环(单场景最多 2 轮,超限 → Needs-Manual 交用户)→ ⛔#3
```

为什么用外部 API 而不是让主模型看图:① 审查消耗的是豆包 token,不是 Claude 上下文;② 审查结果收敛为七条短结论,主代理只读汇总表;③ 用户自己也能看图核对。为什么再加浏览器预览:机器只能报"有问题",交互式预览让用户**直接点问题元素、调参数、写要求**——改哪里、怎么改的品味决策回到用户手里,AI 只执行。

### 5.4 env-gate 低清渲染

Manim 的 `-pql` 等 CLI 档位会被**模块内的 `config.pixel_width/height` 赋值覆盖**(已知坑)。因此模板用环境变量切换:

```python
LOW_RES = os.environ.get("MANIM_LOW_RES", "0") == "1"
config.pixel_height = 480 if LOW_RES else 1080
config.pixel_width  = 854 if LOW_RES else 1920
config.frame_rate  = 15 if LOW_RES else 60
```

`render_all.sh` 低清档 `export MANIM_LOW_RES=1`,高清档 `unset`。一套代码两种档位,画面审查用低清(快),成片用高清。

### 5.5 时长控制链路(目标 ≤3 分钟的核心保障)

```
确认单 b 项 target_duration(默认 180s)
  → spec_lock ## scenes 每场景 duration_budget
  → shot_table 分节秒数预算(硬约束:预算之和 ≤ 目标;句数×5s ≥ 场景预算)
  → 场景代码全部显式 run_time(禁止默认值)
  → render_all.sh 用 ffmpeg 实测每场景时长 → render_log/durations.tsv
  → Step 8 duration_report 对照表
  → 超 110% 触发压缩:减 wait → 加速慢动画 → 与用户协商删节(删物理内容必须用户确认)
```

### 5.6 API key 查找链(vision_check.py)

```
环境变量 ARK_API_KEY → 脚本 cwd/.env → 仓库根 .env → 用户主目录/.manim-teaching-studio/.env
```

脚本**从不硬编码 key**;key 只存在于 `.env`(git 排除)。换视觉模型只需改 `ARK_MODEL`(OpenAI 兼容端点,当前默认 doubao-seed-2-0-mini-260428)。

### 5.7 交互式画面预览(元素探针 scene_probe.py)

仿 ppt-master 的「浏览器注解层 + 文件即模型 + 主 agent 消费注解改写代码 + mtime 驱动刷新」闭环,数据模型换成 Manim 场景代码:

1. **AST 静态分析**(不执行代码):解析 `construct()`,累计 `self.play(run_time=)` / `self.wait()` / `self.add()` 得到精确时间线;识别 mobject 变量(变量名 → 定义行号)、`# ==== Phase N ====` 分段、入场事件(变量第一次被动画引用)。支持辅助函数内联(返回值变量重命名为调用处目标)、常量 for 循环展开(`enumerate`/`range`/字面量,循环局部变量加 `#itN` 后缀)。
2. **节点计算**:每个入场事件结束后 **+1.0s**(透明度拉满、画面稳定;用户确认的规则);1 秒后若撞上下一个事件,取间隙中点;相距 ≤0.5s 合并;场景末帧必为节点。
3. **探针渲染**(替代视频抽帧):加载场景类,接管 `scene.play/wait`——节点之前的动画快进(`begin → interpolate(1) → finish → clean_up_from_scene`,完整复刻 renderer 语义),包含节点时刻的动画用 `scene.update_to_time(t)` 按帧率步进,然后 `camera.reset() + capture_mobjects()` 全量重绘、`get_image()` 输出无损 PNG。同帧用 `camera.points_to_pixel_coords` 计算每个可见元素的像素 bbox(剔除所有点重合的退化成员,如未开始绘制的箭头尖)。产出 `docs/review/preview/<scene>/{node_NN.png, elements.json}`。
4. **浏览器闭环**:`preview/server.py`(Flask,127.0.0.1:5051)服务这些数据;前端画布把 PNG 当背景、按 bbox 铺可点击覆盖层;右侧控件(shift/颜色/透明度/scale/run_time/font_size/z_index)与底部自由文本生成结构化操作,POST 落盘 `docs/review/rework/request.json`。**服务器不调用 AI**——用户回对话说「应用修改」,主代理读 request.json 改码(纪律 #6/#9),重渲染重探针后前端轮询到 mtime 变化弹刷新横幅。
5. **确定性边界**:探针是"读代码 + 渲染取帧"的确定性工具,绝不生成/修改场景代码;时间线静态分析与运行时逐事件对齐,失配立即警告(如不可展开的动态循环)。

## 6. 脚本工具速览

| 脚本 | 输入 | 输出 | 关键实现点 |
|---|---|---|---|
| project_manager.py | slug 或项目路径 | 骨架 / 校验结论 / 状态表 | 纯标准库;REPO_ROOT 由 `parents[3]` 定位 |
| manim_lint.py | 项目路径 + spec_lock | 6 项检查清单(rc!=0 即拦) | 正则 + 括号配对,不执行代码;硬编码 HEX 与 spec_lock 白名单比对 |
| extract_frames.py | mp4 + 时间点 | jpg 帧 | 时长解析走 `ffmpeg -i` stderr(不依赖 ffprobe) |
| vision_check.py | 图片 + 附加要求 | 中文七条报告 | 2 次尝试间隔 3s;temperature 0.1 求稳定 |
| scene_probe.py | 项目路径 / 场景 main.py | 节点无损 PNG + elements.json + index.json | AST 时间线(辅助函数内联+常量循环展开);接管 play/wait 快进/步进;相机取帧 + 像素 bbox;`--scene` 时合并更新 index.json |
| preview/server.py | 项目路径 | 浏览器编辑器 + request.json | Flask;单实例锁 `.live_preview.lock`;空闲超时;只写注解不调 AI |
| render_all.sh | 项目路径 + low/high | mp4 + 日志 + durations.tsv | 从 spec_lock `## scenes` 解析 dir/class;失败不中断,rc 进 tsv |
| make_video.py | 项目路径 | 编号分场景 + 合并片 + 备份 | 按 spec_lock 顺序复制;concat 用 `-c copy` 无损 |

**数据流依赖**:project_manager 建目录 → 策略师填双文件 → render_all / make_video / lint 都**只认 spec_lock 里的 dir/class 声明**——spec_lock 是全流水线的单一事实源(single source of truth)。

## 7. 全局执行纪律(为什么需要它们)

SKILL.md 顶部 9 条纪律是 ppt-master 方法论的核心移植,每一条都对应一个真实失败模式:

| 纪律 | 防御的失败模式 |
|---|---|
| 严格串行 | 后续步骤基于未确认的假设开工,返工 |
| ⛔ 硬停 | AI 替用户做品味决策,用户失去掌控 |
| 禁止跨阶段打包 | "顺手"把代码写了,科学审查形同虚设 |
| GATE 前置条件 | 缺失输入就开工,产出废品 |
| 禁止投机执行 | 预准备的产物与确认后的需求不一致 |
| 禁止子代理生成场景代码 | 子代理没有 spec_lock 与全流程上下文,写出的代码漂移 |
| 逐场景连续生成 | 批量分组丢失场景间的教学节奏连贯性 |
| 每场景重读 spec_lock | 上下文压缩导致颜色/字体/公式凭记忆 |
| 禁脚本批量生成代码 | 脚本是确定性检查器,不该是内容生成器 |

## 8. Token 优化设计(贯穿全工程)

1. **渐进式披露**:SKILL.md 只有流程与索引表;规范全部下沉 `references/`,按步骤索引"何时读哪个"。写代码时只读 style-guide 相关章节,不全量加载。
2. **每场景唯一必读 = spec_lock.md**(小文件);design_spec 仅策略师阶段读。
3. **画面审查零主上下文消耗**:图片给豆包看(外部算力),主代理只读七条短结论汇总;用户看图。
4. **脚本代读**:lint 静态检查代替人工逐文件核查;render_all 批量渲染,主代理只读 rc 汇总与 durations.tsv。
5. **分屏续跑**:Phase A/B 跨会话分离,新会话从磁盘恢复,不重放历史上下文。
6. **报告格式统一"汇总表在前、细节按需展开"**:BLOCKING 呈现时只贴汇总+关键条目。

## 9. 外部依赖清单

| 依赖 | 用途 | 获取 |
|---|---|---|
| Manim CE(≥0.18,本工程基于 0.19.1 实战) | 渲染引擎 | pip |
| LaTeX | MathTex 公式渲染 | TeX 发行版 |
| ffmpeg | 抽帧 / 拼接 / 时长解析 | PATH 或 FFMPEG_DIR 环境变量 |
| Python 3.10+ | 全部工具脚本 | 系统安装 |
| Flask(≥3.0) | 交互式画面预览服务器(preview/server.py) | pip install flask |
| 火山方舟视觉 API(豆包) | 画面机器预筛 | README「API Key 配置」 |
| Claude Code + 用户级 skills 目录 | 运行载体 | junction/软链安装 |

## 10. 扩展指南(常见改法)

- **加 lint 检查项**:改 `manim_lint.py` 的 `lint_file()`,并在 docstring 与 SKILL.md 脚本索引同步说明。
- **换视觉模型/API**:改 `vision_check.py` 的 `API_URL`/`DEFAULT_MODEL`(OpenAI 兼容格式即可);`.env` 里改 `ARK_MODEL`。
- **改模板**:`templates/` 是骨架;注意 spec_lock 模板中的 blockquote 是作者期指导注释,产物中不得携带。
- **改确认单**:`references/strategist.md` 的九项定义 + SKILL.md Step 2 的 ⛔ 描述同步改。
- **改渲染档位**:`scene_template.py` 的 env-gate 三行 + `render_all.sh` 的 `-ql/-qh` 与输出目录名同步改。
- **加独立工作流**:`workflows/` 下新建 md,在 SKILL.md 的「独立工作流」表登记触发条件。
- **调探针节点规则**:`scene_probe.py` 顶部常量 `NODE_GAP_AFTER`(入场后等几秒)/ `NODE_MERGE_EPS`(合并阈值);元素命名规则见 `executor.md` 纪律 9。
- **加预览控件**:前端 `preview/static/app.js` 的 `bindControls()`(生成结构化 op)+ `workflows/live-preview.md` Step 2(主代理如何把 op 翻译成代码改动)两处同步加。

## 11. 设计渊源

- **ppt-master**:流水线架构的直接来源(串行纪律、BLOCKING 确认、GATE、spec 双文件、八大确认单),本工程将其从 PPT 场景移植到视频场景。
- **manim cupec v2.0**:经验手册(配色规范、避坑清单、架构约定)全文吸收进 `references/manim-style-guide.md`。
- **manim cupec v2.5**:视觉查帧工具链(`vision_check.py` 模式)与多场景渲染经验。
- **manim cupec v3.0 / manim_project**:批量渲染与早期架构实践。