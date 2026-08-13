---
name: video-generate
description: 统一的 AI 视频生成技能，通过 API 直接调用 Seedance 2.0 Fast（火山引擎 Ark）或 MiniMax H3（MiniMax 按量购买 API），支持文生视频、多模态参考生视频（图片/视频/音频驱动），默认引擎为 Seedance，可用 --engine 切换到 H3。当用户要求"生成一段视频""跑一个视频测试""用 Seedance/H3 生成视频"时使用。
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

图片 / 视频 / 音频参数支持本地文件路径（自动转 base64 data URI）或公网 URL，可重复传入：

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
