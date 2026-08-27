#!/usr/bin/env python3
"""
查询禅道 Bug 列表
用法: 
  查询指派给我的: python list_bugs.py --assigned_to "xxx" [--status all] [--assigned_date 2024-01-01]
  查询我创建的:   python list_bugs.py --opened_by "xxx" [--opened_date 2024-01-01]
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zentao_client import get_client, ZENTAO_BASE_URL, PURCHASE_PRODUCT_ID


def _get_account(field) -> str:
    """从字段中提取账号，兼容对象和字符串格式"""
    if field is None:
        return ""
    if isinstance(field, dict):
        return field.get("account", "")
    return str(field)


def list_my_bugs(
    assigned_to: str,
    status: str = "all",
    limit: int = 20,
    assigned_date: str = "",
) -> dict:
    """查询指派给指定用户的 bug 列表"""
    client = get_client()
    
    # 禅道 API 的 assignedTo 参数过滤不可靠，需要获取更多数据后在客户端过滤
    # 获取 200 条数据以确保能找到指派给目标用户的 bug
    fetch_limit = 200
    
    # 不依赖 API 的 assignedTo 过滤
    url = f"/api.php/v1/products/{PURCHASE_PRODUCT_ID}/bugs?limit={fetch_limit}"
    result = client.request("GET", url)
    
    if result["status"] != 200:
        return {"success": False, "error": result["data"].get("error", "查询失败")}
    
    bugs = result["data"].get("bugs", [])
    total = result["data"].get("total", len(bugs))
    
    # 客户端过滤：按指派人
    bugs = [b for b in bugs if _get_account(b.get("assignedTo")) == assigned_to]
    
    # 客户端过滤：按状态
    if status and status != "all":
        bugs = [b for b in bugs if b.get("status") == status]
    
    # 客户端过滤：按指派日期
    if assigned_date:
        bugs = [b for b in bugs if (b.get("assignedDate") or "")[:10] == assigned_date]
    
    # 限制返回数量
    bugs = bugs[:limit]
    
    # 统计各状态数量
    stats: dict = {}
    for b in bugs:
        s = b.get("status", "unknown")
        stats[s] = stats.get(s, 0) + 1
    
    status_label = {"active": "未解决", "resolved": "已解决", "closed": "已关闭"}
    stats_display = {status_label.get(k, k): v for k, v in stats.items()}
    
    return {
        "success": True,
        "total": total,
        "count": len(bugs),
        "stats": stats_display,
        "bugs": [
            {
                "id": b["id"],
                "title": b["title"],
                "severity": b.get("severity"),
                "pri": b.get("pri"),
                "status": b.get("status"),
                "assignedDate": (b.get("assignedDate") or "")[:10],
                "url": f"{ZENTAO_BASE_URL}/bug-view-{b['id']}.html",
            }
            for b in bugs
        ],
    }


def list_created_bugs(
    opened_by: str,
    opened_date: str = "",
    opened_date_start: str = "",
    opened_date_end: str = "",
    status: str = "all",
    limit: int = 100,
) -> dict:
    """查询指定用户创建的 bug 列表"""
    client = get_client()
    
    # 禅道 API 的 openedBy 参数过滤相对可靠，但仍需客户端二次过滤
    fetch_limit = max(limit, 200)
    url = f"/api.php/v1/products/{PURCHASE_PRODUCT_ID}/bugs?openedBy={opened_by}&limit={fetch_limit}"
    result = client.request("GET", url)
    
    if result["status"] != 200:
        return {"success": False, "error": result["data"].get("error", "查询失败")}
    
    bugs = result["data"].get("bugs", [])
    
    # 客户端过滤：确保创建人匹配
    bugs = [b for b in bugs if _get_account(b.get("openedBy")) == opened_by]
    
    # 客户端过滤：按状态
    if status and status != "all":
        bugs = [b for b in bugs if b.get("status") == status]
    
    # 客户端过滤：按创建日期
    if opened_date:
        bugs = [b for b in bugs if (b.get("openedDate") or "")[:10] == opened_date]
    elif opened_date_start or opened_date_end:
        if opened_date_start:
            bugs = [b for b in bugs if (b.get("openedDate") or "")[:10] >= opened_date_start]
        if opened_date_end:
            bugs = [b for b in bugs if (b.get("openedDate") or "")[:10] <= opened_date_end]
    
    # 限制返回数量
    bugs = bugs[:limit]
    
    # 统计各状态数量
    stats: dict = {}
    for b in bugs:
        s = b.get("status", "unknown")
        stats[s] = stats.get(s, 0) + 1
    
    status_label = {"active": "未解决", "resolved": "已解决", "closed": "已关闭"}
    stats_display = {status_label.get(k, k): v for k, v in stats.items()}
    
    return {
        "success": True,
        "count": len(bugs),
        "stats": stats_display,
        "bugs": [
            {
                "id": b["id"],
                "title": b["title"],
                "severity": b.get("severity"),
                "pri": b.get("pri"),
                "status": b.get("status"),
                "openedDate": (b.get("openedDate") or "")[:10],
                "url": f"{ZENTAO_BASE_URL}/bug-view-{b['id']}.html",
            }
            for b in bugs
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="查询禅道 Bug 列表")
    parser.add_argument("--assigned_to", help="查询指派给谁的 bug")
    parser.add_argument("--opened_by", help="查询谁创建的 bug")
    parser.add_argument("--status", default="all", help="状态：active/resolved/closed/all")
    parser.add_argument("--limit", type=int, default=20, help="返回数量")
    parser.add_argument("--assigned_date", default="", help="按指派日期过滤 YYYY-MM-DD")
    parser.add_argument("--opened_date", default="", help="按创建日期过滤 YYYY-MM-DD")
    parser.add_argument("--opened_date_start", default="", help="创建日期范围起始")
    parser.add_argument("--opened_date_end", default="", help="创建日期范围结束")
    
    args = parser.parse_args()
    
    if args.opened_by:
        result = list_created_bugs(
            opened_by=args.opened_by,
            opened_date=args.opened_date,
            opened_date_start=args.opened_date_start,
            opened_date_end=args.opened_date_end,
            status=args.status,
            limit=args.limit,
        )
    elif args.assigned_to:
        result = list_my_bugs(
            assigned_to=args.assigned_to,
            status=args.status,
            limit=args.limit,
            assigned_date=args.assigned_date,
        )
    else:
        result = {"success": False, "error": "必须指定 --assigned_to 或 --opened_by"}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
