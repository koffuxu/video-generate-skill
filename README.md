# video-generate

统一的 AI 视频生成 CLI，一套参数直接调用两个视频生成引擎：

- **[Seedance 2.0 Fast](https://www.volcengine.com/docs/82379)**（火山引擎 Ark，默认引擎）
- **[MiniMax H3](https://platform.minimaxi.com/docs/api-reference/video-generation-v2-create)**（`--engine h3` 切换）

两边都是直接调 REST API（异步任务：提交 → 轮询 → 下载），不依赖任何官方 SDK 或第三方 CLI。

## 特性

- 一套 CLI 参数覆盖两个引擎，切换引擎只改 `--engine`，不用改调用方式
- 支持纯文本生成、多模态参考生视频（参考图片 / 视频 / 音频）、H3 的首尾帧图生视频
- 本地文件自动转 base64 data URI，也支持直接传公网 URL
- 异步模式（`--async`）只拿 `task_id` 不阻塞，配合 `task-get` 子命令手动查询/补下载
- `compare` 子命令：同一份提示词同时喂给两个引擎，自动拼成带引擎字幕的对比视频（可选顺带导出 GIF）
- 两种对比布局：`side-by-side`（左右分屏同时播放，静音）/ `sequential`（先后完整播放，保留原始音轨，缺音轨自动补静音）
- `merge` 子命令：两段已有视频直接拼对比图，纯本地 ffmpeg 操作，不产生任何 API 费用
- 下载前自动创建目标目录

## 快速开始

```bash
pip install -r requirements.txt

mkdir -p ~/.private_key/volcengine ~/.private_key/minimax
echo -n '<火山引擎 Ark API Key>' > ~/.private_key/volcengine/api_key
echo -n '<MiniMax API Key>' > ~/.private_key/minimax/api_key

# 默认引擎 Seedance，阻塞等待并自动下载
python3 video_generate.py generate \
  --prompt "一个男孩在海边打篮球，夕阳，写实质感" \
  --duration 5 --ratio 16:9 --out output/test.mp4

# 切到 H3，指定 768P（比默认 2K 更便宜）
python3 video_generate.py generate \
  --engine h3 --resolution 768P \
  --prompt "一个男孩在海边打篮球，夕阳，写实质感" \
  --duration 5 --ratio 16:9 --out output/test-h3.mp4

# 同一份提示词两边各生成一版，自动拼成左右分屏对比视频 + GIF
python3 video_generate.py compare \
  --prompt "一个男孩在海边打篮球，夕阳，写实质感" \
  --duration 10 --ratio 16:9 \
  --out output/compare/篮球对比.mp4 \
  --gif-out output/compare/篮球对比.gif --gif-duration 4
```

需要 `ffmpeg`（`compare`/`merge` 依赖）：`brew install ffmpeg`

完整参数说明、多模态参考用法、计费参考和已知限制见 [SKILL.md](./SKILL.md)。

## 两个引擎怎么选

没有绝对谁更强，各有各的软肋，实测结论：

- **Seedance**：全局一致性约束（"全程保持不变"类强约束）执行更硬，扛得住大幅度动作镜头，计费透明可实时查账单
- **H3**：近景特写下的产品细节稳定性、物态描述还原（颜色/材质/液体种类）更准，默认分辨率更高（2K），按量购买 API 有 768P 更便宜的档位

拿不准就两边各跑一版对比着看，别只信任一边的官方 demo。

## Star 增长

[![Star History Chart](https://api.star-history.com/svg?repos=koffuxu/video-generate-skill&type=Date)](https://star-history.com/#koffuxu/video-generate-skill&Date)

## 作者

| 平台 | 链接 |
|---|---|
| X（Twitter） | [@koffuxu](https://x.com/koffuxu) |
| 微信公众号 | 可夫小子 |

## License

[MIT](LICENSE)
