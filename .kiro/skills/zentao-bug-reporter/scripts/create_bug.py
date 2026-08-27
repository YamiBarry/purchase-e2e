#!/usr/bin/env python3
"""
创建禅道 Bug
用法: python create_bug.py --title "xxx" --steps "xxx" --assigned_to "xxx" [其他参数]
"""
import argparse
import json
import sys
import os

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zentao_client import (
    get_client, build_steps_html, process_images, cleanup_tmp_files,
    ZENTAO_BASE_URL, PURCHASE_PRODUCT_ID, DEFAULT_BUILD,
    BUG_TYPES, SEVERITY_MAP, PRIORITY_MAP, get_product_id_by_op,
    ZENTAO_ACCOUNT, ZENTAO_PASSWORD, ZentaoClient
)


def create_bug(
    title: str,
    steps: str,
    assigned_to: str,
    op_number: str = "",
    platform: str = "app",
    severity: str = "一般",
    priority: str = "中",
    bug_type: str = "代码错误",
    extra_prefix: str = "",
    image_paths: str = "",
    image_count: int = 0,
    images_base64: str = "",
    opened_by: str = "",
) -> dict:
    """创建 Bug"""
    # 如果指定了 opened_by 且不是默认账号，用该账号登录创建
    if opened_by and opened_by != ZENTAO_ACCOUNT:
        client = ZentaoClient()
        import httpx as _httpx
        import time as _time
        resp = _httpx.post(
            f"{ZENTAO_BASE_URL}/api.php/v1/tokens",
            json={"account": opened_by, "password": ZENTAO_PASSWORD},
            timeout=10,
        )
        if resp.status_code in (200, 201) and resp.json().get("token"):
            client._token = resp.json()["token"]
            client._token_expire = _time.time() + 25 * 60
        else:
            # 登录失败，回退到默认账号
            client = get_client()
    else:
        client = get_client()
    
    # 根据 OP 号路由到对应产品
    product_id = get_product_id_by_op(op_number)
    
    # 构建标题
    prefix = f"【{op_number}】" if op_number else ""
    full_title = f"{prefix}【{platform}】{title}"
    if extra_prefix:
        full_title = f"【{extra_prefix}】{full_title}"
    
    # 处理图片
    paths, used_names, tmp_files = process_images(images_base64, image_paths, image_count)
    
    # 第一步：创建 bug
    bug_data = {
        "product": product_id,
        "title": full_title,
        "steps": build_steps_html(steps),
        "assignedTo": assigned_to,
        "openedBuild": DEFAULT_BUILD,
        "severity": SEVERITY_MAP.get(severity, 3),
        "pri": PRIORITY_MAP.get(priority, 3),
        "type": BUG_TYPES.get(bug_type, "codeerror"),
    }
    
    result = client.request("POST", "/api.php/v1/bugs", json=bug_data)
    
    if result["status"] != 201:
        cleanup_tmp_files(tmp_files)
        return {
            "success": False,
            "error": result["data"].get("error", "未知错误"),
            "status": result["status"],
        }
    
    bug_id = result["data"].get("id")
    
    # 第二步：上传图片
    img_tags = []
    for img_path in paths:
        try:
            img_tags.append(client.upload_image(img_path, bug_id))
        except Exception as e:
            pass
    
    # 第三步：有图片则更新 steps
    if img_tags:
        steps_html = build_steps_html(steps, img_tags)
        client.request("PUT", f"/api.php/v1/bugs/{bug_id}", json={"steps": steps_html})
    
    cleanup_tmp_files(tmp_files)
    
    return {
        "success": True,
        "bug_id": bug_id,
        "title": full_title,
        "url": f"{ZENTAO_BASE_URL}/bug-view-{bug_id}.html",
        "message": f"Bug #{bug_id} 创建成功，已指派给 {assigned_to}",
        "images_count": len(img_tags),
    }


