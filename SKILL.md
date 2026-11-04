---
name: video-generate
description: 统一的 AI 视频生成技能，通过 API 直接调用 Seedance 2.0 Fast（火山引擎 Ark）或 MiniMax H3（MiniMax 按量购买 API），支持文生视频、多模态参考生视频（图片/视频/音频驱动），默认引擎为 Seedance，可用 --engine 切换到 H3；还内置 15 种 MG 动态设计风格库（代码驱动、零 API 成本，适合 logo 片头/品牌/科普/花字等），还支持用同一份提示词生成两段视频并自动拼成带引擎字幕的对比视频（横版自动上下堆叠、竖版自动左右分屏，也可强制指定，或用 sequential 先后播放并保留音轨），或直接拼接两段已有视频。当用户要求"做 MG 动画/扁平/像素/玻璃拟态等风格短片"、"生成一段视频""跑一个视频测试""用 Seedance/H3 生成视频""做一个两个引擎的对比视频""拼一个左右分屏/上下对比"时使用。
---

# video-generate：统一视频生成技能

通过 API 直接创建视频生成任务、轮询状态、下载成片，封装了 Seedance 2.0 Fast 和 MiniMax H3 两个引擎的调用差异，命令行参数保持一致，切换引擎只需要改 `--engine`。

## 何时用哪个引擎

- **默认 Seedance 2.0 Fast**：按秒计费透明可实时查账单，全局一致性约束（"全程保持不变"类强约束）执行更硬，尤其扛得住大幅度动作镜头。
- **MiniMax H3**（`--engine h3`）：近景特写下的产品细节稳定性、物态描述还原（颜色/材质/液体种类）更准，默认输出分辨率更高（2K），按量购买 API 支持 768P/2K 两档定价（768P 更便宜）。

两者能力差异的详细实测对比见 `output/seedance-vs-h3/评测文章.md`。没有绝对谁更强，拿不准就两边各跑一版对比着看。

## 前置条件：API Key

```bash
mkdir -p ~/.private_key/volcengine ~/.private_key/minimax
echo -n '<火山引擎 Ark API Key>' > ~/.private_key/volcengine/api_key
echo -n '<MiniMax API Key>' > ~/.private_key/minimax/api_key
```

也可以用 `--api-key` 显式传入，覆盖凭据文件。

依赖：`pip install -r skills/video-generate/requirements.txt`（只需要 `requests`）。

## 基本用法

```bash
# 默认引擎 Seedance，纯文本生成 5 秒视频，阻塞等待并自动下载
python3 skills/video-generate/video_generate.py generate \
  --prompt "一个男孩在海边打篮球，夕阳，写实质感" \
  --duration 5 --ratio 16:9 --out output/test.mp4

# 切换到 H3，指定 768P 档位（比默认 2K 更便宜）
python3 skills/video-generate/video_generate.py generate \
  --engine h3 --resolution 768P \
  --prompt "一个男孩在海边打篮球，夕阳，写实质感" \
  --duration 5 --ratio 16:9 --out output/test-h3.mp4

# 只提交任务，不等待（拿到 task_id 后自己去轮询，适合批量起多个任务）
python3 skills/video-generate/video_generate.py generate \
  --engine seedance --prompt "..." --duration 10 --async

# 手动查询任务状态，成功时下载
python3 skills/video-generate/video_generate.py task-get \
  --engine seedance --task-id cgt-xxxx --out output/result.mp4
```

## 多模态参考生视频

图片 / 视频 / 音频参数支持本地文件路径（自动转 base64 data URI）或公网 URL，可重复传入。注意：Seedance 的 `--reference-video` 只接受公网 URL，传本地文件会报 `reference_video must be a web url`；H3 可以用本地文件。

```bash
python3 skills/video-generate/video_generate.py generate \
  --prompt "全程使用视频1的第一视角构图，全程使用音频1作为背景音乐……" \
  --reference-image ./pic1.jpg --reference-image ./pic2.jpg \
  --reference-video ./ref.mp4 \
  --reference-audio ./bgm.mp3 \
  --duration 11 --ratio 16:9 --out output/r2v.mp4
```

H3 额外支持首尾帧图生视频模式（与 `--reference-*` 互斥，不能混用）：

```bash
python3 skills/video-generate/video_generate.py generate \
  --engine h3 --first-frame start.jpg --last-frame end.jpg \
  --prompt "人物缓缓转身" --duration 5 --out output/i2v.mp4
```

## 生成对比视频（两个引擎同台对比）

