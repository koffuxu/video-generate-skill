# MG 动态设计风格库（15 种）

来源：<https://github.com/Vincentwei1021/mg-styles-15>（MIT，作者 Vincentwei1021，用 Claude Opus 5.5 写代码做成；转载保留 `LICENSE`，二次创作建议回链原仓库）。

核心思路：**不调生图/生视频 API，让 AI 写一个“能画出任意时刻 t 的网页”**，用无头 Chrome 逐帧截图，再由 ffmpeg 合成画面与音轨，得到逐帧确定、可精确复现的 10 秒 MG 动画。适合 logo 动画、品牌片头、数据/科普解说、口播花字等“要风格、要精确文字”的短片；写实镜头仍走 `video_generate.py` 的 Seedance/H3。

## 目录

| 路径 | 内容 |
|---|---|
| `prompts/*.md` | 15 份完整提示词（含风格说明、技术路线、10 秒分镜、风格特征、自评清单），整段发给 AI 即可出片 |
| `template.md` | 自定义新风格的四段式模板 |
| `rubric.md` | 成片评审提示词（另开一个 AI 评审→贴回→再改一轮，原片均改了两轮） |
| `harness/render.mjs` | 确定性渲染器：页面暴露 `window.renderAt(t)` 与 `window.__ready=true`，逐帧截图并 ffmpeg 合成 |
| `harness/preview.html` | 浏览器里拖动时间轴预览 |
| `audio-README.md` | 原仓库 `lib/audio`（mgaudio 配乐/音效合成库）的使用说明；库本体含 103 个乐器采样（约数十 MB），未入库，需要时从原仓库取 |
| `package.json` / `requirements.txt` | 渲染器与配乐的依赖版本 |

## 15 种风格速查

| # | 风格 | 提示词 | 画幅/帧率 | 技术路线 | 适用 |
|---|---|---|---|---|---|
| 01 | 逐帧手绘/线条沸腾 | `05-cel-boil` | 16:9 24fps | Canvas2D 变宽笔刷+抖动变体+纸纹 | 手作感品牌、文艺短片 |
| 02 | 等轴 2.5D | `03-isometric` | 16:9 30fps | Three.js 正交相机+软阴影 | 城市/产品/流程可视化 |
| 03 | 扁平矢量 | `01-flat-vector` | 16:9 30fps | SVG+GSAP 弹性缓动 | SaaS 宣传、企业解说（最通用） |
| 04 | 线条动画 | `02-line-art` | 16:9 30fps | SVG stroke-dashoffset+跟笔相机 | 一笔画、品牌 ID |
| 05 | 3D 渲染（C4D 质感） | `04-3d-render` | 16:9 24fps | Blender CLI→PNG 序列+HTML 叠字 | 高端产品片头（需 Blender，最重） |
| 06 | 形变动画 | `08-morph` | 16:9 30fps | SVG+flubber/MorphSVG | 一形多义、转场 |
| 07 | 粗描边贴纸人科普 | `19-paperclip` | 16:9 30fps | 大画布+相机变换+照片贴纸 | 知识科普（回形针/林超风） |
| 08 | 赛博朋克 HUD/FUI | `22-hud` | 16:9 30fps | SVG/Canvas+Three 线框全息 | 科技/游戏/安全产品 |
| 09 | 拼贴剪贴 | `06-collage` | 16:9 30fps(12fps 节拍) | PNG 抠图+半调滤镜 | 杂志感、创意提案 |
| 10 | 弥散渐变/玻璃拟态 | `12-aurora-glass` | 16:9 30fps | WebGL 极光网格渐变+玻璃折射 | AI/软件产品、发布会 |
| 11 | 几何包豪斯 | `09-bauhaus` | 16:9 30fps | SVG/Canvas+严格网格+120BPM | 节奏型卡点、设计类 |
| 12 | 80s 合成波/VHS | `10-synthwave` | 16:9 30fps | WebGL 透视网格+VHS 后处理 | 复古、音乐、游戏 |
| 13 | 像素风 | `20-pixel` | 16:9 30fps | Canvas 320×180 整数倍放大 | 游戏、怀旧 |
| 14 | 液态流动 | `07-liquid` | 16:9 30fps | WebGL2 SDF metaball | 饮品/化妆品/流体品牌 |
| 15 | 综艺花字 | `18-hanazi` | **9:16 竖屏** 30fps | DOM/SVG 多层描边花字+弹簧 | 短视频口播/vlog 包装 |

## 用法（照原仓库流程）

1. 在 `output/<任务名>/` 下新建工作目录（遵守项目 `output/` 约定）。本机需 Node ≥ 22.12、Chrome、ffmpeg、Python ≥ 3.11；3D 风格另需 Blender。
2. 选一份 `prompts/*.md`，把「提示词」代码块整段发给 AI（可改 `Creative seed` 里的故事/品牌/文案/配色，或改 `Output` 的尺寸与时长；**保留 `Signature features`**，它决定风格辨识度）。竖屏发布（抖音/小红书/视频号）把 `Output` 改为 1080×1920。
3. 让 AI 直接复用 `harness/render.mjs` 渲染、`audio-README.md` 里的 mgaudio 配乐，省去重造轮子：
   ```bash
   npm install                                # 安装 puppeteer-core 等
   node harness/render.mjs <demo目录>          # 逐帧渲染 → <demo目录>/out/video.mp4
   node harness/render.mjs <demo目录> --stills 0.5,2,4.25   # 先出关键帧静帧看效果
   ```
   Chrome 不在默认位置时设 `MG_CHROME=<路径>`。预览：在仓库根起 `python3 -m http.server`，打开 `harness/preview.html?demo=<名>`。
4. 评审迭代：另开一个 AI，用 `rubric.md` 评审成片，把意见贴回再改一轮。
5. 新风格：按 `template.md` 填四段（Style / Output / Technical route / Creative seed / Signature features），通用部分从任意提示词复制。

## 注意

- 提示词里的 `../demos/...` 源码链接指向原仓库，本地不存在；需要参考完整源码到原仓库的 `demos/<名>/` 取。
- 中文字体未随原仓库提供，缺字体会回退系统字体，字形与原片不同；字体清单见原仓库 `assets/fonts/README.md`。
- 同一提示词每次出片结果不同，原片是多轮迭代的产物，别指望一次到位。
- 素材只用 CC0/OFL/可商用授权；品牌名用虚构的，避免商标问题。
- 与本技能其他能力的分工：写实镜头/人物 → `video_generate.py`（Seedance/H3）；要精确文字、品牌 ID、数据解说、特定设计风格 → 本风格库（代码出片，零 API 成本）；手绘讲解 → `skills/sweety-handdraw-video`。
