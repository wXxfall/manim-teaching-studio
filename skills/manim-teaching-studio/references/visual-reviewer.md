# 画面审查流程(Visual Reviewer)

> Step 6 的执行规范:低清批量渲染后,机器预筛(豆包视觉 API)+ **交互式画面预览**(浏览器点选元素修改)双轨并行,⛔ BLOCKING #3 呈用户。
> 引擎:`scripts/vision_check.py`(机器预筛,API key 见 README)、`scripts/scene_probe.py` + `preview/server.py`(交互式预览,见 `workflows/live-preview.md`)。

## 一、流程总览

```
render_all.sh low(全部场景低清 mp4)
  ├─ 机器预筛:extract_frames.py 抽帧 → vision_check.py 七条清单逐帧审查
  └─ 交互式预览:scene_probe.py probe(入场后 1s 节点 + 无损 PNG + 元素 bbox + 代码行号映射)
        → preview/server.py(浏览器画布:点选元素 → 右侧控件 → 底部回炉重造)
        → 用户提交 → docs/review/rework/request.json
        → 用户说「应用修改」→ 主代理改码 → lint → 重渲染+重探针 → 浏览器自动刷新
  → 汇总 docs/review/visual_review.md(A/B/C 分级)
  → A 级修复循环(单场景最多 2 轮,超限 Needs-Manual)
  → ⛔ BLOCKING #3:审查报告 + 预览地址 + 抽帧图打包呈用户
```

**设计意图**:机器预筛拦截低级问题(重叠/溢出/错字)且零主上下文消耗;交互式预览把"改哪里、怎么改"的掌控交给用户——点元素、调参数、写要求,AI 只负责执行落盘的修改(纪律 #6/#9 场景代码仍由主代理亲自改)。

## 二、抽帧策略(extract_frames.py)

- 对每场景低清 mp4,按 spec_lock `## scene_layouts` 的阶段(phase)边界取时间点,每 phase 1 帧。
- 场景 phase > 5 时,改为 15% / 50% / 85% 时间点共 3 帧。
- 输出:`docs/review/frames/sceneXX_phaseN.jpg`。
- ffmpeg 查找链:PATH → `FFMPEG_DIR` 环境变量。

## 三、逐帧审查(vision_check.py)

- 固定七条中文清单:① 布局是否平衡、有无元素重叠遮挡 ② 小图/分面板内坐标轴、曲线、文字是否清晰可辨、颜色分明 ③ 面板元素是否对齐、是否溢出边界 ④ 任何元素是否被画布边缘裁剪 ⑤ 文字是否过小难读 ⑥ 顶部标题是否完整 ⑦ 公式渲染是否错乱。
- **附加要求**:由 spec_lock `## scene_layouts` 该阶段预期元素派生(如"左下角应出现 2×2 小图且四色分明"),逐帧传入。
- temperature 0.1;每帧一次调用,失败重试 1 次。

## 四、汇总与分级(docs/review/visual_review.md)

| 级别 | 定义 | 处理 |
|---|---|---|
| **A** | 必须修:遮挡/溢出/裁剪/错字/公式错乱/文字过小 | 改代码(或应用 request.json)→ 重跑该场景低清 → 重探针 → 复审 |
| **B** | 建议修:轻微不平衡/间距不佳 | 顺手修,不阻塞 |
| **C** | 风格偏好 | 记录,不改 |

- 汇总表在前(场景×帧×级别+一句话问题),逐条细节按需展开。
- **修复循环**:A 级所在场景改代码(用户浏览器提交的修改按 `workflows/live-preview.md` Step 2 应用)→ 重渲染该场景 → 重探针 → 复审该场景;**单场景最多 2 轮**,超限标 `Needs-Manual` 交用户裁决。
- 全部 A 清零(或 Needs-Manual 已裁决)后,进入 ⛔ BLOCKING #3。

## 四-补、交互式预览要点(scene_probe.py + preview/server.py)

- **节点 = 元素入场动画结束后 1 秒**(透明度已拉满、画面稳定);间隙不足 1 秒取中点;相距 ≤0.5s 合并;场景末帧必为节点。多元素同 play 入场合并为同一节点。
- **探针图是 Manim 相机亲自渲染的无损 PNG**(不是视频抽帧),同帧导出每个可见元素的屏幕像素 bbox + 变量名 + 定义行号 + 入场 play 行号/run_time。
- **元素命名**:优先 mobject 的 `set_name("中文名")`,其次代码变量名;新场景按 executor.md 纪律给可见元素逐个 set_name。
- **控件操作语义**:上/下/左/右=shift(Manim 单位);颜色=set_color(须仍出自 spec_lock 配色);深浅=set_opacity;大小=scale;动画时长=入场 play 的 run_time;字号=font_size(仅 Text);层级=set_z_index。全部操作 + 自由文本落盘 `docs/review/rework/request.json`,由主代理应用。
- 探针静态分析支持:辅助函数内联(返回值变量重命名)、常量 for 循环展开(enumerate/range/字面量,循环局部变量自动加 `#itN` 后缀)、`# ==== Phase N ====` 分段归属。

## 五、⛔ BLOCKING #3 呈现格式

打包呈现:
1. 画面审查汇总表(每场景:A/B/C 数量 + 关键问题一句话)
2. **画面预览地址 http://127.0.0.1:5051**(可点选元素直接改;服务器未启动则按 live-preview 工作流启动)
3. 抽帧图目录路径(用户自行查看,主代理不逐张描述)
4. Needs-Manual 条目(如有,逐条列裁决请求)
5. 结尾:"确认画面无误请回复『确认』,进入高清渲染;或在预览里点选元素提交修改,回到对话说『应用修改』。"

用户确认后进入 Step 7 高清渲染;用户提出修改 → 修改对应场景 → 重跑该场景低清+抽帧复审 → 再次确认。
