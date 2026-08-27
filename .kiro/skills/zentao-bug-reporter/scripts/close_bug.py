#!/usr/bin/env python3
"""
关闭禅道 Bug
用法: python close_bug.py --bug_id 7739 [--comment "已修复"]
"""
import argparse
import json
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zentao_client import get_client, ZENTAO_BASE_URL, ZENTAO_ACCOUNT


def close_bug(bug_id: int, comment: str = "") -> dict:
    """关闭 Bug"""
    client = get_client()
    today = time.strftime("%Y-%m-%d")
    
    payload = {
        "status": "closed",
        "closedBy": ZENTAO_ACCOUNT,
        "closedDate": today,
    }
    if comment:
        payload["comment"] = comment
    
    result = client.request("PUT", f"/api.php/v1/bugs/{bug_id}", json=payload)
    
    if result["status"] == 200 and result["data"].get("status") == "closed":
        return {
            "success": True,
            "bug_id": bug_id,
            "url": f"{ZENTAO_BASE_URL}/bug-view-{bug_id}.html",
            "message": f"Bug #{bug_id} 已关闭",
        }
    
    return {"success": False, "error": result["data"].get("error", f"关闭失败，状态码 {result['status']}")}


def main():
    parser = argparse.ArgumentParser(description="关闭禅道 Bug")
    parser.add_argument("--bug_id", type=int, required=True, help="Bug ID")
    parser.add_argument("--comment", default="", help="关闭备注")
    
    args = parser.parse_args()
    
    result = close_bug(bug_id=args.bug_id, comment=args.comment)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