`compare` 子命令：同一份提示词分别提交给左右两个引擎，等两边都生成完，自动拼成对比视频，各自左上角烧字幕标注引擎名（默认左 Seedance、右 H3），效果和 `output/seedance-vs-h3/评测文章.md` 里的对比图/动图一致。

拼接布局默认是 `auto`：**按视频实际宽高自动判断**——宽视频（16:9 等横版，含正方形）自动**上下堆叠**，竖视频（9:16 等）自动**左右分屏**，这样拼出来的画面不会变成一个极端的长条形。也可以用 `--layout` 强制指定 `side-by-side`（左右分屏）或 `top-bottom`（上下堆叠）。

```bash
python3 skills/video-generate/video_generate.py compare \
  --prompt "一个男孩在海边打篮球，夕阳，写实质感" \
  --duration 10 --ratio 16:9 \
  --out output/compare/篮球对比.mp4 \
  --gif-out output/compare/篮球对比.gif --gif-duration 4
```

生成后会在 `--out` 同目录留下三份文件：`{名字}-left-seedance.mp4`、`{名字}-right-h3.mp4`（两段原始素材，默认保留，方便单独复查/发布）、以及拼好的对比视频本体；传了 `--gif-out` 还会额外截一段转 GIF（适合直接嵌公众号/小红书正文，微信图文接口对 GIF 大小敏感，建议 `--gif-duration` 控制在 3-5 秒）。

可以用 `--left-engine`/`--right-engine` 互换或指定同引擎对比不同 prompt 场景，`--left-label`/`--right-label` 自定义字幕文字，`--no-keep-source` 合成完删掉两段原始素材省磁盘。

**`side-by-side`/`top-bottom`（也就是 `auto` 自动选出来的这两种）都是静音的**（两段视频同时播放，两条音轨叠在一起没法听），如果想保留音频，显式传 `--layout sequential`：先完整播放第一段（带字幕），再完整播放第二段，音轨原样保留；哪一段没有音轨会自动补一段等长静音，避免 ffmpeg 因为音视频流不匹配而报错。

```bash
python3 skills/video-generate/video_generate.py compare \
  --prompt "一个男孩在海边打篮球，夕阳，写实质感" \
  --duration 5 --ratio 16:9 --layout sequential \
  --out output/compare/篮球对比-先后播放.mp4
```

`--height` 在 `side-by-side` 下是单侧高度、在 `top-bottom` 下不生效；`--width` 在 `top-bottom` 下是单侧宽度、在 `side-by-side` 下不生效；`sequential` 下 `--width`/`--height` 一起决定统一画布尺寸（默认 1280×720，避免不同源分辨率导致黑边）。

**已经有两段视频，只想拼对比图，不想再花钱生成**：用 `merge` 子命令，纯本地 ffmpeg 操作，不调用任何 API：

```bash
python3 skills/video-generate/video_generate.py merge \
  --left seedance-案例.mp4 --right h3-案例.mp4 \
  --left-label "Seedance 2.0 Fast" --right-label "MiniMax H3" \
  --out output/compare/对比.mp4 \
  --gif-out output/compare/对比.gif --gif-duration 4
```

依赖 `ffmpeg`（`brew install ffmpeg`），`compare` 和 `merge` 都需要。

## MG 风格库：代码驱动的 10 秒动画（无需视频 API）

