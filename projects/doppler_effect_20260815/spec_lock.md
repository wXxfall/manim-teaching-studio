# 执行契约(Spec Lock)

## project
- slug: doppler_effect_20260815
- target_duration: 180
- resolution: 1920x1080
- fps: 60
- audience: undergrad

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

## typography
- font: "Times New Roman"
- cjk_font: "SimSun"
- tex_template: default
- title_size: 42
- body_size: 24
- label_size: 20
- annotation_size: 16

## scenes
- scene01: dir=scene01_intro, class=IntroScene, type=anchor, duration_budget=20, run_time_max=3
- scene02: dir=scene02_waves, class=WavesScene, type=demo, duration_budget=32, run_time_max=3
- scene03: dir=scene03_formula, class=FormulaScene, type=derivation, duration_budget=52, run_time_max=3
- scene04: dir=scene04_applications, class=ApplicationsScene, type=demo, duration_budget=44, run_time_max=3
- scene05: dir=scene05_clarify, class=ClarifyScene, type=anchor, duration_budget=32, run_time_max=3

## scene_rhythm
- scene01: anchor
- scene02: demo
- scene03: derivation
- scene04: demo
- scene05: anchor

## scene_layouts
- scene01: "居中大标题+救护车图标,音调高低示意(高音波密/低音波疏),底部历史一行(1842 提出/1845 验证)"
- scene02: "上方静止波源同心圆波面,下方运动波源波面(前方压缩/后方拉伸),右侧标注波长变化"
- scene03: "左侧波面压缩示意(小图),右侧公式面板;阶段1 观察者动推导 → 阶段2 波源动推导 → 阶段3 统一式+救护车数值例题"
- scene04: "三列应用卡片:雷达测速/医用超声/天文红移,各自带公式与数值;末尾光多普勒点题一行"
- scene05: "三张误区卡片(✗错误红字→✓正解绿字)+底部一句总结条"

## math_locked
- 波速关系: r"v = \lambda f"
- 观察者动中间式: r"f' = \frac{v \pm v_o}{\lambda}"
- 观察者动: r"f' = f\,\frac{v \pm v_o}{v}"
- 观察者动展开: r"f' = f\left(1 + \frac{v_o}{v}\right)"
- 波源动波长: r"\lambda' = \frac{v \mp v_s}{f}"
- 波源动频率: r"f' = f\,\frac{v}{v \mp v_s}"
- 波源动接收式: r"f' = \frac{v}{\lambda'}"
- 统一式: r"f' = f\,\frac{v \pm v_o}{v \mp v_s}"
- 反射式测速: r"f_d = \frac{2 f_0 v \cos\theta}{c}"
- 光多普勒低速近似: r"\frac{\Delta f}{f} \approx \frac{v}{c}"
- 相对论纵向式: r"f_{\mathrm{obs}} = f_s \sqrt{\frac{1+\beta}{1-\beta}}"
- 救护车例题: r"\frac{340}{340-27.8} \approx 1.089"
- 着色约定: 多子串 MathTex(part1, part2, ...)后 expr[i].set_color(...)
- 排版约定: \frac 不拆散;rf"..." 注入变量;长推导中间步 set_opacity(0.35)

## physics
- sim_method: none(纯几何波面示意,免数值模拟)
- condition: 默认声源速度小于波速(v_s < v),不展开激波
- example_sound: v=343 m/s(20°C 空气,画面取 340 计算)
- example_ambulance: v_s=27.8 m/s(100 km/h) 驶近 → f'≈1.089 f(约 +9%,1000 Hz → 1089 Hz)
- example_radar: f0=10.525 GHz,往返频移 2 f0 v/c,100 km/h → ≈1.95 kHz
- example_ultrasound: f0=2~10 MHz,血流 0.3~1 m/s,频移几百 Hz~几 kHz
- honesty: 数值例题输入输出同屏显示,不四舍五入误导

## forbidden
- physics_forbidden: 禁止"声源运动改变波速"表述(波速由介质决定);禁止把声学多普勒公式直接用于光(需说明相对论修正);禁止混淆音调(频率)与响度(振幅);符号规则:接近必升高、远离必降低;光的多普勒高速必须用相对论公式
- visual_forbidden: 禁止硬编码新 HEX;波面同心圆用虚线+低透明度避免视觉噪声;禁止 3D 陡峭 Surface(Cairo 针状伪影)

## delivery
- render_quality: low_then_high
- visual_review: 交互式预览(元素探针+浏览器点选)+ 机器预筛(豆包视觉 API)
- subtitle_density: 3.5~5s/句
- merged: true
- backup: true
