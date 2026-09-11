# 执行契约(Spec Lock)

> **⚠️ 骨架供策略师填写,勿逐字复制进项目。** 产出 `<project_path>/spec_lock.md` 时,只保留 `##` 节与填好的 `- ` 数据行,**不得携带任何 `>` blockquote 指导注释**——那些是作者期指导,不是运行时数据。产物中每一行都必须是可解析数据。
>
> 本文件是机器可读执行契约,执行者**每个场景写代码前必须 read_file 本文件**:颜色/字体/公式/参数一律来自这里,不得凭记忆或自造。设计叙事(为什么)见 `design_spec.md`。
>
> 开始写场景代码后,本文件是颜色/字体/公式的唯一权威来源。修改应同步两处:改本文件 + 让执行者按新值修正已写场景。

## project
- slug: quantum_tunneling
- target_duration: 180
- resolution: 1920x1080
- fps: 60
- audience: undergrad

> 填 slug、目标时长(秒)、分辨率、帧率、受众。target_duration 是时长校验(Step 8)的基准。

## colors
- bg: #282c34
- col_a: #58b9ff
- col_b: #8be9fd
- accent: #ffd866
- err: #ff6188
- green_a: #a6e22e
- white_: #ffffff
- opacity_subtitle: 0.55
- opacity_faded: 0.35

> 只填实际使用的颜色,名称对应 scene_template.py 中的常量名(white_ 即 WHITE_)。执行者不得使用本表之外的任何 HEX。opacity_* 是透明度层级约定。

## typography
- font: "Segoe UI"
- cjk_font: "Microsoft YaHei"
- tex_template: default
- title_size: 42
- body_size: 24
- label_size: 20
- annotation_size: 16

> font/cjk_font 必须与 design_spec §IV 一致。字号为基准锚点,执行者可在 ±20% 内微调。

## scenes
- scene01: dir=scene01_intro, class=IntroScene, type=anchor, duration_budget=22, run_time_max=3
- scene02: dir=scene02_barrier, class=BarrierScene, type=derivation, duration_budget=28, run_time_max=3

> 每场景一行。dir=场景目录名(在 <project>/scenes/ 下),class=场景类名,duration_budget=秒数预算(来自 shot_table),run_time_max=单个 self.play 的 run_time 上限(秒)。render_all.sh 与 make_video.py 解析本节的 dir/class。

## scene_rhythm
- scene01: anchor
- scene02: derivation
- scene03: demo
- scene04: demo
- scene05: anchor

> 每场景一个节奏标签,词汇固定为 anchor / definition / derivation / demo 四个值:
> - `anchor` — 结构场景(开场/过渡/结尾):居中大标题,无密集信息。
> - `definition` — 定义式:一个概念或公式居中呈现,视觉留白大。
> - `derivation` — 推导式:公式面板+推导步骤,允许信息密集(多列、面板)。
> - `demo` — 演示式:图形/动画为主,公式为辅,画面活跃。
> 执行者按标签选择布局密度,打破"每个场景长一样"。缺失节 → 全部按 definition 处理(不推荐,新项目必填)。

## scene_layouts
- scene01: "居中标题+副标题,渐入,无面板"
- scene02: "左侧坐标系+势垒,右侧公式面板;阶段1 居中演示 → 阶段2 缩小左移 → 阶段3 右侧面板"

> 每场景一句布局描述,写清阶段(phase)演进。画面审查的"逐帧附加要求"由本节派生:每个 phase 一帧,检查该阶段预期元素是否到位。

## math_locked
- 薛定谔方程: r"i\hbar\frac{\partial}{\partial t}\Psi = \hat{H}\Psi"
- 透射系数: r"T = \frac{4k\kappa}{(k+\kappa)^2}"
- 着色约定: 多子串 MathTex(part1, part2, ...)后 expr[i].set_color(...)
- 排版约定: \frac 不拆散;rf"..." 注入变量;长推导中间步 set_opacity(0.35)

> **允许出现的公式逐条列出,执行者不得自造变体或新增未列公式。** 新公式必须先经科学审查再补进本节。着色/排版约定全项目统一。

## physics
- sim_method: split-step Fourier
- key_params: E/V0 ≈ 0.73(三现象并存)
- conservation_check: 概率归一化自检
- honesty: 透射振幅最小可见下限 0.05,数值显示真实 T
- boundary: 波函数势垒边界 C⁰ 连续

> 模拟验证方法与参数。无含时过程的纯几何示意项目可省略本节。honesty 行强制:放大显示必须诚实,数值必须真实。

## forbidden
- physics_forbidden: 禁止"借能量还能量"式误导表述;禁止暗示守恒律瞬时破坏
- visual_forbidden: 禁止硬编码新 HEX;禁止 3D 陡峭 Surface(Cairo 针状伪影)

> 物理表述禁区与视觉禁区。科学审查(Step 4)按 physics_forbidden 逐条核查;执行者写码时遵守 visual_forbidden。

## delivery
- render_quality: low_then_high
- visual_review: 按 phase 边界抽帧,每场景 2~4 帧
- subtitle_density: 3.5~5s/句
- merged: true
- backup: true

> 交付配置:渲染档位、画面审查抽帧策略、字幕密度、是否合并成片、是否源码备份。
