# FA26 Studio A2 — 阶段二：Spectral Space（可导航 3D 光谱感知空间）
## 设计分析 + 本地写码 prompt

---

## 0. 数据事实核对（已读，未运行任何构建代码）

| 项 | 值 |
|---|---|
| 文件 | `data/philadelphia and cherry springs data/DRL_spectra.csv`、`CSSP_spectra.csv` |
| DRL | Drexel, Philadelphia（城市）· 5383 条原始 / **3199 条有效** |
| CSSP | Cherry Springs State Park, PA（暗夜公园）· 3755 条原始 / **3192 条有效** |
| 形状 | 566 行 × N 列；**列 = 一条光谱**（按时间），行 = 元数据 + 波长 |
| 行 1 | timestamp，格式 `05-Jul-2014 19:30:28`（注意行 1 末尾有空列，比数据列多 1） |
| 行 2 | date_id（观测夜编号，1…N） |
| 行 3 | solar elevation (deg) |
| 行 4 | lunar elevation (deg) |
| 行 5 | lunar illuminated fraction (0–1) |
| 行 6–566 | **561 个波长 bin = 280–840 nm，步长 1 nm**（此常数不在文件内，来自 `analysis/light_spectra_analysis.py`） |
| 单位 | W·m⁻²·nm⁻¹，downwelling vector irradiance |
| 缺陷 | DRL 饱和 323 / NaN 或零 1861；CSSP 零 559。大量 cell 为 `0.0`（探测底噪）或 `NaN`（探测器截止） |
| 来源 | Spitschan et al. 2016, *Scientific Data*, 2014 年 6/30–7/19 |

**天文夜筛选**（沿用你已有脚本的口径）：`solar elevation < −18°`。结果约 Philadelphia 1200 条、Cherry Springs 854 条。

**已确认的两个决定：**
1. 两个独立 3D 空间 = **Philadelphia（城市）vs Cherry Springs（暗夜）**，不混合。
2. 空间骨架 = **混合方案：数据轴 + 场景比例尺**。

---

## 0.5 全局约定（每一轮 prompt 都必须重复这两条）

### A. 代码位置

所有代码与构建产物写入：

```
/Users/lindaxiangyideng/Documents/FA26 studio A2/claude_code/
```

- 这是一个**新建目录**，第一轮时创建。
- **只读**上级的 `data/` 与 `analysis/`，绝不修改它们。
- 项目根目录（`analysis/`、`*.py`、`visual tests/`、各种 concept png）保持原样不动。
- 上级路径在代码里用相对路径引用：`../data/...`、`../analysis/...`；不要在源码里硬编码 `/Users/lindaxiangyideng/...` 绝对路径（`.venv` 的调用命令除外）。

### B. 语言

**所有文件内容一律英语**，包括：

| 范围 | 要求 |
|---|---|
| 目录名、文件名 | English, `snake_case`（Python）/ `kebab-case` 或 `camelCase`（JS） |
| 代码标识符、函数名、变量名 | English |
| 注释、docstring | English |
| JSON key 与字符串值（含 `source` 引用、物种名、显示映射说明） | English |
| 界面上所有可见文案（标签、按钮、刻度、METHODS 面板全文、脚注） | English |
| README、commit message、CLI 输出与报错 | English |

中文**只出现在我们的对话里**，以及这份规划文档。代码库里任何位置出现中文都算不合规，需要改掉。

> 理由不止是一致性：这是要放进 portfolio 的项目，英文代码库和英文界面是可展示的前提；而且 `species.json` 里的文献出处、物种学名本来就是英文，混写会很难看。

---

## 1. 空间骨架（混合方案的具体定义）

一个立方体数据域，落在一块隐含地面上，尺度按真实米数解释。

```
X 轴  波长 λ        280 nm → 840 nm        映射到 0 → 24 m（场景宽度）
Z 轴  夜间时间 t     日落 → 日出            映射到 0 → 16 m（场景深度）
Y 轴  log10 辐照度   floor → ceil           映射到 0 → 9 m（场景高度）
```