收录自 [mg-styles-15](https://github.com/Vincentwei1021/mg-styles-15)（MIT）。思路：让 AI 写一个能画出任意时刻 `t` 的网页（`window.renderAt(t)`），无头 Chrome 逐帧截图 + ffmpeg 合成画面与配乐，输出逐帧确定的 MP4。15 种风格：逐帧手绘、等轴 2.5D、扁平矢量、线条、3D 渲染、形变、贴纸科普、赛博 HUD、拼贴、极光玻璃、包豪斯、合成波/VHS、像素、液态、综艺花字（竖屏）。

**何时用**：要精确的文字/品牌/数据、特定设计风格、MG/片头/花字类短片，或不想花生视频费用。写实镜头、真人/场景仍用上面的 Seedance/H3。

**怎么用**（详见 `references/mg-styles/README.md`，含 15 种风格速查表、适用场景与流程）：

1. 先读 `references/mg-styles/README.md` 选风格，再读对应 `prompts/<编号-名>.md`。
2. 工作目录放 `output/<任务名>/`；把提示词代码块整段交给 AI，改 `Creative seed`（故事/品牌/文案/配色）与 `Output`（竖屏发布改 1080×1920），保留 `Signature features`。
3. 复用 `references/mg-styles/harness/render.mjs` 渲染（`node render.mjs <demo目录>`，`--stills` 先出关键帧；需 Node ≥ 22.12 + Chrome + ffmpeg，`npm install` 用同目录 `package.json`），配乐参考 `audio-README.md`（mgaudio 库本体未入库，需要时从原仓库取）。
4. 成片用 `rubric.md` 另开 AI 评审，贴回再改一轮；新风格按 `template.md` 自定义。

**注意**：提示词内 `../demos/` 链接指向原仓库；中文字体需自备，否则回退系统字体；同一提示词每次结果不同，需迭代；仅用可商用素材，品牌名用虚构。

## 参数说明

| 参数 | 说明 |
|---|---|
| `--engine` | `seedance`（默认）或 `h3` |
| `--prompt` | 必填，视频描述提示词。建议用工程化写法：主体先定义、镜头按编号拆分、动作拆到肢体细节、结尾加风格约束包（可用 `idiom-video-script` 技能参考格式） |
| `--duration` | 时长（秒），整数，常见范围 4-15 |
| `--ratio` | 画幅比例，默认 `16:9`。h3 走图生视频时会被忽略，按输入图自适应 |
| `--resolution` | h3: `2K`（默认）/ `768P`（更便宜）；seedance 此字段未经官方文档确认支持，谨慎使用，报错就去掉 |
| `--reference-image` / `--reference-video` / `--reference-audio` | 多模态参考素材，可重复传入，本地路径或 URL |
| `--first-frame` / `--last-frame` | 仅 h3，首尾帧图生视频，与 `--reference-*` 互斥 |
| `--generate-audio` | 仅 seedance，是否同步生成背景音频，默认关闭 |
| `--watermark` | 是否加水印，默认不加 |
| `--async` | 只提交任务返回 `task_id`，不等待不下载 |
| `--poll-interval` | 轮询间隔秒数，默认 15 |
| `--max-wait` | 最长等待秒数，默认 900（15 分钟） |

## 计费参考（按官方刊例价，实际以账单为准）

- **Seedance 2.0 Fast**：720P 最低约 0.6-0.8 元/秒
- **MiniMax H3**（按量购买 API）：2K 分辨率 0.8 元/秒，768P 分辨率 0.5 元/秒；输入图片超过 5 张后 0.2 元/张

## 已知限制

- H3 任务查询接口（`task-get`）只能查最近 7 天内的任务，超出会报无效 task_id
- Seedance 的 `resolution` 字段未在官方文档中明确支持，脚本允许传入但不保证生效
- H3 的 `reference_image/video/audio` 与 `first_frame/last_frame` 互斥，不能同时使用（脚本会在提交前拦截并报错）
- `compare`/`merge` 依赖本机 `ffmpeg`（`sequential` 布局还依赖 `ffprobe`，随 ffmpeg 一起装），未安装会直接报错退出
- `side-by-side`/`top-bottom` 固定静音（`-an`），只有 `sequential` 布局保留音轨
- `auto` 布局按视频宽高判断，正方形（宽=高）按上下堆叠处理；探测失败会回退为 `side-by-side` 并打印警告

## 动作迁移（照着参考视频跳舞/表演）

要严格跟随参考视频的动作和节奏时，用 `wan_animate.py`，不要用 Seedance/H3 的参考生视频。Key 放 `~/.private_key/dashscope_api_key`（百炼北京地域）。

```bash
python3 skills/video-generate/wan_animate.py \
  --image 角色带场景全身图.png --video 动作视频.mp4 --mode wan-pro --out output/xxx.mp4
```

- 优先 Move（`wan2.2-animate-move`，0.4 元/秒）：背景和人物都来自图片。Mix（0.6 元/秒）在原视频上替换人物，原片衣服和水印可能残留。
- 正式出片用 `wan-pro`（Move 0.6 元/秒，约 704×1252、25fps）；`wan-std` 只有 15fps，手指易糊，适合先跑 5 秒验证。
- 角色图要高清（豆包 Seedream 出 1600×2848 即可，面积上限约 462 万像素），图片不超过 5MB、边长 200–4096。
- 视频 2–30 秒、边长 200–2048，文件名不要含中文。19 秒 pro 约生成 9–10 分钟。
- 输出不带原音，用 `ffmpeg -i 生成.mp4 -i 原音.m4a -map 0:v:0 -map 1:a:0 -c:v copy -shortest` 合回原音轨。
- 成人舞者迁移到幼儿角色时腿会偏长，角色选大一点的孩子更自然。
- Seedance 的 `reference_video` 必须是网址，不能用本地文件；写实的 AI 人物图可能被判为真人而拦截。
