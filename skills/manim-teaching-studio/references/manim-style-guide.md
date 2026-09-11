# Manim 实战规范手册(物理教学动画)

> 沉淀自「Manim Cupe v2.0 / v2.5 / v3.0 / manim_project」量子力学动画项目全部实战经验。
> **本文件是执行者写场景代码的技术规范源**。按需读取:写代码前对照 §3 避坑清单,布局/标注问题对照 §4.3–§4.4,物理动画对照 §5,渲染流程对照 §6。
> 3b1b 视觉语言与公式编排美学细节(TransformMatchingTex 花样、构图节奏)参见 `manim-3b1b-style` skill。

## 目录

- §1 项目架构约定
- §2 场景文件头模板(含低清 env-gate)
- §3 代码编写避坑清单(核心)
- §4 布局与动画模式
- §5 物理正确性验证
- §6 渲染与迭代流程
- §7 最终检查清单

---

## §1 项目架构约定

```
<project>/
├── design_spec.md / spec_lock.md   # 设计书 + 执行契约(策略师产出)
├── sources/                        # 素材
├── scenes/sceneXX_xxx/main.py      # 每场景独立目录,可独立渲染/调试
├── prototypes/                     # 数值模拟/实验代码(物理验证)
├── legacy/                         # 旧版代码存档,永不覆盖删除
├── docs/scripts/  docs/review/     # 脚本、审查报告
├── output/                         # 最终渲染视频
├── render_log/  media/             # 产物(进 .gitignore)
```

- **每场景一个目录**,不要把所有场景写进一个大文件(manim_project 的单文件 7 场景架构已被放弃)。
- 场景目录内自包含:素材放 `assets/`,多版本并存用子目录(如 `furi1_v2/`)。
- 被替换的代码移入 `legacy/`,而不是直接覆盖或删除。

## §2 场景文件头模板

```python
"""场景名 — 一句话描述.

Run:
    manim -pql main.py ClassName    # 低清预览
    manim -pqh main.py ClassName    # 1080p60 高清
"""

from __future__ import annotations
import os
import numpy as np
from manim import *  # noqa: F401,F403

# ---------- 分辨率/帧率(env-gate:MANIM_LOW_RES=1 时低清,供画面审查快速渲染)----------
LOW_RES = os.environ.get("MANIM_LOW_RES", "0") == "1"
config.pixel_height = 480 if LOW_RES else 1080
config.pixel_width  = 854 if LOW_RES else 1920
config.frame_rate   = 15 if LOW_RES else 60

# ---------- 配色(必须与 spec_lock.md ## colors 一致,不得自造)----------
BG_COLOR = "#282c34"
WHITE_   = "#ffffff"   # 注意:不用 WHITE(与 manim 常量冲突)
COL_A    = "#58b9ff"   # 主蓝(A 区 / 入射)
COL_B    = "#8be9fd"   # 青(B 区 / 透射)
ACCENT   = "#ffd866"   # 强调黄(结论 / 标题)
ERR      = "#ff6188"   # 红(势垒 / 经典限制)
GREEN_A  = "#a6e22e"   # 绿(透射 / 反射 / 对比)

FONT     = "Segoe UI"          # 英文/公式
CJK_FONT = "Microsoft YaHei"   # 中文(正式场景可换 "STKaiti" 楷体 / "SimSun" 宋体)
```

`construct()` 第一行设置背景:`self.camera.background_color = BG_COLOR`。

**低清 env-gate 说明**:manim 模块内 `config.pixel_*` 会覆盖 CLI `-pql` 的分辨率(已知坑),因此用 `MANIM_LOW_RES` 环境变量切换 480×854@15 / 1080p60,而不是依赖 CLI 参数。`render_all.sh` 低清档会自动 export 该变量。

**标题模式**(各场景通用):

```python
title_cn = Text("量子隧穿", font=CJK_FONT, font_size=42, color=WHITE_)
title_en = Text("Quantum Tunneling", font=FONT, font_size=28, color=WHITE_).set_opacity(0.55)
title = VGroup(title_cn, title_en).arrange(RIGHT, buff=0.4, aligned_edge=DOWN).to_edge(UP, buff=0.3)
self.add(title)
```

## §3 代码编写避坑清单(核心)

### 3.1 公式与文字必须分离

- **公式用 `MathTex`,中文用 `Text(font=CJK_FONT)`,绝不混用**(MathTex 里不写中文,Text 里不拼公式)。
- 需要混排(如标题带公式)时用 `VGroup(Text(...), MathTex(...)).arrange(RIGHT, buff=...)`。
- 中文 `Text` 一律显式 `font=CJK_FONT`,`font_size` 明确给值;长中文句子单独成 Text。