- **Y 的 floor/ceil 必须两个空间共用同一套**，否则 Philadelphia 和 Cherry Springs 的高度不可比，整个对比就废了。**实测结果（第一轮已跑）：`log10` 域 = `[-10, -5]`**，取两站合并后的 **p0.1 / p99.9** 再向外圆整。不要用 p1/p99——那会把 Cherry Springs 最暗的 1.56% 压到地面，而那 1.56% 里有 321 个 cell 落在 320–400 nm，正是只有鸟和虫能看见的那一段。改用 p0.1/p99.9 后只裁掉 Philadelphia 4 个、Cherry Springs 71 个 cell。
- **Z 轴的实际实现是「合成夜」**：数据跨 19 个夜晚，按录制顺序等间隔抽样会让 Z 轴在不同夜之间跳变、画面出现条带。所以按「距该夜太阳最低点的小时数」把所有夜折叠成一夜，再按时间 bin 取中位数光谱。实测范围 **−2.75 h → +3.00 h**，240 个 bin，每 bin 1.4 分钟。`build_data.py --time-mode sequential` 可一键切回原始顺序。
- **两站在高度上几乎不重叠**，这正是想要的效果：映射进 9 m 立方体后，Philadelphia 占 0.8–9.0 m（中位 6.7 m），Cherry Springs 占 0.0–5.5 m（中位 3.6 m）。城市的点云浮在上层，暗夜公园的贴着地面。
- **地面 y = 0** 画一条极淡的网格（仅两三条 hairline，不要完整 grid）。
- **参考高度线**（水平细线 + 右端 mono 小标签）：
  - `0.02 m` 地栖昆虫
  - `1.55 m` 人眼
  - `9 m` 立方体顶（= 最亮）
  - 鸟的高度在立方体之上，用一条虚线 + `≈ 40 m` 标注，实际相机放在 28–35 m 处（保证画面能装下整个立方体）
- **坐标轴渲染**：`#1b2431` 级别的 hairline，只在立方体的三条「近角」边上画刻度；刻度文字 IBM Plex Mono 9–10px，`#7d8a9e`。不要画完整的 wireframe box，只要三条轴 + 若干淡刻度线。

### 点云

每个点 = 一个 (t, λ) 采样：
- position = 上面三轴映射
- 携带属性：`lambda`（nm）、`irradiance`（原始 W·m⁻²·nm⁻¹）、`quality`（0=正常, 1=零值/底噪, 2=NaN/饱和）

**降采样预算**：时间取 240 列（等间隔抽样天文夜内的列），波长取 2 nm 步长（281 bin）→ **约 67,000 点/空间**。用单个 `THREE.Points` + `ShaderMaterial` 渲染，性能无压力，视觉密度也刚好（1200×561 = 67 万点会糊成一团雾）。

---

## 2. 光谱 → 颜色：两段式管线

这是整件作品的技术核心，也是唯一不能糊弄的部分。

### 阶段 A：波段真色（进入空间时的默认状态）

每个点按**它自己的波长**着色，用光谱轨迹（spectral locus）色：

1. λ → CIE 1931 `x̄(λ), ȳ(λ), z̄(λ)`（用解析近似式即可，Wyman–Sloan–Ludwig 多高斯拟合，几行代码，精度足够）
2. XYZ → linear sRGB → gamma
3. 超出 380–700 nm 的部分（UV 280–380、NIR 700–840）**不是黑色**——人类看不到，所以渲染成**去饱和的冷灰**（`#3a4354` 附近），并在进入时用一次扫掠动画点亮，明确告诉观众「这段存在但你看不见」。这是全片最重要的一句视觉论述。

亮度 = `normalize(log10(irradiance))`，控制点的 alpha 和 size（size 范围 1.5–5 px，DPR 感知）。

### 阶段 B：物种感知假色（点击动物后过渡）

**原理**：每个点是单一波长的窄片，所以某物种对它的响应可以纯粹写成波长的函数——一维 LUT。这让整套东西能在 vertex shader 里跑，切换物种只换一个 uniform，不重建 geometry。

对物种 i 的第 k 个感光细胞：

```
Q_k(λ) = S_k(λ) · E(λ) · (λ / hc)      // W → 光子通量
```

`S_k(λ)` 用 **Govardovskii 视色素模板**（A1 色素，给定 λmax 就能生成整条曲线，公开公式，20 行代码）。鸟类再乘上油滴的截止透射。

