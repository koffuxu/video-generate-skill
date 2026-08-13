#!/usr/bin/env python3
"""统一视频生成 CLI：Seedance 2.0 Fast（火山引擎 Ark）/ MiniMax H3，默认引擎 Seedance。"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
from pathlib import Path

import requests

SEEDANCE_MODEL = "doubao-seedance-2-0-fast-260128"
SEEDANCE_CREATE_URL = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"
SEEDANCE_QUERY_URL = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/{task_id}"

H3_MODEL = "MiniMax-H3"
H3_CREATE_URL = "https://api.minimaxi.com/v2/video_generation"
H3_QUERY_URL = "https://api.minimaxi.com/v2/query/video_generation/{task_id}"

DEFAULT_KEY_PATHS = {
    "seedance": os.path.expanduser("~/.private_key/volcengine/api_key"),
    "h3": os.path.expanduser("~/.private_key/minimax/api_key"),
}


def load_api_key(engine, explicit_key):
    if explicit_key:
        return explicit_key
    path = DEFAULT_KEY_PATHS[engine]
    if not os.path.exists(path):
        print(f"❌ 未找到 {engine} 的 API Key，请传 --api-key，或把凭据存到 {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def to_url_or_data_uri(value, kind):
    """本地文件路径 -> base64 data URI；已是 http(s) 链接则原样返回。"""
    if value.startswith("http://") or value.startswith("https://") or value.startswith("data:"):
        return value
    path = Path(value)
    if not path.exists():
        print(f"❌ 找不到本地文件: {value}")
        sys.exit(1)
    mime, _ = mimetypes.guess_type(str(path))
    if not mime:
        mime = {"image": "image/png", "video": "video/mp4", "audio": "audio/mpeg"}[kind]
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def build_seedance_payload(args):
    content = [{"type": "text", "text": args.prompt}]
    for img in args.reference_image:
        content.append({
            "type": "image_url",
            "image_url": {"url": to_url_or_data_uri(img, "image")},
            "role": "reference_image",
        })
    for vid in args.reference_video:
        content.append({
            "type": "video_url",
            "video_url": {"url": to_url_or_data_uri(vid, "video")},
            "role": "reference_video",
        })
    for aud in args.reference_audio:
        content.append({
            "type": "audio_url",
            "audio_url": {"url": to_url_or_data_uri(aud, "audio")},
            "role": "reference_audio",
        })

    payload = {
        "model": SEEDANCE_MODEL,
        "content": content,
        "generate_audio": args.generate_audio,
        "ratio": args.ratio,
        "duration": args.duration,
        "watermark": args.watermark,
    }
    if args.resolution:
        # 未在官方文档中确认该模型支持此字段，如遇报错请去掉 --resolution 重试
        payload["resolution"] = args.resolution
    return payload


def build_h3_payload(args):
    content = [{"type": "text", "text": args.prompt}]

    has_frame = args.first_frame or args.last_frame
    has_reference = args.reference_image or args.reference_video or args.reference_audio
    if has_frame and has_reference:
        print("❌ H3 的首尾帧模式（--first-frame/--last-frame）与多模态参考模式（--reference-*）互斥，不能同时使用")
        sys.exit(1)

    if args.first_frame:
        content.append({
            "type": "image_url",
            "image_url": {"url": to_url_or_data_uri(args.first_frame, "image")},
            "role": "first_frame",
        })
    if args.last_frame:
        content.append({
            "type": "image_url",
            "image_url": {"url": to_url_or_data_uri(args.last_frame, "image")},
            "role": "last_frame",
        })
    for img in args.reference_image:
        content.append({
            "type": "image_url",
            "image_url": {"url": to_url_or_data_uri(img, "image")},
            "role": "reference_image",
        })
    for vid in args.reference_video:
        content.append({
            "type": "video_url",
            "video_url": {"url": to_url_or_data_uri(vid, "video")},
            "role": "reference_video",
        })
    for aud in args.reference_audio:
        content.append({
            "type": "audio_url",
            "audio_url": {"url": to_url_or_data_uri(aud, "audio")},
            "role": "reference_audio",
        })

    payload = {
        "model": H3_MODEL,
        "content": content,
        "resolution": args.resolution or "2K",
        "duration": args.duration,
        "aigc_watermark": args.watermark,
    }
    # 文生视频（content 仅含 text）必须显式指定 ratio，且不能为 adaptive
    if not has_frame:
        payload["ratio"] = args.ratio if args.ratio != "adaptive" else "16:9"
    elif args.ratio and args.ratio != "adaptive":
        payload["ratio"] = args.ratio
    return payload


def submit_task(engine, api_key, payload):
    if engine == "seedance":
        url = SEEDANCE_CREATE_URL
    else:
        url = H3_CREATE_URL
    resp = requests.post(
        url,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=60,
    )
    data = resp.json()
    if engine == "seedance":
        task_id = data.get("id")
    else:
        task_id = data.get("task_id")
    if not task_id:
        print(f"❌ 任务创建失败: {json.dumps(data, ensure_ascii=False)}")
        sys.exit(1)
    return task_id, data


def query_task(engine, api_key, task_id):
    if engine == "seedance":
        url = SEEDANCE_QUERY_URL.format(task_id=task_id)
    else:
        url = H3_QUERY_URL.format(task_id=task_id)
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=30,
    )
    data = resp.json()
    if engine == "seedance":
        status = data.get("status")
        video_url = None
        if status == "succeeded":
            video_url = data.get("content", {}).get("video_url")
        return status, video_url, data
    else:
        task = data.get("task", {})
        status = task.get("status")
        video_url = None
        if status == "succeeded":
            video_url = task.get("content", {}).get("url")
        return status, video_url, data


def poll_until_done(engine, api_key, task_id, poll_interval, max_wait_seconds):
    elapsed = 0
    while elapsed <= max_wait_seconds:
        status, video_url, data = query_task(engine, api_key, task_id)
        print(f"   [{elapsed:>4}s] status: {status}")
        if status in ("succeeded", "failed", "cancelled"):
            return status, video_url, data
        time.sleep(poll_interval)
        elapsed += poll_interval
    print("⚠️  轮询超时，任务可能仍在后台运行，可稍后用 task get 手动查询")
    return "timeout", None, None


def download(video_url, out_path):
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    resp = requests.get(video_url, stream=True, timeout=120)
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1 << 16):
            f.write(chunk)
    return out_path


def cmd_generate(args):
    api_key = load_api_key(args.engine, args.api_key)
    payload = build_seedance_payload(args) if args.engine == "seedance" else build_h3_payload(args)
    print(f"🚀 提交任务（引擎: {args.engine}）...")
    task_id, _ = submit_task(args.engine, api_key, payload)
    print(f"   task_id: {task_id}")

    if args.async_mode:
        print(json.dumps({"engine": args.engine, "task_id": task_id}, ensure_ascii=False))
        return

    status, video_url, data = poll_until_done(args.engine, api_key, task_id, args.poll_interval, args.max_wait)
    if status != "succeeded":
        print(f"❌ 生成失败或未完成，最终状态: {status}")
        print(json.dumps(data, ensure_ascii=False, indent=2) if data else "")
        sys.exit(1)

    out_path = args.out or f"{args.engine}-{task_id}.mp4"
    download(video_url, out_path)
    print(f"✅ 已下载: {out_path}")
    print(json.dumps({"engine": args.engine, "task_id": task_id, "file": out_path}, ensure_ascii=False))


def cmd_task_get(args):
    api_key = load_api_key(args.engine, args.api_key)
    status, video_url, data = query_task(args.engine, api_key, args.task_id)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    if status == "succeeded" and video_url and args.out:
        download(video_url, args.out)
        print(f"✅ 已下载: {args.out}")


def build_parser():
    parser = argparse.ArgumentParser(description="统一视频生成 CLI：Seedance 2.0 Fast / MiniMax H3")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="创建视频生成任务（默认阻塞等待并下载）")
    gen.add_argument("--engine", choices=["seedance", "h3"], default="seedance", help="生成引擎，默认 seedance")
    gen.add_argument("--prompt", required=True, help="视频描述提示词")
    gen.add_argument("--duration", type=int, default=5, help="时长（秒）。seedance/h3 均支持整数秒，常见范围 4-15")
    gen.add_argument("--ratio", default="16:9", help="画幅比例，如 16:9 / 9:16 / 1:1（h3 图生视频场景会被忽略，按输入图自适应）")
    gen.add_argument("--resolution", default=None, help="分辨率。h3: 2K(默认) / 768P；seedance: 未经官方文档确认，谨慎使用")
    gen.add_argument("--reference-image", action="append", default=[], help="参考图片（本地路径或 URL），可重复传入")
    gen.add_argument("--reference-video", action="append", default=[], help="参考视频（本地路径或 URL），可重复传入")
    gen.add_argument("--reference-audio", action="append", default=[], help="参考音频（本地路径或 URL），可重复传入")
    gen.add_argument("--first-frame", default=None, help="首帧图片（仅 h3，图生视频场景）")
    gen.add_argument("--last-frame", default=None, help="尾帧图片（仅 h3，需搭配 --first-frame）")
    gen.add_argument("--generate-audio", action="store_true", help="seedance：是否同步生成背景音频，默认关闭")
    gen.add_argument("--watermark", action="store_true", help="是否加水印，默认不加")
    gen.add_argument("--api-key", default=None, help="覆盖默认凭据文件")
    gen.add_argument("--out", default=None, help="视频保存路径，默认 {engine}-{task_id}.mp4")
    gen.add_argument("--async", dest="async_mode", action="store_true", help="仅提交任务并返回 task_id，不等待不下载")
    gen.add_argument("--poll-interval", type=int, default=15, help="轮询间隔秒数，默认 15")
    gen.add_argument("--max-wait", type=int, default=900, help="最长等待秒数，默认 900（15 分钟）")
    gen.set_defaults(func=cmd_generate)

    task = sub.add_parser("task-get", help="查询任务状态，成功时可选下载")
    task.add_argument("--engine", choices=["seedance", "h3"], default="seedance")
    task.add_argument("--task-id", required=True)
    task.add_argument("--api-key", default=None)
    task.add_argument("--out", default=None, help="任务成功时下载到该路径")
    task.set_defaults(func=cmd_task_get)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
