# 执行契约(Spec Lock)— 拉曼光谱

## project
- slug: raman_spectroscopy
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
- color_role: laser=green_a, stokes=err, antistokes=col_a, rayleigh=white_, title=accent
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
- scene02: dir=scene02_energy, class=EnergyScene, type=definition, duration_budget=32, run_time_max=3
- scene03: dir=scene03_classic, class=ClassicScene, type=derivation, duration_budget=45, run_time_max=3
- scene04: dir=scene04_fingerprint, class=FingerprintScene, type=demo, duration_budget=40, run_time_max=3
- scene05: dir=scene05_clarify, class=ClarifyScene, type=anchor, duration_budget=36, run_time_max=3

## scene_rhythm
- scene01: anchor
- scene02: definition
- scene03: derivation
- scene04: demo
- scene05: anchor

## scene_layouts
- scene01: "居中标题+英文副标题,下方绿激光照样品示意(绿光入、白/红/蓝三色出),底部年份引言"
- scene02: "左侧能级图(基态与振动激发态实线、虚态虚线、三条散射箭头),右侧公式面板;阶段1 瑞利 → 阶段2 斯托克斯 → 阶段3 反斯托克斯"
- scene03: "上半经典推导(诱导偶极 p=αE、极化率展开、三频率分量,中间步骤淡出),下半光谱示意(中央白瑞利峰+左红斯托克斯峰+右蓝反斯托克斯峰);阶段2 收拢到拉曼位移定义"
- scene04: "左侧指纹谱线图(三个峰带数值标注),右侧选律+红外互补面板;结尾应用图标一行"
- scene05: "三个澄清卡片依次出现(✗ 误区红字 → ✓ 正解绿字),收尾总结条"

## math_locked
- 能量守恒: r"h\nu' = h\nu_0 \pm h\nu_{\mathrm{vib}}"
- 拉曼位移定义: r"\Delta\bar{\nu} = \frac{1}{\lambda_0} - \frac{1}{\lambda'}"
- 诱导偶极: r"\mathbf{p} = \alpha\,\mathbf{E}"
- 极化率展开: r"\alpha(Q) = \alpha_0 + \left(\frac{\partial\alpha}{\partial Q}\right)_0 Q"
- 简谐振动坐标: r"Q(t) = Q_0 \cos(2\pi \nu_{\mathrm{vib}} t)"
- 三频率分量: r"\nu_0,\quad \nu_0-\nu_{\mathrm{vib}},\quad \nu_0+\nu_{\mathrm{vib}}"
- 强度比: r"\frac{I_{\mathrm{AS}}}{I_{\mathrm{S}}} = \left(\frac{\nu_0-\nu_{\mathrm{vib}}}{\nu_0+\nu_{\mathrm{vib}}}\right)^4 e^{-h\nu_{\mathrm{vib}}/k_B T}"
- 拉曼选律: r"\left(\frac{\partial\alpha}{\partial Q}\right)_0 \neq 0"
- 红外选律: r"\left(\frac{\partial\mu}{\partial Q}\right)_0 \neq 0"
- 着色约定: 多子串 MathTex(part1, part2, ...)后 expr[i].set_color(...)
- 排版约定: \frac 不拆散;rf"..." 注入变量;长推导中间步 set_opacity(0.35)

## physics
- sim_method: none(纯几何/解析示意,无含时动力学过程)
- analytic_check: 300K 下 h\nu_vib/k_BT ≈ 4.8(取 \nu_vib = 1000 cm⁻¹),e^(-4.8) ≈ 0.008
- worked_example: 532 nm 激发 + 520 cm⁻¹ 位移 ⇒ \lambda' ≈ 547 nm(数字必须真实)
- honesty: 谱峰高度比按玻尔兹曼因子真实取值;虚态一律虚线并标注"非真实能级"

## forbidden
- physics_forbidden: 禁止"拉曼是吸收过程"表述;禁止把虚态说成真实能级;禁止暗示拉曼位移随激光波长变;禁止把振动激发态说成散射中间态;禁止"反斯托克斯与斯托克斯等强"
- visual_forbidden: 禁止硬编码本表之外的新 HEX;禁止虚态实线绘制

## delivery
- render_quality: low_then_high
- visual_review: 按 phase 边界抽帧,每场景 2~4 帧
- subtitle_density: 3.5~5s/句
- merged: true
- backup: true