然后做 **von Kries 归一化**（每个通道除以该物种在该空间整夜的平均响应），避免某个通道恒定压倒其他通道。

**显示映射（必须在界面上标注为 false colour）：**

| 物种 | 感光细胞 λmax (nm) | 可见范围 | 屏幕映射 |
|---|---|---|---|
| **人（明视）** | S 420 · M 534 · L 564 | 400–700 | 真色（CIE → sRGB），这是唯一"不假"的一档 |
| **人（暗视 / 杆细胞）** | 507（单通道） | 400–620 | 单色蓝灰，Purkinje 位移；可作为人视角的子状态 |
| **鸟（UVS 型鸣禽）** | U 372 · S 449 · M 504 · L 565 | 300–700 | R=L, G=M, B=S；**U 通道不混进 RGB**，而是渲染成点外围的一圈冷紫 halo + size 加成。四维压三维必然丢信息，把丢失做成可见的第四层，比硬塞进 RGB 诚实得多 |
| **夜行蛾** | UV 350 · B 440 · G 530 | 300–650 | R=G-receptor, G=B-receptor, B=UV-receptor（整体左移一档）。UV 强的点会烧成刺眼的蓝紫 |
| **地栖甲虫** | UV 360 · G 530（弱蓝） | 300–620 | 双通道：R=G-receptor, B=UV-receptor, G=两者均值。色相极窄，画面接近双色 |
| **萤火虫** | UV ~360 · Y-G 545 | 350–620 | R=G=Y-receptor（黄绿主导），B=UV。可加一条水平参考线标出 Photinus 生物发光的 560 nm，让观众看到城市光谱正好压在它的通讯频道上 |

**每个物种的点数不同**——切换到鸟的瞬间，280–380 nm 那一整片原本灰掉的点会**亮起来**；切换到人的瞬间，它们重新灰掉。这就是整个交互的高潮，不需要额外解释文案。

> 数值说明：上表的 λmax 是文献常见代表值，写码前请让模型标注每个数字的出处并写进 `species.json` 的 `source` 字段，展示层的 methods 面板直接读这个字段。不要让数字只活在代码注释里。

---

## 3. 物种视角 = 相机（交互核心）

五个（或六个）`PerspectiveCamera`，点击左栏物种条目后过渡。

| 视角 | 位置（场景米） | 朝向 | FOV | 运动 |
|---|---|---|---|---|
| **Default** | (18, 11, 22)，看向立方体中心 | 正三维透视 | 42° | 静止；缓慢 auto-rotate（≤0.2 °/s），用户一拖就永久停止（沿用上一个 artifact 的做法） |
| **人** | (12, 1.55, 26)，站在立方体外正前方 | 水平，微微抬头 | 55°（近人眼） | 静止；允许左右转头 ±40°，不允许飞行 |
| **鸟** | (12, 32, 14) | 俯视 −72° | 75° | 缓慢沿一条大半径弧线漂移，像盘旋 |
| **地栖甲虫** | (10, 0.02, 9)，在立方体**内部**贴地 | 仰视 +70° | 100°（近广角/鱼眼感） | 极慢的小幅位移，像爬行 |
| **夜行蛾** | 绕**当前最亮的点**做半径 1.2–2.5 m 的李萨如轨道 | 始终 lookAt 那个点 | 65° | 持续飞舞；轨道不规则（三个不同频率叠加），不要用完美圆形 |
| **萤火虫**（可选） | (14, 0.9, 12)，草丛高度 | 水平偏上 | 70° | 悬停 + 随机小跳 |

**过渡实现**：不要瞬切。对 position 和 quaternion 做 1.2 s `easeInOutCubic` 插值（quaternion 用 `slerp`，直接插值欧拉角会翻滚）；同时对物种颜色 LUT 做一个 0.8 s 的 crossfade uniform `uMix`，让颜色变化和相机移动**错开一点**（颜色稍晚 0.3 s），观众才能分别感知到「我移动了」和「世界变色了」两件事。

**退出**：任何视角下按 Esc 或点「default」回到默认视角。人视角保留有限的头部转动，其余视角锁定用户控制（因为运动本身是内容的一部分）——这一点要在 UI 上用一个小 `LOCKED` 标记说明，否则观众会以为交互坏了。

---

## 4. 视觉语言：与 Earth After Dark 的连贯与区隔

