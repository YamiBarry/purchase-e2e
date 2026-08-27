#!/usr/bin/env python3
"""
修改禅道 Bug
用法: python update_bug.py --bug_id 7739 [--title "xxx"] [--assigned_to "xxx"] [--priority "高"]
"""
import argparse
import json
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zentao_client import (
    get_client, build_steps_html, process_images, cleanup_tmp_files,
    ZENTAO_BASE_URL, BUG_TYPES, SEVERITY_MAP, PRIORITY_MAP
)


def update_bug(
    bug_id: int,
    title: str = "",
    steps: str = "",
    assigned_to: str = "",
    op_number: str = "",
    platform: str = "",
    severity: str = "",
    priority: str = "",
    bug_type: str = "",
    image_paths: str = "",
    image_count: int = 0,
    images_base64: str = "",
) -> dict:
    """修改 Bug"""
    client = get_client()
    
    # 获取当前 bug 信息
    current = client.request("GET", f"/api.php/v1/bugs/{bug_id}")
    if current["status"] != 200:
        return {"success": False, "error": f"Bug #{bug_id} 不存在或无权限访问"}
    
    current_data = current["data"]
    current_title = current_data.get("title", "")
    title_match = re.match(r"^(【[^】]+】)*(.*)", current_title)
    current_desc = title_match.group(len(title_match.groups())) if title_match else current_title
    
    # 处理图片
    paths, used_names, tmp_files = process_images(images_base64, image_paths, image_count)
    
    img_tags = []
    for img_path in paths:
        try:
            img_tags.append(client.upload_image(img_path, bug_id))
        except Exception:
            pass
    
    cleanup_tmp_files(tmp_files)
    
    payload = {}
    
    # 处理标题更新
    need_title_update = title or op_number or platform
    if need_title_update:
        new_desc = title if title else current_desc
        if op_number:
            new_op = f"【{op_number}】"
        else:
            op_match = re.search(r"【(OP-\d+)】", current_title)
            new_op = f"【{op_match.group(1)}】" if op_match else ""
        if platform:
            new_platform = platform
        else:
            plat_match = re.search(r"【(app|PC|H5|服务)】", current_title)
            new_platform = plat_match.group(1) if plat_match else "app"
        payload["title"] = f"{new_op}【{new_platform}】{new_desc}"
    
    # 处理 steps 更新
    if steps or img_tags:
        current_steps_html = current_data.get("steps", "")
        # 提取已有的 img 标签
        existing_imgs = re.findall(r'<img[^>]+>', current_steps_html)
        if steps:
            steps_text = steps
        else:
            # 去掉 HTML 标签提取纯文本
            steps_text = re.sub(r"<[^>]+>", "", current_steps_html).strip()
        all_img_tags = existing_imgs + img_tags if not steps else img_tags
        payload["steps"] = build_steps_html(steps_text, all_img_tags if all_img_tags else None)
    
    if assigned_to:
        payload["assignedTo"] = assigned_to
    if severity:
        payload["severity"] = SEVERITY_MAP.get(severity, 3)
    if priority:
        payload["pri"] = PRIORITY_MAP.get(priority, 3)
    if bug_type:
        payload["type"] = BUG_TYPES.get(bug_type, "codeerror")
    
    if not payload:
        return {"success": False, "error": "没有提供任何要修改的字段"}
    
    result = client.request("PUT", f"/api.php/v1/bugs/{bug_id}", json=payload)
    
    if result["status"] == 200:
        return {
            "success": True,
            "bug_id": bug_id,
            "url": f"{ZENTAO_BASE_URL}/bug-view-{bug_id}.html",
            "message": f"Bug #{bug_id} 已更新",
            "updated_fields": list(payload.keys()),
            "images_count": len(img_tags),
        }
    
    return {"success": False, "error": result["data"].get("error", f"更新失败，状态码 {result['status']}")}


def main():
    parser = argparse.ArgumentParser(description="修改禅道 Bug")
    parser.add_argument("--bug_id", type=int, required=True, help="Bug ID")
    parser.add_argument("--title", default="", help="新的 Bug 描述")
    parser.add_argument("--steps", default="", help="新的复现步骤")
    parser.add_argument("--assigned_to", default="", help="重新指派给谁")
    parser.add_argument("--op_number", default="", help="新的 OP 编号")
    parser.add_argument("--platform", default="", help="新的平台")
    parser.add_argument("--severity", default="", help="新的严重程度")
    parser.add_argument("--priority", default="", help="新的优先级")
    parser.add_argument("--bug_type", default="", help="新的 Bug 类型")
    parser.add_argument("--image_paths", default="", help="图片路径，逗号分隔")
    parser.add_argument("--image_count", type=int, default=0, help="从企业微信取最新 N 张图")
    parser.add_argument("--images_base64", default="", help="图片 base64 JSON 数组")
    
    args = parser.parse_args()
    
    result = update_bug(
        bug_id=args.bug_id,
        title=args.title,
        steps=args.steps,
        assigned_to=args.assigned_to,
        op_number=args.op_number,
        platform=args.platform,
        severity=args.severity,
        priority=args.priority,
        bug_type=args.bug_type,
        image_paths=args.image_paths,
        image_count=args.image_count,
        images_base64=args.images_base64,
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
