# AGENTS.md — 非 Claude 类 agent 工具的入口说明

本项目是一个面向大学物理教学的 **Manim 动画视频制作流水线 skill**(harness),配合任何具备"读写文件 + 执行命令 + 多轮对话"能力的 agent(Claude Code、Codex、Cursor 等)使用。

**入口**:任何"制作物理教学视频/动画"类任务,先读 `skills/manim-teaching-studio/SKILL.md`(9 步流水线 + 9 条全局纪律 + 三个 ⛔ 硬停确认点)。

**要点**:

- 三个 ⛔ 硬停点必须等用户显式确认,不得替用户决策;
- 场景代码一律由主 agent 逐场景手写/修改(禁止子代理与脚本代写),每场景写前重读 `spec_lock.md`;
- 工具脚本(scripts/ 下)只做确定性工作:检查、渲染、抽帧、探针、拼接;
- API key 只放 `.env`,绝不写入代码或提交 git;
- 画面审查阶段可用 `scripts/scene_probe.py` + `preview/server.py` 启动浏览器交互式预览(详见 README §3.2)。

工程构造与扩展指南见 `ARCHITECTURE.md`,操作步骤见 `README.md`。