### 继承（保证这是同一个项目的两个阶段）

- 背景 `#05070c`，面板 `#0b1017`，hairline `#1b2431`，主文字 `#e9ecf2`，次级 `#7d8a9e`
- 字体系统：**Archivo 800**（标题，letter-spacing −0.02em）+ **IBM Plex Mono**（全部数字、坐标、刻度，`font-variant-numeric: tabular-nums`）
- 微标签：10–11px、大写、letter-spacing 0.06–0.08em、`#7d8a9e`
- 一个超大的 mono display 数字作为画面锚点
- 全出血 canvas + 一条窄侧栏的布局
- 所有边框 1px hairline，**无圆角、无阴影、无渐变**（除极淡的面积填充）
- 底部一段承认作品局限的小字脚注（上一个 artifact 里那段「VIIRS 看不见颜色」的角色）

### 区隔（避免变成同一个东西的第二版）

| 维度 | Earth After Dark | Spectral Space |
|---|---|---|
| 强调色 | 固定 sodium amber `#ffa62b` + cool `#7fb3ff` | **取消固定强调色**。画面里唯一的饱和色就是光谱本身；UI chrome 全部中性灰白。这是最重要的一条区隔 |
| 侧栏 | 右栏 · 50 城排行 + % 条 | **左栏** · 物种列表，每条 = 剪影图标 + 该物种可见波段的一条微型光谱条（不是百分比条） |
| Display 数字 | 年份 `2024` | **波长** `589 nm` 或当前物种名；hover 点位时实时变化 |
| 时间控件 | 底部横向 scrubber + play | **右侧边缘竖向**的夜间时间轴（日落→日出），刻度是 solar elevation 而非时钟；无自动播放，或播放按钮做得很小 |
| 主交互 | 拖动地球 / 点城市 | **切换视角**。拖动在多数视角下被锁定 |
| 画面几何 | 球体，圆形轮廓主导 | 立方体 + 直线坐标轴，硬边主导 |

**不要照搬的具体元素**：地球贴图式的 texture crossfade、排行榜列表、amber/blue 二元配色、底部 transport bar 的形态。

### 两个空间之间的切换

顶部一个二选一的极简 toggle：`PHILADELPHIA / CHERRY SPRINGS`。切换时**保持当前物种和当前相机不变**——同一只蛾子，同一个高度，换一片天空。这个约束会让对比的冲击力最大化。

---

## 5. 技术栈与文件结构

全部位于 `FA26 studio A2/claude_code/`，文件名与内容一律英语：

```
FA26 studio A2/
├── data/                              ← 只读，不改
├── analysis/                          ← 只读，复用 load_spectra()
└── claude_code/                       ← 本阶段所有代码都在这里
    ├── README.md                      # English
    ├── package.json
    ├── vite.config.js
    ├── index.html
    ├── preprocess/
    │   ├── build_data.py              # CSV → compact binary + manifest
    │   └── species.py                 # Govardovskii template, CIE fit, LUT generation
    ├── public/data/
    │   ├── philadelphia.bin           # Float32 (240 × 281) ≈ 270 KB
    │   ├── cherry_springs.bin
    │   ├── manifest.json              # axis ranges, timestamps, λ array, log10 floor/ceil
    │   └── species.json               # λmax, visible range, LUTs, channel mapping, citations
    └── src/
        ├── main.js
        ├── scene.js                   # scene, axes, reference height lines
        ├── points.js                  # BufferGeometry + ShaderMaterial
        ├── shaders/points.vert|.frag
        ├── cameras.js                 # six camera rigs + slerp transitions
        └── ui.js                      # left rail, night timeline, methods panel
```

- **three.js r160+**，Vite 开发，`vite build` 出静态站
- 预处理用项目根的 `.venv`（`claude_code/` 内不要再建一个），从 `claude_code/preprocess/` 用相对路径 `../../analysis/light_spectra_analysis.py` 复用 `load_spectra()`；若直接 import 不便，就把该函数复制一份到 `preprocess/` 并在注释里注明来源，**但逻辑与波长轴必须完全一致**
- 数据走 `.bin` + `fetch` + `new Float32Array(buffer)`，**不要 JSON 存数值矩阵**（67 万个浮点的 JSON 是几十 MB，二进制是 270 KB）
- 上一个 artifact 的教训：如果最终要发 artifact，外部 CDN 是被挡的，`.bin` 也不能用 `fetch` 从 `file://` 读。所以**开发期用 `vite dev`，交付期决定是发布成 Artifact（把 .bin 转 base64 内联）还是给 zip + 本地 server**。这个决定要在开工前定，会影响数据打包方式。

