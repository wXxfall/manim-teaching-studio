# manim-teaching-studio(插件)

> 面向大学物理教学的 **Manim 动画视频制作流水线** —— 把「一个物理主题」变成「3 分钟、科学正确、画面干净的 1080p60 教学动画」。

本目录是一个 **Claude Code 插件**(单 skill 插件,根目录 `SKILL.md` 即入口),同时也是一个标准的 **Agent Skill**(可在 Cursor / Codex 等支持 `skills/` 布局的工具中直接使用)。

## 安装

```bash
# Claude Code 插件市场(推荐)
/plugin marketplace add wXxfall/manim-teaching-studio
/plugin install manim-teaching-studio@manim-teaching-studio

# 通用 Agent Skills
npx skills add wXxfall/manim-teaching-studio
```

手动挂载(把本目录链接到 `~/.claude/skills/`)与详细依赖说明见仓库根 [README.md](../../README.md) §2。

## 这个插件提供什么

| 能力 | 说明 |
|---|---|
| **九步串行流水线** | 项目初始化 → 策略师九项确认单⛔ → 教学脚本 → 科学审查⛔ → 场景代码 → 低清渲染+画面审查⛔ → 高清渲染 → 时长校验 → 拼接交付 |
| **三个 ⛔ 硬停点** | 视频规格、教学内容、画面效果必须由用户显式确认,AI 不替用户做品味决策 |
| **科学审查** | 以大学物理教授视角按五维度 rubric 审查脚本(P0/P1/P2 分级,最多 3 轮) |
| **元素级探针** | 在每个元素**入场动画结束后 1 秒**的节点,用 Manim 相机渲染无损 PNG + 导出元素包围盒与代码行号映射 |
| **浏览器交互式预览** | 点选/拖拽元素、调位置/颜色/深浅/大小/时长/字号/层级、PPT 式排版对齐、提交队列 + 回炉重造文本框 |
| **任意工程可用** | `scene_probe.py file <场景.py>` + `preview/server.py <目录>`,任何 Manim 工程都能接入预览 |

## 使用

装好后在任意会话中说:

> 做一个 3 分钟以内的量子隧穿教学视频

即触发完整流水线;只给主题名时会先联网搜集教材资料。

## 依赖

- 必需:Python 3.10+、Manim CE、ffmpeg(抽帧/拼接)、LaTeX(公式场景)
- 预览功能:Flask;一键启动器:PySide6(可选,缺失自动降级 tkinter)
- 画面机器预筛(可选):火山方舟(豆包)视觉 API key,写在仓库根 `.env`

## 许可

MIT © meteoron_ist
