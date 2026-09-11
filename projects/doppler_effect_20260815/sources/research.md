# 多普勒效应 素材调研

> 调研范围(用户已确认):本科低年级(普物+微积分基础)、标准深度、中文为主。
> 本文件供策略师 Step 2 填 design_spec/spec_lock 与执行者 Step 5 写码时引用,不替代 spec_lock。

## 核心概念与公式清单(供 math_locked 候选)

- **机械波多普勒效应(介质中)**:介质波速 `v` 只由介质决定,与波源/观察者运动无关。
  - 波源静止、观察者以 `v_o` 运动:`f' = f (v ± v_o)/v`(接近取 +,远离取 −)。
  - 观察者静止、波源以 `v_s` 运动:`f' = f · v/(v ∓ v_s)`(接近取 −,远离取 +)。
  - 两者同时运动:`f' = f (v ± v_o)/(v ∓ v_s)`(统一式;接近→频率升高)。
  - 物理根源:波源动 → 波长压缩/拉伸(`λ' = (v ∓ v_s)/f`);观察者动 → 相对波速改变;两种机制在低速一阶近似下等价,严格值不同。
- **光(电磁波)多普勒**:无介质,仅取决于波源与观察者的相对速度。
  - 纵向相对论公式:`f_obs = f_s sqrt((1+β)/(1−β)), β = v/c`;低速近似 `Δf/f ≈ v/c`;红移/蓝移。
- **反射式测速(雷达/超声)**:信号往返两次频移,`f_d = 2 f_0 v cosθ / c`。
- 附带工具公式:`v = λf`(波速=波长×频率),周期 `T = 1/f`。

## 教学叙事线索(现象 → 理论 → 直觉,对标"先故事→公式→澄清")

1. **现象(故事)**:1842 年奥地利物理学家 Christian Doppler 提出;1845 年 Buys Ballot 用火车+号手实验验证。今天人人都听过:救护车鸣笛驶近时音调变高、驶离时变低。
2. **理论(公式)**:接收频率 = 每秒接收到的完整波数。分两步推导——① 波源动:一个周期内波源追着波跑,波长被压缩 `λ' = (v−v_s)/f` → `f' = v/λ'`;② 观察者动:波长不变,但观察者相对波的速度变为 `v±v_o` → `f' = (v±v_o)/λ`。合起来得统一公式。
3. **直觉**:分子是"谁在追波",分母是"谁在追谁";统一式低速展开后两种情形趋同,但严格值不同(教学重点)。
4. **应用**:交警雷达测速(10.525 GHz 微波往返频移)、医学超声测血流(2~10 MHz)、天文红移(哈勃定律)、声呐。
5. **澄清**:波速不由波源决定;只有接近/远离分量产生频移;光多普勒无介质、高速需相对论公式。

## 关键参数与数值(供 physics 节候选)

- 20°C 空气中声速 `v = 343 m/s`(常取 340)。
- 救护车 100 km/h ≈ 27.8 m/s 驶近静止观察者:`f' = 340/(340−27.8)·f ≈ 1.089 f`(约 +9%)。
- 交警雷达:f₀ = 10.525 GHz,车速 100 km/h → 往返频移约 ±1.95 kHz。
- 医用超声:f₀ = 2~10 MHz,血流 0.3~1 m/s → Δf 约几百 Hz~几 kHz(角 θ 影响)。
- 太阳自转边缘线速度约 2 km/s → 谱线相对偏移 `Δλ/λ ≈ 6.7×10⁻⁶`。
- 哈勃定律:`v = H₀ d`,`H₀ ≈ 70 km/s/Mpc`(用于红移讲解)。

## 常见误解与教学禁区(供 forbidden 候选)

1. **"声源运动会改变波速"**(错:波速由介质决定,声源动只压缩/拉伸波长)——必须显式澄清。
2. **混淆声源动与观察者动两种情形**:两者频移公式不同(低速近似才趋同),需分开推导、指出差异。
3. **把"音调变化"当响度变化或心理错觉**:实际是接收频率的物理变化(AJP 1997 论文专门研究此误区)。
4. **把声学多普勒公式直接套到光**:光无介质、只取决于相对速度,高速必须用相对论公式。
5. 禁区:符号规则写反(接近必升高、远离必降低);光的多普勒用"介质风"类比;未经说明的横向多普勒。

## 参考来源(每条附 URL)

- 大学物理网络课程 第 11 章 多普勒效应(上海交大):http://www.phycai.sjtu.edu.cn/pub/webphy/content/ch11/sec1109.htm
- 大学物理(第五版)电子课件 10-6 多普勒效应:http://read.cucdc.com/cw/83639/78485.html
- OpenStax University Physics 17.7 The Doppler Effect(公式与符号规则):https://pressbooks.online.ucf.edu/phy2048tjb/chapter/17-7-the-doppler-effect/
- 维基百科:多普勒效应:https://zh.wikipedia.org/wiki/%E5%A4%9A%E6%99%AE%E5%8B%92%E6%95%88%E5%BA%94
- LibreTexts:5.7 Doppler Effect for Light:https://byui-physics.github.io/OpenStaxPhysicsInteractive/textbook_files/af275420-6050-4707-995c-57b9cc13c358-at-aa8a43e-colon-25aab831-7b83-47f9-8c12-27e1715cddf4.html
- AJP:Overcoming naïve mental models in explaining the Doppler shift(教学误区研究):https://pubs.aip.org/aapt/ajp/article-abstract/65/7/618/1044640/
- 多普勒效应与相对运动的问题剖析(知网·科技风 2019):https://wap.cnki.net/touch/web/Journal/Article/KJFT201931190.html
- The Doppler Effect:Now Widely Accepted and Easy to Use(DigiKey 应用综述):https://www.digikey.nl/en/blog/the-doppler-effect-now-widely-accepted-and-easy-to-use