---

## 6. 必须写进界面的诚实性声明

这几条不是免责声明，是这个作品的论点本身。放进一个可展开的 `METHODS` 面板，**逐字使用下面的英文定稿**，不要让模型改写或重译——措辞本身是论点的一部分。

最后一条直接呼应 brief 里的「系统看不见什么」，也是整个 METHODS 面板的落点，不要把它排在中间。

### 定稿：METHODS 面板（paste verbatim）

```
METHODS AND LIMITS

Downwelling spectral irradiance, 280–840 nm at 1 nm, recorded every
~60 s at Drexel University, Philadelphia and at Cherry Springs State
Park, Pennsylvania, 30 June – 19 July 2014. Spitschan, Aguirre, Brainard
& Sweeney, Scientific Data 3:160032 (2016). Only spectra recorded below
−18° solar elevation are shown.


NOT A PHYSICAL SCENE

The data is a time series of irradiance measured at one point, not a
light field. This cube is a data domain: width is wavelength, depth is
the passage of the night, height is intensity. The heights at which the
animals stand are a scale metaphor. None of them observed this light
from these positions.


NON-HUMAN COLOUR IS FALSE COLOUR

Humans cannot see ultraviolet and cannot see in four channels. What
reaches the screen is a projection of another animal's photoreceptor
responses onto three screen primaries. It is not what a bird sees. The
bird's ultraviolet channel is drawn as a separate halo rather than mixed
into red, green and blue, so that the part which cannot be shown stays
visible as something withheld.


PHOTORECEPTOR VALUES ARE LITERATURE AVERAGES

Peak sensitivities are representative values drawn from the published
literature, not measurements of animals present at these two sites.
Sensitivity curves are generated from the Govardovskii et al. (2000) A1
visual pigment template. They ignore oil droplet variation, opsin
polymorphism, neural processing downstream of the receptor, and the
state of adaptation of an eye that has been in the dark for hours.


THE TWO SITES ARE NOT A CONTROLLED COMPARISON

Philadelphia and Cherry Springs were measured on different nights under
different lunar conditions. Cherry Springs' astronomical-night sample
falls mostly under a darker moon. The difference shown here is
descriptive. It is not an estimate of the effect of a city.


ZERO IS NOT DARKNESS

About 3.5% of Cherry Springs' readings between 360 and 700 nm during
astronomical night are recorded as zero, against almost none in
Philadelphia. That is the detector's noise floor, not an absence of
light. Those samples are drawn as hollow points. The instrument reached
its limit, not the night.
```

### 定稿：屏幕底部脚注（一行版，不展开 METHODS 也能读到）

```
Irradiance measured at a single point, 280–840 nm. Colour for every
species except human daylight vision is false colour: a projection of
photoreceptor responses onto a screen that cannot show ultraviolet.
Hollow points are readings at the detector's noise floor — the
instrument's limit, not the night's.
```

> 3.5% 是第一轮 `build_data.py` 实测值（筛选条件仅 `solar elevation < −18°`，未加月相条件）。Philadelphia 同口径下是 0.00%。

---

## 7. 分阶段落地（建议四轮，每轮独立 prompt）

| 轮次 | 产出 | 验收 |
|---|---|---|
| **1. 数据层** ✅ 已完成 | `build_data.py` + `species.py` + `.bin` + `manifest.json` + `species.json` + `README.md` | 打印两站的 log10 分位数、天文夜样本数、各物种 LUT 的峰值位置；确认 floor/ceil 共用 |
| **2. 空间骨架** ✅ 已完成 | Vite + three.js r169、三轴 + 地面线 + 参考高度线 + 默认视角 + 64,068 点单色点云 + HTML 标签层 | 截图：1600×1000 / 820×1180 / 1920×820 三种视口，标签无重叠无溢出；点数与 build_data.py 一致；拖拽后自转永久停止 |
| **3. 光谱着色** ✅ 已完成 | 阶段 A 光谱轨迹真色 + 6 个物种 LUT（281×14 float texture）+ shader crossfade + 左栏物种列表 | 截图对比：人 vs 鸟，280–400 nm 确实点亮/灰掉；蛾/甲虫/萤火虫各自色相不同；Cherry Springs 3,422 个底噪点渲染为空心环 |
| **4. 相机与 UI** | 六个 rig + 过渡 + 左栏 + 时间轴 + methods 面板 + 双空间 toggle | 录一段 GIF：default → 蛾 → 鸟 → default，过渡不抖 |