def main():
    parser = argparse.ArgumentParser(description="创建禅道 Bug")
    parser.add_argument("--title", required=True, help="Bug 描述内容")
    parser.add_argument("--steps", required=True, help="复现步骤")
    parser.add_argument("--assigned_to", required=True, help="指派给谁")
    parser.add_argument("--op_number", default="", help="OP 编号，如 OP-1234")
    parser.add_argument("--platform", default="app", help="平台：app/PC/H5/服务")
    parser.add_argument("--severity", default="一般", help="严重程度：致命/严重/一般/轻微")
    parser.add_argument("--priority", default="中", help="优先级：紧急/高/中/低")
    parser.add_argument("--bug_type", default="代码错误", help="Bug 类型")
    parser.add_argument("--extra_prefix", default="", help="额外标签，如'线上bug'")
    parser.add_argument("--image_paths", default="", help="图片路径，逗号分隔")
    parser.add_argument("--image_count", type=int, default=0, help="从企业微信取最新 N 张图")
    parser.add_argument("--images_base64", default="", help="图片 base64 JSON 数组")
    parser.add_argument("--opened_by", default="", help="创建人禅道账号，不传则用默认账号")
    parser.add_argument("--chat_id", default="", help="当前会话chatId，用于自动确定opened_by和图片目录")
    
    args = parser.parse_args()
    
    # 根据 chat_id 自动确定 opened_by（如果未显式传入）
    opened_by = args.opened_by
    chat_id = args.chat_id
    
    CREATOR_MAP = {
        "Alan.Li": "Alan_Li",
        "erin.lin": "erin_lin",
        "Phoebe.Song": "Phoebe_Song",
        "renee.zhang": "renee_zhang",
    }
    
    if not opened_by and chat_id:
        wecom_id = chat_id.replace("dm_", "")
        opened_by = CREATOR_MAP.get(wecom_id, "")
    
    # 兜底：从 image_paths 中提取 chat_id
    if not opened_by and args.image_paths:
        # 路径格式: D:/workspace/autoqa-agent/sessions/dm_erin.lin/images/xxx.png
        for img_p in args.image_paths.split(","):
            if "/sessions/dm_" in img_p.replace("\\", "/"):
                parts = img_p.replace("\\", "/").split("/sessions/")[1].split("/")
                chat_id = parts[0]
                wecom_id = chat_id.replace("dm_", "")
                opened_by = CREATOR_MAP.get(wecom_id, "")
                break
    
    # 最终兜底：找最近活跃的 session 记忆文件中的 opened_by
    if not opened_by:
        work_dir = os.environ.get("WORK_DIR", "D:/workspace/autoqa-agent")
        sessions_dir = os.path.join(work_dir, "sessions")
        best_mtime = 0
        if os.path.isdir(sessions_dir):
            for dm_dir in os.listdir(sessions_dir):
                if not dm_dir.startswith("dm_") or dm_dir == "dm_renee.zhang":
                    continue
                ctx_file = os.path.join(sessions_dir, dm_dir, "last_bug_context.json")
                if os.path.exists(ctx_file):
                    mtime = os.path.getmtime(ctx_file)
                    if mtime > best_mtime:
                        try:
                            ctx = json.load(open(ctx_file, encoding="utf-8-sig"))
                            if ctx.get("opened_by"):
                                best_mtime = mtime
                                opened_by = ctx["opened_by"]
                                if not chat_id:
                                    chat_id = dm_dir
                        except Exception:
                            pass
    
    # 设置图片目录环境变量（供 collect_recent_images 使用）
    if chat_id:
        work_dir = os.environ.get("WORK_DIR", "D:/workspace/autoqa-agent")
        os.environ["WECOM_IMAGES_DIR"] = os.path.join(work_dir, "sessions", chat_id, "images")
    
    result = create_bug(
        title=args.title,
        steps=args.steps,
        assigned_to=args.assigned_to,
        op_number=args.op_number,
        platform=args.platform,
        severity=args.severity,
        priority=args.priority,
        bug_type=args.bug_type,
        extra_prefix=args.extra_prefix,
        image_paths=args.image_paths,
        image_count=args.image_count,
        images_base64=args.images_base64,
        opened_by=opened_by,
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
