# 🎬 Manim Teaching Studio

> **`manim-teaching-studio`** · 面向大学生的物理教学 Manim 动画视频制作流水线

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Manim CE 0.19.1](https://img.shields.io/badge/ManimCE-0.19.1-525893?style=flat-square)](https://www.manim.community/)
[![1080p 60fps](https://img.shields.io/badge/输出-1080p60-FF6B6B?style=flat-square)](https://docs.manim.community/)
[![License MIT](https://img.shields.io/badge/License-MIT-00B4D8?style=flat-square)](LICENSE)
[![skills.sh](https://skills.sh/b/wXxfall/manim-teaching-studio)](https://skills.sh/wXxfall/manim-teaching-studio)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-插件市场-8B5CF6?style=flat-square)](https://code.claude.com/docs/en/discover-plugins)

把物理主题变成 **默认 3 分钟以内(可调)**、**科学正确**(模拟大学物理教授五维审查)、**画面干净**(视觉 API 机器预筛 + 浏览器交互式画面审查)的 1080p60 教学动画。

---

## 🎬 演示视频

<video src="https://raw.githubusercontent.com/wXxfall/manim-teaching-studio/main/docs/assets/demo.mp4" controls width="100%"></video>

> 若上方播放器没有出现(部分镜像站/客户端不渲染内嵌视频),请[**点此下载观看**(4.7 MB)](docs/assets/demo.mp4)。

视频内容:从「策略师确认单」到「浏览器点选元素改动画」的完整流程演示。

---

## 📖 目录

- [🏗️ 一、项目结构](#一项目结构)
- [📦 二、环境依赖与安装](#二环境依赖与安装)
- [🚀 三、操作步骤](#三操作步骤)
- [🧰 四、脚本工具速览](#四脚本工具速览)
- [💡 五、常见问题与注意事项](#五常见问题与注意事项)

---

**核心流水线**:

```
素材(可选 topic-research)
  → ① 项目初始化
  → ② 策略师九项确认单 ⛔#1
  → ③ 教学脚本 + 分镜预算表
  → ④ 科学审查 ⛔#2
  → ⑤ 场景代码生成(逐场景手写 + lint + 低清预览)
  → ⑥ 低清渲染 + 画面审查(元素探针 + 浏览器交互式预览)⛔#3
  → ⑦ 高清渲染
  → ⑧ 时长校验
  → ⑨ 拼接交付
```

三个 ⛔ 是**硬停确认点**,确认前绝不往下走:① 视频确认单(主题/时长/分辨率/配色/字体/公式深度等九项)② 教学脚本+科学审查报告 ③ 低清画面+画面审查(在浏览器里点选元素直接改)。

---

## 🏗️ 一、项目结构

### 1.1 仓库根目录

```
manim-teaching-studio/
├── CLAUDE.md                     # Claude Code 入口:强制先读 SKILL.md;API key 安全红线
├── README.md                     # 本文档
├── ARCHITECTURE.md               # 工程解析:数据流、核心机制、扩展指南(想改工程先读)
├── .gitignore                    # 排除 .env / 渲染产物 / 预览数据
├── .env.example / .env           # 视觉 API key(本机私有,不入 git)
├── preview_launcher.pyw          # ★ 一键启动器(双击即用,液态玻璃 GUI)
├── projects/                     # 用户工作区(每个视频一个目录)
│   ├── doppler_effect_20260815/  # 示例项目(多普勒效应,5 场景 180s)
│   └── raman_spectroscopy_20260813/  # 示例项目(拉曼光谱,已交付)
└── skills/manim-teaching-studio/ # skill 本体(可 junction 到用户级 skills 目录)
```

### 1.2 skill 本体(`skills/manim-teaching-studio/`)

```
skills/manim-teaching-studio/
├── SKILL.md                      # ★ 权威流水线:9 条全局纪律 + 9 步流程 + 脚本/引用索引
├── workflows/                    # 独立工作流(按触发条件单跑)
│   ├── topic-research.md         #   只给主题名时:联网搜集教材 → sources/research.md
│   ├── resume-execute.md         #   分屏续跑:新会话"继续生成 projects/<x>"
│   └── live-preview.md           #   画面预览与回炉:启动浏览器 / 应用 request.json
├── references/                   # 角色规范(渐进式披露,按需加载)
│   ├── strategist.md             #   策略师:九项确认单、双文件、脚本撰写规范
│   ├── science-reviewer.md       #   科学审查员:五维度 rubric、P0/P1/P2
│   ├── executor.md               #   执行者:逐场景手写纪律、元素 set_name 命名
│   ├── visual-reviewer.md        #   画面审查员:机器预筛 + 交互式预览双轨
│   └── manim-style-guide.md      #   Manim 实战规范(避坑清单/布局动画/物理验证)
├── templates/                    # 产物骨架(策略师/执行者照此填写)
│   ├── design_spec_reference.md  #   设计书(十一节)
│   ├── spec_lock_reference.md    #   执行契约(十节,机器可读)
│   ├── scene_template.py         #   场景代码骨架(env-gate + 配色 + set_name 示范)
│   ├── shot_table.md             #   分镜时长预算表
│   └── science_review_template.md#   科学审查报告
├── preview/                      # ★ 交互式画面预览(浏览器编辑器)
│   ├── server.py                 #   Flask 服务器(127.0.0.1:5051;提交队列/视频/静态)
│   └── static/                   #   index.html + app.js + style.css(浅色默认+黑夜切换)
└── scripts/                      # 工具脚本(确定性工作,不生成/修改场景代码)
    ├── project_manager.py        #   项目骨架 init/validate/status
    ├── manim_lint.py             #   场景代码静态规范检查(6 项,0 error 才过关)
    ├── scene_probe.py            #   ★ 元素级探针(见 §3.2)
    ├── extract_frames.py         #   按时间点从 mp4 抽帧
    ├── vision_check.py           #   豆包视觉 API 七条清单逐帧审查
    ├── render_all.sh             #   批量渲染 low/high + 时长实测
    └── make_video.py             #   编号复制 + ffmpeg 拼接 + 源码备份
```

### 1.3 单个视频项目(`projects/<slug>_<YYYYMMDD>/`)

```
projects/doppler_effect_20260815/
├── design_spec.md                # 人类可读设计书(为什么这样设计,十一节)
├── spec_lock.md                  # 机器可读执行契约(颜色/字体/公式/场景清单,单一事实源)
├── sources/research.md           # 素材调研(仅 topic-research 流程产出)
├── scenes/                       # 每场景独立目录 + 独立 main.py(Manim 惯例)
│   ├── scene01_intro/main.py
│   ├── scene02_waves/main.py
│   └── .../media/                #   Manim 渲染产物(低清 480p15 / 高清 1080p60 mp4)
├── prototypes/                   # 数值验证(含时物理过程先在这里验证)
├── docs/scripts/                 # narration.md(分节脚本)+ shot_table.md(分镜预算)
├── docs/review/                  # science_review.md / visual_review.md / duration_report.md
│   ├── frames/                   #   机器预筛帧图 + 逐帧报告
│   ├── preview/                  #   ★ 元素探针数据(节点 PNG + elements.json + index.json)
│   └── rework/request.json       #   ★ 待应用修改队列(浏览器"提交落盘"写入)
├── render_log/                   # 渲染日志 + durations.tsv(每场景实测时长)
├── output/                       # <NN>_<dir>.mp4 分场景 + <slug>_final.mp4 合并片
└── backup/<timestamp>/           # 交付时源码自动存档
```

### 1.4 关键数据格式

| 文件 | 内容 |
|---|---|
| `docs/review/preview/<scene>/elements.json` | 探针数据:时间线、节点(入场后 1s)、每节点元素 bbox/颜色/透明度/代码行号映射 |
| `docs/review/preview/<scene>/node_NN.png` | 节点无损静帧(Manim 相机亲自渲染,非视频抽帧) |
| `docs/review/preview/index.json` | 全场景索引(预览服务器场景列表) |
| `docs/review/rework/request.json` | **提交队列**:`{pending, items:[{scene, node, ops, free_text, targets, created}]}`,每场景一条,同场景重复提交=覆盖 |
| `render_log/durations.tsv` | 每场景渲染 rc 与实测时长(时长校验依据) |

---

## 📦 二、环境依赖与安装

| 依赖 | 必需 | 用途 | 获取 |
|---|---|:---:|---|
| Python 3.10+ | ✅ | 全部工具脚本 | python.org |
| Manim CE(0.19.1 实战) | ✅ | 渲染引擎 | `pip install manim` |
| LaTeX | 公式场景 | MathTex 公式渲染 | TeX 发行版 |
| ffmpeg | ✅ | 抽帧/拼接/时长解析 | PATH 或 `FFMPEG_DIR` 环境变量 |
| Flask | 预览功能 | 画面预览服务器 | `pip install flask` |
| PySide6 | 启动器 | 液态玻璃 GUI(缺失自动降级 tkinter) | `pip install PySide6` |
| 火山方舟视觉 API(豆包) | 推荐 | 画面机器预筛 | 见 §2.4 |

### 2.1 安装(三种方式,任选其一)

**① Claude Code 插件市场(推荐)**

```
/plugin marketplace add wXxfall/manim-teaching-studio
/plugin install manim-teaching-studio@manim-teaching-studio
```

**② 通用 Agent Skills(Claude Code / Cursor / Codex 等跨工具)**

```bash
npx skills add wXxfall/manim-teaching-studio      # 全局安装,自动识别 skills/ 目录
```

**③ 手动挂载(离线 / 想改源码)**

把 `skills/manim-teaching-studio` 目录链接到你的用户级 skills 目录,详见 §2.2。

### 2.2 手动挂载(Windows junction)

把 skill 链接到用户级 skills 目录,任意会话全局可用且不占 C 盘空间(`<仓库路径>`、`<用户名>` 换成你自己的):

```bash
cd /c/Users/<用户名>/.claude/skills
cmd //c 'mklink /J manim-teaching-studio "<仓库路径>\skills\manim-teaching-studio"'
```

- 验证:`ls "/c/Users/<用户名>/.claude/skills/manim-teaching-studio"` 能看到 SKILL.md。
- 卸载:`cmd //c rmdir manim-teaching-studio`(junction 用 rmdir,勿用 del)。
- macOS/Linux:`ln -s "<仓库路径>/skills/manim-teaching-studio" ~/.claude/skills/manim-teaching-studio`。
- 之后在任意会话中说"帮我做一个物理教学动画"即可触发。

### 2.3 一键安装 GUI 依赖(可选)

```bash
pip install flask PySide6
```

### 2.4 API Key 配置(画面机器预筛的视觉模型)

画面审查使用**火山方舟(豆包)视觉 API**检查渲染帧。

1. 打开火山引擎方舟控制台 <https://console.volcengine.com/ark> → 开通豆包大模型服务 → 「API Key 管理」创建密钥(格式 `ark-xxxx-...`)。
2. 把密钥写进**仓库根目录**的 `.env`(一行即可):

   ```
   ARK_API_KEY=ark-你的密钥
   ARK_MODEL=doubao-seed-2-0-mini-260428   # 可选,默认已是视觉小模型
   ```

3. 查找链:环境变量 `ARK_API_KEY` → 当前目录 `.env` → 仓库根 `.env`(推荐)→ `~/.manim-teaching-studio/.env`。
4. 验证:`python "<仓库路径>/skills/manim-teaching-studio/scripts/vision_check.py" check <某张图片.jpg>`,输出中文七条报告即成功。

> ⚠️ **安全红线:key 只放 `.env`,绝不写进任何 `.py` 文件**;`.env` 已在 `.gitignore` 中。泄露时立即到控制台吊销重建。

---

## 🚀 三、操作步骤

### 3.1 制作一部教学视频(对话式流水线)

1. 在 AI 会话(Claude Code 等)中说:"做一个 3 分钟以内的**量子隧穿**教学视频"。
2. 流水线自动推进,**在三个 ⛔ 处停下等您拍板**:
   - ⛔#1 九项确认单:主题/时长/分辨率/配色/字体/语言/公式深度/类比/审查交付——一次打包呈现,回复「确认」或逐条修改;
   - ⛔#2 教学脚本 + 科学审查报告:确认后 AI 才开始写代码;
   - ⛔#3 画面审查:此时**浏览器预览**已就绪(见 §3.2),点选元素直接改。
3. 确认 ⛔#3 后自动高清渲染 → 时长校验 → 拼接交付(成品在 `output/`,源码备份在 `backup/`)。

> 只给主题名、没有素材时,流水线会先跑 `topic-research`(联网搜集教材资料,同样先请您确认范围)。
> **分屏续跑**:脚本审完后可开新会话输入「继续生成 projects/<项目名>」直接进入写代码与渲染阶段。

### 3.2 画面预览与回炉(⛔#3 的交互式审查界面)

**第一步:元素级探针**——对每个元素**入场动画结束后 1 秒**的节点,用 Manim 相机亲自渲染无损 PNG(非视频抽帧),并导出每个可见元素的屏幕坐标与「元素 ↔ 代码行号」映射:

```bash
python skills/manim-teaching-studio/scripts/scene_probe.py probe <项目路径> --quality low
```

**第二步:启动预览服务器**:

```bash
python skills/manim-teaching-studio/preview/server.py <项目路径>   # 默认 http://127.0.0.1:5051
```

**第三步:浏览器里改**:

| 能力 | 操作 |
|---|---|
| 浏览 | 左侧选场景/节点(黄点=该节点新出现的元素);「▶ 总预览」连续播放全部场景视频 |
| 选元素 | 点击选中、Ctrl+点击多选、Esc 取消;**鼠标拖拽直接移动**(自动换算 Manim 单位) |
| 调参数 | 右侧边栏:上/下/左/右(步长 0.05~0.5)、颜色、深浅、大小、动画时长、字号、层级——**多次点击自动累加** |
| 排版对齐 | PPT 式:画布水平/垂直居中、左/水平居中/右对齐、顶端/垂直居中/底端对齐、横向/纵向分布 |
| 即时反馈 | 修改后画布立即显示**琥珀色虚线幽灵框 + 位移箭头**(重渲染前预览效果) |
| 回炉重造 | 底部文本框:未选元素=场景级要求,选中元素=元素级要求(自动记录目标) |
| 提交 | 「提交落盘」→ 弹窗可见**提交队列**(按场景归档,可单条删除);同场景重复提交=覆盖 |

**第四步:应用修改**:回到 AI 对话说「**应用修改**」→ AI 按队列逐场景改代码 → lint → 低清重渲染 → 重探针 → 浏览器右上角弹「探针数据已更新」→ 点「重新加载」看最终画面。

> 探针是确定性工具,**只读代码 + 渲染取帧,绝不改您的代码**;修改始终由 AI 会话里的主代理执行。数据占用参考:480p 约 0.3 MB/场景(实测 5 场景 59 节点共 2.1 MB),1080p 约 1.5 MB/场景。

### 3.3 一键启动器(推荐给任意工程)

双击仓库根的 **`preview_launcher.pyw`**:

- 点击选择或**拖入** manim 的 `.py` 文件 / 工程文件夹 → 选画质 → 点「✦ 分析并启动预览」;
- 自动完成:探针生成 → 拉起预览服务器 → 打开浏览器;
- 状态卡实时显示**磁盘占用**(字节/文件数/场景数/节点图数)、日志与服务器状态;
- 「刷新数据」重新生成探针;「删除数据」释放磁盘;**退出时提醒保留或删除数据**;
- 支持白天/黑夜模式切换;探针日志框保持等宽字体,其余中文宋体/英文 Times New Roman。

### 3.4 对任意 Manim 工程使用预览 UI

画面预览是**通用工具**,不限于本仓库布局。任何 Manim 工程(场景代码含 `self.play/wait`)两步接入:

```bash
# 第一步:探针(方式 A 本仓库布局;方式 B 任意单文件,可多次执行叠加,index.json 自动合并)
python <仓库>/skills/manim-teaching-studio/scripts/scene_probe.py probe <工程根目录> --quality low
python <仓库>/skills/manim-teaching-studio/scripts/scene_probe.py file <你的场景.py> [--class 类名] --quality low

# 第二步:预览服务器
python <仓库>/skills/manim-teaching-studio/preview/server.py <工程根目录或 main.py 所在目录>
```

> 代码风格建议(非强制):元素用变量名或 `set_name("中文名")` 命名、`run_time` 显式给出——探针自动用变量名映射代码行号,set_name 让侧边栏显示中文名。"▶ 总预览"需要低清视频按 `media/videos/main/480p15/<类名>.mp4` 存放(先 `MANIM_LOW_RES=1 manim -ql 你的场景.py 类名` 渲染一次即可)。

---

## 🧰 四、脚本工具速览

| 脚本 | 用法 | 说明 |
|---|---|---|
| project_manager.py | `init <slug>` / `validate <路径>` / `status <路径>` | 项目骨架 / 续跑自检 / 产物状态表 |
| manim_lint.py | `lint <项目路径> [--spec spec_lock.md] [--json]` | 6 项静态检查(env-gate/配色白名单/中文字体/背景色等),0 error 才过关 |
| scene_probe.py | `probe <项目> [--scene X] [--quality low\|high]` | 元素级探针(§3.2) |
| scene_probe.py | `file <任意 main.py> [--class X] [--out dir]` | 任意布局单文件探针 |
| scene_probe.py | `analyze <main.py>` | 只输出静态时间线+节点(调试,不渲染) |
| extract_frames.py | `extract <mp4> --out <dir> [--times 0.25,0.5,0.85]` | ffmpeg 抽帧(机器预筛用) |
| vision_check.py | `check <帧图> ["附加要求"] [--out 报告.md]` | 豆包视觉 API 七条清单逐帧审查 |
| render_all.sh | `<项目路径> --quality low\|high [--only sceneXX]` | 批量渲染 + 日志 + durations.tsv |
| preview/server.py | `<项目路径> [--port 5051] [--no-browser] [--timeout 秒]` | 画面预览服务器(单实例锁 `.live_preview.lock`) |
| make_video.py | `<项目路径> [--merged]` | 编号复制 + ffmpeg 无损拼接 + 源码备份 |

---

## 💡 五、常见问题与注意事项

- **画面审查的 API 依赖**:机器预筛需要豆包 key(§2.4);不配置则跳过机器预筛,仍可用浏览器交互式预览。
- **端口冲突**:预览默认 5051(避开 ppt-master 的 5050),可用 `--port` 换端口;启动器会自动复用已运行的服务。
- **外部编辑器慎防回退**:AI 应用修改后,若您的 IDE 同时打开了场景文件并做了覆盖保存,可能回退 AI 的修改——建议 AI 工作时让编辑器只读或先关闭相关文件。
- **纪律红线**:工具脚本只做确定性工作(检查/渲染/抽帧/探针),**场景代码一律由 AI 主代理手写/修改**;`.env` 中的 key 永不入代码、永不提交。
- **更多细节**:工程构造与扩展指南见 `ARCHITECTURE.md`;工作流权威定义见 `skills/manim-teaching-studio/SKILL.md`。

---

**作者**:meteoron_ist · **许可证**:MIT · 欢迎 Star / Issue / PR

