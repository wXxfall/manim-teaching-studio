# 独立工作流:resume-execute(分屏续跑,Phase B 入口)

> **触发条件**:用户在**新会话**中说"继续生成 projects/<项目名>"或类似。
> Phase A(Step 1~4:初始化、策略师、脚本、科学审查)在旧会话完成;本工作流从磁盘恢复状态,直接进入 Phase B(Step 5 写代码及之后)。

## 流程

1. **Sanity check**:`python ${SKILL_DIR}/scripts/project_manager.py validate <project_path>`
   - 必须存在:design_spec.md、spec_lock.md、docs/scripts/narration.md、docs/scripts/shot_table.md。
   - 缺失 → 停止,告知用户旧会话未完成 Phase A,回到主流水线对应步骤。
2. **读状态**(按需,先读小文件):
   - `spec_lock.md`(必读,执行契约)→ `design_spec.md §VIII 场景大纲`(如记不清)→ `docs/review/science_review.md` 结论(确认已通过)。
   - `python ${SKILL_DIR}/scripts/project_manager.py status <project_path>` 看哪些场景已有代码/产物。
3. **状态判断**:
   - 有场景代码但未渲染 → 从 Step 6(低清批量渲染+画面审查)继续。
   - 无场景代码 → 从 Step 5 逐场景写代码,执行者纪律(每场景写前重读 spec_lock)照旧。
4. 之后完全按主流水线 Step 5~9 推进,三个 BLOCKING 中尚未发生的(#3)照常硬停。

**纪律**:续跑不重跑 Phase A(不重新问九项确认、不重写脚本),一切以磁盘上的 spec/脚本/审查报告为准;若用户要求改设计,回到主流水线 Step 2 走变更。