### 3.2 LaTeX 注意事项

- `\frac` 等命令**必须在单个 `MathTex` 字符串内**,不要用 Python 字符串拼接拆散 TeX 命令。
- 复杂公式用原始字符串 `r"..."`;注入 Python 变量用 `rf"V_0 = {v0:g}E"`。
- 公式局部着色:构造时用**多个子串**传入 `MathTex(part1, part2, ...)`,然后 `expr[2].set_color(COL_A)`(子串拆到不同 submobject)。
- 数量级写法:`r"10^{\,1.48\times 10^{21}}\,\text{s}"`。

### 3.3 已知 API 兼容坑

- **`GrowArrow` 在 Manim v0.19.x 有 `scale_tips` 兼容问题**,箭头出现改用 `Create(arrow)`,GrowArrow 出问题就换 Create。
- **Cairo 渲染器 `ThreeDScene` `Surface` 在陡峭高度梯度下出现竖直"针状"伪影**,多方尝试(关 checkerboard、纯色填充、OpenGL 渲染器)无法消除 → **3D 曲面动画改用 matplotlib 渲染**(见 v2.0 prototypes/render_animation.py),Manim 仅作 2D 叠层参考。
- `WHITE` 命名与 manim 常量冲突 → 项目常量统一用 `WHITE_`。
- `python -m manim` 时 `RuntimeWarning: 'manim.__main__' found in sys.modules` 无害可忽略。
- 长文本/多行中文注意 `font_size` 与 `scale()`,避免溢出画布。

### 3.4 透明度层级惯例(避免压过主线)

| 用途 | 透明度 |
|---|---|
| 副标题 | 0.55 |
| 推导中间步骤(淡出保留) | 0.35 |
| 势垒/区域填充 | 0.16~0.22 |
| 轨道/背景图形填充 | 0.10 |

## §4 布局与动画模式

### 4.1 布局陷阱

- **`to_edge(UP)` 只改变 Y 不改变 X**;需要水平居中必须显式 `move_to([0, top_y, 0])`。
- 用 `axes.c2p(x, y)` 把**数据坐标**转画布坐标,元素(标签、箭头、Dot)全部放在 c2p 结果上,才能与曲线精确对齐。
- 标签/标注避免与曲线重叠:把区域标签抬高到 y 轴顶端附近(如 `c2p(-2, 5.0)`),不要贴着曲线。

### 4.2 标注与图形同步运动(重要模式)

图像缩放/移动时,如果标注不同步会**漂移**。正确做法"预计算目标位置 → 同一 `play` 内同步 `animate` → 结束后静默微调":

```python
diagram = VGroup(axes, barrier, waves)

# ① 预计算目标位置:临时对 axes 施加相同变换,再取 c2p
axes.save_state()
axes.scale(0.55).to_edge(LEFT, buff=0.3).shift(DOWN * 0.4)
tgt_labI = axes.c2p(-2, 5.0)
tgt_txt_inc = (axes.c2p(-4.5, 3.8) + axes.c2p(-2.5, 3.8)) / 2 + UP * 0.4
axes.restore()

# ② 同一帧内同步动画
self.play(
    diagram.animate.scale(0.55).to_edge(LEFT, buff=0.3).shift(DOWN * 0.4),
    labI.animate.move_to(tgt_labI),
    txt_inc.animate.move_to(tgt_txt_inc),
    run_time=1.0,
)

# ③ 动画后无感知精确修正
labI.move_to(axes.c2p(-2, 5.0))
arr_inc.put_start_and_end_on(axes.c2p(-4.5, 3.8), axes.c2p(-2.5, 3.8))
```

### 4.3 过渡动画选择

- **公式推导的中间步骤淡出而非删除**:`mobj.animate.set_opacity(0.35)`,保留可读性。
- **公式变换用 `TransformMatchingTex(old.copy(), new)`**(基于 TeX 子串匹配),视觉连续不闪跳。
- **多元素错落入场用 `LaggedStart(*[...], lag_ratio=0.25)`**,或逐元素 `self.play` 串联。
- **速率函数**:避免默认线性,用 `rate_func=rate_functions.ease_in_out_sine`、`there_and_back`、`smooth`。
- **强调**:`Indicate`(高亮)、`Flash`(闪光)、`ShowPassingFlash`(沿路径传播)、`Create`/`Write`(绘制/书写)。
- 入场微移:`FadeIn(x, shift=DOWN*0.3)`;概率条生长:`GrowFromEdge(fill, LEFT)`。

### 4.4 动画编排节奏

