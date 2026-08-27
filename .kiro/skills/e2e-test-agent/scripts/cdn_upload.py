#!/usr/bin/env python3
"""
CDN 文件上传工具

将文件上传到 Yamibuy CDN，返回可访问的 URL。

使用方式:
    # 上传单个文件
    python scripts/cdn_upload.py --file reports/OP-35677/stage4_first_test.html

    # 上传多个文件
    python scripts/cdn_upload.py --file reports/OP-35677/stage4_first_test.html --file reports/OP-35677/first_test_result.json

    # 指定 content-type
    python scripts/cdn_upload.py --file report.html --content-type text/html
"""

import argparse
import json
import os
import sys
import urllib.request
import uuid

UPLOAD_URL = "https://rs.yamibuy.tech/resource/upload"


def upload_file(file_path: str, content_type: str = None) -> dict:
    """
    上传文件到 CDN

    Args:
        file_path: 本地文件路径
        content_type: 文件 MIME 类型（不指定则根据扩展名推断）

    Returns:
        {"success": True, "url": "https://cdn.yamibuy.tech/...", "name": "..."}
        或 {"success": False, "error": "..."}
    """
    if not os.path.exists(file_path):
        return {"success": False, "error": f"文件不存在: {file_path}"}

    # 推断 content-type
    if not content_type:
        ext = os.path.splitext(file_path)[1].lower()
        content_type_map = {
            ".html": "text/html",
            ".json": "application/json",
            ".css": "text/css",
            ".js": "application/javascript",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".pdf": "application/pdf",
            ".txt": "text/plain",
        }
        content_type = content_type_map.get(ext, "application/octet-stream")

    boundary = uuid.uuid4().hex
    file_name = os.path.basename(file_path)

    with open(file_path, "rb") as f:
        file_data = f.read()

    def field(name, value):
        return (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n').encode()

    body = (
        field("type", "common") +
        field("channel", "Yamibuy") +
        field("local", "local") +
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{file_name}"\r\nContent-Type: {content_type}\r\n\r\n'.encode() +
        file_data +
        f'\r\n--{boundary}--\r\n'.encode()
    )

    try:
        req = urllib.request.Request(
            UPLOAD_URL,
            data=body,
            headers={
                "token": "example-token",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            body_list = result.get("body", [])
            if body_list:
                url = body_list[0].get("url", "")
                return {"success": True, "url": url, "name": body_list[0].get("name", "")}
            else:
                return {"success": False, "error": f"上传响应无 body: {result}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description='CDN 文件上传工具')
    parser.add_argument('--file', required=True, action='append', help='要上传的文件路径（可多次指定）')
    parser.add_argument('--content-type', help='文件 MIME 类型（不指定则自动推断）')

    args = parser.parse_args()

    results = []
    for file_path in args.file:
        result = upload_file(file_path, args.content_type)
        results.append({"file": file_path, **result})
        if result["success"]:
            print(f"✅ {os.path.basename(file_path)} → {result['url']}", file=sys.stderr)
        else:
            print(f"❌ {os.path.basename(file_path)} → {result['error']}", file=sys.stderr)

    # 输出 JSON 结果到 stdout
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
