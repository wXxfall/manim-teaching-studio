# CLAUDE.md

本文件是 Claude Code 的项目入口。

**任何物理教学视频制作任务或本仓库修改前,必须先读 [`skills/manim-teaching-studio/SKILL.md`](skills/manim-teaching-studio/SKILL.md)。** 本仓库存在的意义是制作物理教学 Manim 动画视频;SKILL.md 是权威工作流,拥有项目创建、角色切换、串行执行、三重 BLOCKING、双重质量门、渲染、时长校验与交付的全部流程。

想理解工程的构造与技术流程(目录职责、脚本数据流、核心机制、扩展点)时,读 [`ARCHITECTURE.md`](ARCHITECTURE.md)。

## 项目概述

Manim 教学工作室:面向大学生的物理教学动画视频制作流水线。多角色协作(策略师 → 科学审查员 → 执行者 → 画面审查)把物理主题变成 3 分钟左右的 1080p60 Manim 动画视频。

**核心流水线**:`素材 → 项目初始化 → 策略师九项确认[⛔] → 教学脚本 → 科学审查[⛔] → 场景代码生成 → 低清渲染+画面审查[⛔] → 高清渲染 → 时长校验 → 拼接交付`

> 只给主题名、无素材:先跑独立工作流 [`topic-research`](skills/manim-teaching-studio/workflows/topic-research.md) 搜集教材资料。
>
> 分屏续跑:新会话说"继续生成 projects/<x>"时,跑 [`resume-execute`](skills/manim-teaching-studio/workflows/resume-execute.md) 从磁盘恢复状态直接进 Phase B。

## 执行要求

- 角色规范在 [`skills/manim-teaching-studio/references/`](skills/manim-teaching-studio/references/):strategist(策略师)、science-reviewer(科学审查)、executor(执行者)、visual-reviewer(画面审查)、manim-style-guide(Manim 实战规范)。
- 工具脚本在 [`skills/manim-teaching-studio/scripts/`](skills/manim-teaching-studio/scripts/):project_manager / manim_lint / extract_frames / vision_check / render_all / make_video。
- 骨架模板在 [`skills/manim-teaching-studio/templates/`](skills/manim-teaching-studio/templates/)。
- 用户工作区在 [`projects/`](projects/),命名 `<slug>_<YYYYMMDD>/`。

## 必须遵守的约定

- **始终用中文回复用户**。
- **写/改 Manim 代码前先读**本 skill 的 `references/manim-style-guide.md`(已吸收全部实战避坑经验:配色/API 兼容坑/布局动画/物理验证),SKILL.md 内会再次提示。
- **API key 安全**:视觉 API key 只放在 `.env`(已被 .gitignore 排除),绝不写进任何 .py 或提交 git。配置方法见 README「API Key 配置」章节。

## 兼容边界

- 本仓库是工作流/skill 包,不是应用或服务脚手架。
- 不要按通用项目惯例建 `tests/`、`.worktrees/`、CI 或强制分支流程,除非用户明确要求。
- 与通用编程 skill 冲突时,以本仓库的 SKILL.md 为准。
