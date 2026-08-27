# -*- coding: utf-8 -*-
"""
工具类 Action Handlers
"""

import sys
from handlers.base import require_param


def handle_timestamp(client, db, env, args, email):
    """时间戳工具"""
    from modules.utils import action_timestamp
    return action_timestamp(
        ts=args.ts,
        offset=args.offset,
    )


def handle_format_json(client, db, env, args, email):
    """格式化 JSON"""
    from modules.utils import action_format_json
    require_param(args.json_str, "--json 参数")
    return action_format_json(args.json_str)


def handle_compress_json(client, db, env, args, email):
    """压缩 JSON"""
    from modules.utils import action_compress_json
    require_param(args.json_str, "--json 参数")
    return action_compress_json(args.json_str)


# Handler 注册表
UTILS_HANDLERS = {
    "timestamp": handle_timestamp,
    "format_json": handle_format_json,
    "compress_json": handle_compress_json,
}
