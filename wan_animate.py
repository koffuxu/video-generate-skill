#!/usr/bin/env python3
"""百炼 Wan 2.2 Animate（默认 Move，设 WAN_MODEL=wan2.2-animate-mix 用 Mix）：上传临时存储 -> 建任务 -> 轮询 -> 下载。"""
import argparse, json, mimetypes, os, sys, time
from pathlib import Path
import requests

BASE = "https://dashscope.aliyuncs.com"
MODEL = os.environ.get("WAN_MODEL", "wan2.2-animate-move")


def upload(key, path):
    h = {"Authorization": f"Bearer {key}"}
    r = requests.get(f"{BASE}/api/v1/uploads", params={"action": "getPolicy", "model": MODEL}, headers=h, timeout=30)
    r.raise_for_status()
    d = r.json()["data"]
    obj = f"{d['upload_dir']}/{Path(path).name}"
    fields = {
        "OSSAccessKeyId": d["oss_access_key_id"],
        "Signature": d["signature"],
        "policy": d["policy"],
        "x-oss-object-acl": d["x_oss_object_acl"],
        "x-oss-forbid-overwrite": d["x_oss_forbid_overwrite"],
        "key": obj,
        "success_action_status": "200",
    }
    with open(path, "rb") as f:
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        u = requests.post(d["upload_host"], data=fields, files={"file": (Path(path).name, f, mime)}, timeout=300)
    u.raise_for_status()
    return f"oss://{obj}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--image", required=True)
    p.add_argument("--video", required=True)
    p.add_argument("--mode", default="wan-std", choices=["wan-std", "wan-pro"])
    p.add_argument("--out", required=True)
    a = p.parse_args()
    key = Path(os.path.expanduser("~/.private_key/dashscope_api_key")).read_text().strip()

    img, vid = upload(key, a.image), upload(key, a.video)
    print("✅ 素材已上传到百炼临时存储", flush=True)
    r = requests.post(
        f"{BASE}/api/v1/services/aigc/image2video/video-synthesis",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
            "X-DashScope-OssResourceResolve": "enable",
        },
        json={"model": MODEL, "input": {"image_url": img, "video_url": vid}, "parameters": {"mode": a.mode}},
        timeout=60,
    )
    if r.status_code != 200:
        print("❌ 建任务失败:", r.status_code, r.text[:600]); sys.exit(1)
    tid = r.json()["output"]["task_id"]
    print("task_id:", tid, flush=True)

    start = time.time()
    while time.time() - start < 1700:
        time.sleep(15)
        q = requests.get(f"{BASE}/api/v1/tasks/{tid}", headers={"Authorization": f"Bearer {key}"}, timeout=30).json()
        out = q.get("output", {})
        st = out.get("task_status")
        print(f"[{int(time.time()-start):4d}s] {st}", flush=True)
        if st == "SUCCEEDED":
            url = out.get("results", {}).get("video_url") or out.get("video_url")
            v = requests.get(url, timeout=300); v.raise_for_status()
            Path(a.out).write_bytes(v.content)
            print("✅ 已下载:", a.out, "| usage:", json.dumps(q.get("usage", {}), ensure_ascii=False)); return
        if st in ("FAILED", "CANCELED", "UNKNOWN"):
            print("❌ 任务失败:", json.dumps(out, ensure_ascii=False)[:600]); sys.exit(1)
    print("⏳ 超时未完成，task_id:", tid); sys.exit(2)


if __name__ == "__main__":
    main()