- 每段用 `# ==== Phase N ====` 分隔注释。
- 节奏为 `play → wait(0.3~0.8) → play`;新概念后必须有 `wait` 留白;结尾 `self.wait(1.5~2.5)`。
- **run_time 全部显式给出**(时长控制的依据,见 spec_lock 的 duration_budget)。

### 4.5 动态联动(实时交互)

用 `ValueTracker` + `always_redraw` 做参数驱动的实时曲线变化(如时域波包 ↔ 能量谱联动、势垒高度随参数变化):

```python
alpha = ValueTracker(0.28)

def curve(x):
    a = alpha.get_value()
    return -np.cos(x) - a * x

dynamic = always_redraw(lambda: axes.plot(curve, x_range=[0, 9.5, 0.01], color=COL_A))
self.add(dynamic)
self.play(alpha.animate.set_value(0.55), rate_func=rate_functions.ease_in_out_sine, run_time=1.5)
```

注意:ValueTracker 动画帧数大(单个动画可到 840 帧@60fps),渲染慢,靠低清预览 + run_time 精确控制。

### 4.6 素材路径

- 相对定位:`IMG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "images")`。
- 素材缺失会导致渲染失败(OSError)→ 提供**程序化 fallback**(如头像用 `make_qman()` 现画),并在 docstring 注明依赖。
- Windows 含空格路径:命令与脚本中目录一律加引号。

## §5 物理正确性验证

1. **数值求解优先**:含时薛定谔方程用分步傅里叶法(split-step Fourier),无条件稳定且幺正(自动守恒概率)。参数集中在 `PARAMS` 字典便于调节。
2. **参数选择要出效果**:调 `E/V₀` 使隧穿/反射/透射三种现象并存(如 `E/V₀ ≈ 0.73`),教学效果最佳。
3. **独立于 Manim 的验证**:用 matplotlib 画概率密度曲面、抽帧诊断、交互查看器,确认物理过程再交付。
4. **能量守恒检查**:吸收边界(CAP)计入"逃逸"概率,终态三者之和体现概率分配,用于自检。
5. **诚实性约定**:透射振幅 ∝√T≈0.029 真实值画出来几乎不可见时,设 **0.05 最小可见振幅下限,但 T 数值显示仍用真实值**(注释注明"画上会消失")。
6. **边界条件**:波函数在势垒两边界 C⁰ 连续;近共振放大问题用透射端取反相处理。
7. **先原型验证再进 Manim**:凡含时物理过程(波包演化/散射/隧穿)必须先在 `prototypes/` 数值验证,确认动画呈现的内容是"对的",再写场景。纯几何示意图可免。

## §6 渲染与迭代流程

1. **先低清预览**:`MANIM_LOW_RES=1 manim -pql main.py ClassName`(快,几十秒),确认布局、动画、物理表现。
2. **再高清成片**:`manim -pqh main.py ClassName`(1080p60,慢)。
3. **小步迭代**:每次修改后先跑低清验证,再逐步提高清晰度;出现布局重叠/漂移先修布局再渲染。
4. 批量渲染用 `scripts/render_all.sh`(逐场景、日志、rc 记录、失败不中断、ffprobe 记实测时长)。
5. ffmpeg 需在 PATH 中,或设置 `FFMPEG_DIR` 环境变量指向含 ffmpeg 的目录(render_all.sh 会自动 export PATH)。
6. 验证通过后注明"××场景低清通过(N 个动画)"。

## §7 最终检查清单(每场景写完后逐项核对,`manim_lint.py` 会自动查 ①②④⑥)

- [ ] ① 文件头部有 docstring:场景描述 + 运行命令
- [ ] ② 有 env-gate config 三行(pixel_height/pixel_width/frame_rate)
- [ ] ③ 方法带类型注解(`-> None`)
- [ ] ④ 使用 spec_lock.md 的配色常量,无硬编码新 HEX
- [ ] ⑤ 中文 `Text` 使用 `CJK_FONT`,公式全用 `MathTex`
- [ ] ⑥ `construct()` 第一行设置背景色
- [ ] ⑦ `to_edge(UP)` 后如需居中已显式 `move_to([0, y, 0])`
- [ ] ⑧ 标注与图像缩放同步运动(save_state → c2p → animate)
- [ ] ⑨ 公式推导中间步骤用 `set_opacity(0.35)` 淡出,非直接消失
- [ ] ⑩ run_time 全部显式,总时长与 spec_lock 的 duration_budget 一致
- [ ] ⑪ 物理内容经数值模拟/原型验证(如适用)
- [ ] ⑫ 低清渲染通过,视觉无重叠、无漂移
- [ ] ⑬ 旧版代码已存 `legacy/`,media 等产物进 .gitignore
