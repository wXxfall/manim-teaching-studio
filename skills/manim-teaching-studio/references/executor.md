# 执行者(Executor)

> 主代理在 Step 5 切换为本角色,逐场景手写 Manim 代码。技术规范源:`manim-style-guide.md`(按需读对应章节,不全文加载)。

## 一、写码纪律(硬规则,逐条对齐 SKILL.md 全局纪律)

1. **每场景写前必读** `<project_path>/spec_lock.md` —— 颜色/字体/公式/参数一律来自它,不得凭记忆或自造(防上下文压缩漂移)。
2. **逐场景连续写**:一个场景写完(含 docstring、常量、全部 Phase)再写下一个,**禁止分批、禁止子代理代写、禁止脚本批量生成**。
3. **先数值后动画**:spec_lock `## physics` 要求数值验证的场景,先在 `prototypes/` 用 split-step Fourier 等方法验证物理参数(如 E/V₀≈0.73 三现象并存、归一化守恒自检),确认"对的"再写 Manim。纯几何示意图可免。
4. **每场景独立目录** `scenes/<dir>/main.py`(dir 来自 spec_lock `## scenes`),文件头 docstring 含场景描述 + Run 命令;配置与常量照 `templates/scene_template.py`(env-gate config 三行 + spec_lock 配色常量 + FONT/CJK_FONT)。
5. **run_time 全显式**,单个不超过 `## scenes` 的 run_time_max;wait 预算与 shot_table 一致。
6. 布局/标注/公式/动画技巧对照 `manim-style-guide.md` 的 §3 避坑清单、§4 布局与动画模式。
7. 每场景写完立即跑 `python ${SKILL_DIR}/scripts/manim_lint.py lint <project_path>`(0 error 才继续下一场景),再跑低清单场景预览确认无重叠漂移。
8. 改版不覆盖:旧版移 `legacy/`,多版本并存用子目录。
9. **元素命名(交互式画面预览的可点击前提)**:每个会被动画引入的可见 mobject 在构造后调用 `set_name("中文名")`,如 `sample.set_name("样品方块")`、`ray_stokes.set_name("斯托克斯散射")`;同一 play 里的多个 mobject 逐个命名,保证预览里可单独点选。探针优先取 set_name,其次回退代码变量名——变量名是机器标识(映射代码行号),set_name 是给人看的中文标签。VGroup 只作为容器时不需命名,其子元素逐个命名。

## 二、写码顺序建议

1. 读 spec_lock.md(必)→ 2. 从 templates/scene_template.py 复制骨架 → 3. 按场景类型(anchor/definition/derivation/demo)搭布局 → 4. 写 Phase 动画 → 5. lint → 6. 低清预览 → 7. 下一场景。

## 三、物理绘制严谨性要点(manim-style-guide §5 展开)

- 波函数在势垒边界 C⁰ 连续;三段(入射/内部/透射)用联立方程解振幅相位。
- 透射端取反相避免近共振放大;吸收边界 CAP 防波包绕域回卷,逃逸概率计入读数。
- 振幅小到不可见时按 spec_lock 的 honesty 约定:最小可见下限放大绘制,数值显示真实值。
- 参数集中字典(PARAMS)便于调节;关键参数选择"要出效果"(如 E/V₀≈0.73)。

## 四、检查点

每场景完成 = lint 0 error + 低清预览通过(视觉无重叠/漂移)+ 物理内容已按 `## physics` 验证。全部场景完成后进入 Step 6(低清批量渲染 + 画面审查)。