每轮做完停下来看截图再进下一轮。一次性要四轮的结果，返工成本远高于分四次。

---

## 8. 给我（或任何模型）在本地写码时的 Prompt

### 8.1 通用原则（为什么这样写）

1. **把不在数据里的常数显式写出来。** 波长轴 280–840 nm 不在 CSV 里，不说就一定会被猜错。行 1–5 的含义同理。
2. **先要数据契约，再要渲染。** 让模型先输出 `manifest.json` 的 schema 和实际统计量，你确认后再写 three.js。否则 shader 写好了发现轴范围不对，全部返工。
3. **给性能预算数字，不要给形容词。** 「约 67,000 点、单个 THREE.Points、单次 draw call」比「要流畅」有用一万倍。
4. **明确禁止项。** 「不要用 CSS3DRenderer」「不要把数值矩阵存成 JSON」「不要画完整 wireframe box」——模型的默认选择往往是最普通的那个。
5. **要求自检。** 让它用 Playwright 起 dev server、截图、自己看，再报告。上一个 artifact 就是这么验的。
6. **一次一个阶段，明确 done criteria。** 并且要求它做完停下来，不要连着往下做。
7. **指明复用已有代码。** `analysis/light_spectra_analysis.py` 里的 loader 已经对了，不要让它重写一遍。
8. **每轮都重申写入目录和语言约定。** 模型不会记得上一轮的约束，尤其「输出目录」和「全英文」这两条——第二轮开始会自动漂回项目根目录、注释会开始冒中文。这两句话每次都要粘。
9. **明确「只读上级目录」。** 不写这句，模型有一定概率去"顺手整理"`analysis/` 里已有的脚本。

### 8.2 第一轮可直接复制的 prompt

