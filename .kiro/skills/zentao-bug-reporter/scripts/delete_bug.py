#!/usr/bin/env python3
"""
删除禅道 Bug
用法: python delete_bug.py --bug_id 7739
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zentao_client import get_client


def delete_bug(bug_id: int) -> dict:
    """删除 Bug"""
    client = get_client()
    
    result = client.request("DELETE", f"/api.php/v1/bugs/{bug_id}")
    
    if result["status"] in (200, 204):
        return {"success": True, "message": f"Bug #{bug_id} 已删除"}
    
    return {"success": False, "error": result["data"].get("error", f"删除失败，状态码 {result['status']}")}


def main():
    parser = argparse.ArgumentParser(description="删除禅道 Bug")
    parser.add_argument("--bug_id", type=int, required=True, help="Bug ID")
    
    args = parser.parse_args()
    
    result = delete_bug(bug_id=args.bug_id)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
