# projects/ 用户工作区

每个教学视频项目一个目录,命名约定:

```
projects/<slug>_<YYYYMMDD>/
```

- `<slug>`:主题英文小写短横线名(如 `quantum_tunneling`)
- `<YYYYMMDD>`:项目创建日期

由 `python skills/manim-teaching-studio/scripts/project_manager.py init <slug>` 自动创建,目录结构:

```
<slug>_<YYYYMMDD>/
├── README.md              # 项目说明(由 init 生成,自动填入日期/路径)
├── design_spec.md         # 设计书(策略师产出,十一节,人类可读)
├── spec_lock.md           # 执行契约(策略师产出,十节,执行者每场景写前必读)
├── sources/               # 素材(教材/论文/参考图,来自 topic-research 或用户提供)
├── scenes/                # 每场景独立目录 sceneXX_xxx/main.py
├── prototypes/            # 数值模拟/物理验证代码
├── legacy/                # 旧版代码存档,永不覆盖删除
├── docs/
│   ├── scripts/           # 教学脚本 narration.md + 分镜时长预算 shot_table.md
│   └── review/            # 科学审查报告 + 画面审查报告 + 时长报告
├── output/                # 成品视频(编号分场景 + 合并成片)
├── backup/                # 交付前源码存档 <timestamp>/
├── render_log/            # 渲染日志(不入 git)
└── media/                 # manim 产物(不入 git)
```

本目录是工作区,生成物不提交 git(`output/`、`backup/`、`media/`、`render_log/` 已忽略)。