```
项目路径：/Users/lindaxiangyideng/Documents/FA26 studio A2
这是 studio 作业的第二阶段，最终产出是一个可导航的 3D 光谱感知空间（three.js）。
本轮只做数据预处理层，不写任何前端代码，做完停下来等我确认。

== 全局约定（每轮都适用）==
1. 所有代码和产物写入 /Users/lindaxiangyideng/Documents/FA26 studio A2/claude_code/
   （新建目录）。上级的 data/ 和 analysis/ 只读，绝不修改；项目根目录保持原样。
   源码里用相对路径引用上级，不要硬编码绝对路径。
2. 所有文件内容一律英语：文件名、变量名、函数名、注释、docstring、
   JSON key 与字符串值、README、commit message、CLI 输出、以及日后界面上
   所有可见文案。代码库里任何位置不得出现中文。我们的对话可以是中文。

== 数据事实（不要重新推断，直接用）==
文件：data/philadelphia and cherry springs data/DRL_spectra.csv (Philadelphia, 城市)
     data/philadelphia and cherry springs data/CSSP_spectra.csv (Cherry Springs, 暗夜公园)
结构：566 行 × N 列，列 = 一条光谱。
  行1 timestamp "05-Jul-2014 19:30:28"（行1末尾多一个空列，要 strip）
  行2 date_id  行3 solar elevation(deg)  行4 lunar elevation(deg)  行5 lunar fraction
  行6-566 = 561 个波长 bin = 280..840 nm，步长 1 nm  ← 这个不在文件里
单位：W·m^-2·nm^-1 downwelling vector irradiance (Spitschan et al. 2016)
已有 loader：analysis/light_spectra_analysis.py 的 load_spectra()，直接复用，不要重写。
用项目里的 .venv。

== 本轮任务 ==
在 claude_code/ 下写 preprocess/build_data.py 和 preprocess/species.py，产出：

1. claude_code/public/data/{philadelphia,cherry_springs}.bin
   - 筛选 solar elevation < -18（天文夜）
   - 时间等间隔抽样到 240 列，波长 2nm 步长抽样到 281 bin
   - 内容：Float32Array，形状 (240, 281)，row-major，存 log10(irradiance)
   - 非正值（0 或负）存为哨兵值 -999，NaN 存为 -998，前端要能区分"测不到"和"很暗"

2. claude_code/public/data/manifest.json
   - 两站共用的 log10 floor/ceil（取两站合并后的 p1/p99 再圆整成整数）
   - 每站：抽样后的 timestamp 数组、solar/lunar elevation、lunar fraction、
           实际有效点数、零值点数、NaN 点数
   - 波长数组 (281 个)

3. claude_code/public/data/species.json
   六个物种：human_photopic, human_scotopic, bird_uvs, moth_nocturnal,
             ground_beetle, firefly
   每个包含：
   - 感光细胞 λmax 列表 + 每个数字的文献出处字符串（source 字段，必填）
   - 可见波长范围
   - 用 Govardovskii(2000) A1 视色素模板生成的灵敏度曲线，
     采样到和 .bin 相同的 281 个波长点
   - 显示映射说明（哪个感光细胞进哪个屏幕通道）
   human_photopic 额外给 CIE 1931 真色 LUT（281 × RGB），
   用 Wyman-Sloan-Ludwig 多高斯拟合 x̄ȳz̄ → XYZ → linear sRGB → gamma。

== 禁止 ==
- 不要把数值矩阵存成 JSON
- 不要猜波长轴
- 不要写任何 three.js / 前端代码
- 不要在 claude_code/ 以外的任何位置创建或修改文件
- 代码、注释、JSON、输出里不要出现中文

== 做完请报告 ==
- 两站天文夜样本数、log10 分位数表、最终选定的 floor/ceil
- 每个物种各感光细胞曲线的峰值波长（验证模板实现对不对）
- 每个 .bin 的字节数
- claude_code/ 下的完整文件树
然后停下来。
```

### 8.3 后续三轮的 prompt 骨架

每轮都保留这四段：**(a) 全局约定两条（写入 `claude_code/`、全英文）——不要省；(b) 项目路径 + 上一轮产物路径；(c) 本轮范围 + 明确禁止项；(d) done criteria + 「做完停下来」**。

可直接复制的全局约定段（每轮开头粘一次）：

```
== 全局约定（每轮都适用）==
1. 所有代码和产物写入 /Users/lindaxiangyideng/Documents/FA26 studio A2/claude_code/
   上级的 data/ 和 analysis/ 只读，绝不修改；项目根目录保持原样。
   源码里用相对路径引用上级，不要硬编码绝对路径。
2. 所有文件内容一律英语：文件名、变量名、函数名、注释、docstring、
   JSON key 与字符串值、README、commit message、CLI 输出、界面可见文案。
   代码库里任何位置不得出现中文。我们的对话可以是中文。
```

- **第二轮**追加：三轴映射表（本文档 §1 的九行）、场景尺寸（24 × 9 × 16 m）、参考高度线数值、颜色 token 列表、「只画三条轴不画 wireframe box」、「约 67000 点单 draw call」、要求 Playwright 截图自检。
- **第三轮**追加：§2 的完整映射表、「LUT 在 vertex shader 里采样，切换物种只改 uniform，不重建 geometry」、「鸟的 U 通道不混进 RGB，做成 halo」、「哨兵值 -999 渲染成空心小点」、要求人/鸟两张对比截图。
- **第四轮**追加：§3 的相机参数表、「quaternion 用 slerp」、「颜色 crossfade 比相机移动晚 0.3s」、§4 的区隔清单、**§6 的两段英文定稿（整段粘进 prompt，并写明 paste verbatim, do not rewrite, do not re-translate, do not shorten）**、要求录 GIF。

> §6 的 `[X]%` 占位符要在第一轮跑完后先替换成真实数字，再进第四轮的 prompt。

---

*本文档基于 2026-09-22 对数据文件与 `analysis/light_spectra_analysis.py` 的只读检查。未运行任何构建代码。*
*本文档本身是规划文档、属于「对话」范畴，保持中文；`claude_code/` 内一律英语。*
