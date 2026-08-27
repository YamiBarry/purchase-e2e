# -*- coding: utf-8 -*-
"""
工具模块 - 时间戳转换等实用功能
"""

import time
import re
from datetime import datetime, timezone, timedelta


def action_timestamp(ts: int = None, offset: str = None) -> dict:
    """
    时间戳工具：生成或解析时间戳
    
    参数:
    - ts: 要解析的时间戳（秒），不填则使用当前时间
    - offset: 时间偏移量，如 -5m(前5分钟) +1h(后1小时) -1d(前1天)
              支持单位: s(秒) m(分钟) h(小时) d(天)
    
    返回: 时间戳和三个时区的日期时间（UTC、北京、美西）
    """
    _start = time.time()
    
    try:
        # 确定基准时间戳
        if ts is not None:
            base_ts = ts
            description = "指定时间戳"
        else:
            base_ts = int(time.time())
            description = "当前时间"
        
        # 解析偏移量
        offset_seconds = 0
        if offset:
            offset_seconds = _parse_offset(offset)
            if offset_seconds != 0:
                description = f"{description} {offset}"
        
        # 计算最终时间戳
        final_ts = base_ts + offset_seconds
        
        # 转换为三个时区的日期时间
        utc_time = _ts_to_utc(final_ts)
        beijing_time = _ts_to_beijing(final_ts)
        us_west_time, us_west_tz_name = _ts_to_us_west(final_ts)
        
        return {
            "success": True,
            "action": "timestamp",
            "data": {
                "时间戳": final_ts,
                "UTC": utc_time,
                "北京时间 (UTC+8)": beijing_time,
                f"美西时间 ({us_west_tz_name})": us_west_time,
                "描述": description,
            },
            "elapsed": time.time() - _start,
        }
    except Exception as e:
        return {
            "success": False,
            "action": "timestamp",
            "error": str(e),
            "elapsed": time.time() - _start,
        }


def _parse_offset(offset: str) -> int:
    """
    解析时间偏移量字符串
    
    支持格式: -5m, +1h, -1d, 30s, +2h30m
    单位: s(秒) m(分钟) h(小时) d(天)
    
    返回: 偏移秒数（正数表示未来，负数表示过去）
    """
    if not offset:
        return 0
    
    offset = offset.strip()
    
    # 判断正负号
    negative = False
    if offset.startswith("-"):
        negative = True
        offset = offset[1:]
    elif offset.startswith("+"):
        offset = offset[1:]
    
    # 解析数值和单位
    # 支持复合格式如 2h30m
    total_seconds = 0
    pattern = r"(\d+)([smhd])"
    matches = re.findall(pattern, offset.lower())
    
    if not matches:
        # 尝试纯数字（默认秒）
        try:
            total_seconds = int(offset)
        except ValueError:
            raise ValueError(f"无法解析偏移量: {offset}，支持格式如 -5m, +1h, -1d, 30s")
    else:
        unit_map = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        for value, unit in matches:
            total_seconds += int(value) * unit_map[unit]
    
    return -total_seconds if negative else total_seconds


def _ts_to_utc(ts: int) -> str:
    """时间戳转 UTC 时间"""
    dt = datetime.utcfromtimestamp(ts)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _ts_to_beijing(ts: int) -> str:
    """时间戳转北京时间 (UTC+8)"""
    tz_beijing = timezone(timedelta(hours=8))
    dt = datetime.fromtimestamp(ts, tz=tz_beijing)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _ts_to_us_west(ts: int) -> tuple:
    """
    时间戳转美西时间，自动判断夏令时
    
    返回: (日期时间字符串, 时区名称)
    - 夏令时 (3月第2个周日 - 11月第1个周日): PDT, UTC-7
    - 冬令时: PST, UTC-8
    """
    # 先用 UTC-8 计算日期，判断是否在夏令时范围内
    tz_pst = timezone(timedelta(hours=-8))
    dt_pst = datetime.fromtimestamp(ts, tz=tz_pst)
    
    # 判断是否在夏令时范围内
    if _is_dst(dt_pst.year, dt_pst.month, dt_pst.day, dt_pst.hour):
        # 夏令时 PDT (UTC-7)
        tz_pdt = timezone(timedelta(hours=-7))
        dt = datetime.fromtimestamp(ts, tz=tz_pdt)
        return dt.strftime("%Y-%m-%d %H:%M:%S"), "PDT, UTC-7"
    else:
        # 冬令时 PST (UTC-8)
        return dt_pst.strftime("%Y-%m-%d %H:%M:%S"), "PST, UTC-8"


def _is_dst(year: int, month: int, day: int, hour: int) -> bool:
    """
    判断美西时间是否在夏令时范围内
    
    夏令时规则（美国，2007年起）:
    - 开始: 3月第2个周日 02:00 PST → 03:00 PDT（时钟向前拨1小时）
    - 结束: 11月第1个周日 02:00 PDT → 01:00 PST（时钟向后拨1小时）
    
    边界条件说明:
    - 3月切换日 02:00-02:59 PST 不存在（直接跳到 03:00 PDT）
    - 11月切换日 01:00-01:59 会出现两次（先 PDT 后 PST）
    - 本函数在边界时刻按"切换后"处理（3月02:00视为夏令时，11月02:00视为冬令时）
    
    Args:
        year: 年份
        month: 月份 (1-12)
        day: 日期 (1-31)
        hour: 小时 (0-23)，基于 PST (UTC-8) 计算
    
    Returns:
        True 表示在夏令时范围内，False 表示在冬令时范围内
    """
    # 1-2月、12月：一定是冬令时
    if month < 3 or month > 11:
        return False
    
    # 4-10月：一定是夏令时
    if month > 3 and month < 11:
        return True
    
    # 3月: 第2个周日 02:00 开始是夏令时
    if month == 3:
        second_sunday = _nth_weekday_of_month(year, 3, 6, 2)  # 6=Sunday
        if day > second_sunday:
            return True
        elif day == second_sunday:
            # 02:00 及之后视为夏令时（实际上 02:00-02:59 不存在，直接跳到 03:00）
            return hour >= 2
        return False
    
    # 11月: 第1个周日 02:00 之前是夏令时
    if month == 11:
        first_sunday = _nth_weekday_of_month(year, 11, 6, 1)
        if day < first_sunday:
            return True
        elif day == first_sunday:
            # 02:00 及之后视为冬令时（01:00-01:59 会出现两次，这里按 PDT 处理）
            return hour < 2
        return False
    
    return False


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> int:
    """
    获取某月第n个星期几的日期
    
    weekday: 0=Monday, 6=Sunday
    n: 第几个（1-based）
    返回: 日期（1-31）
    """
    # 该月1号是星期几
    first_day = datetime(year, month, 1)
    first_weekday = first_day.weekday()
    
    # 计算第一个目标星期几的日期
    days_until = (weekday - first_weekday) % 7
    first_target = 1 + days_until
    
    # 第n个
    return first_target + (n - 1) * 7


# ══════════════════════════════════════════════════════════════════════════════
# JSON 工具
# ══════════════════════════════════════════════════════════════════════════════

# 中文标点 → 英文标点 映射表（用于 str.translate，使用 Unicode 码点避免编码问题）
_CHINESE_PUNCT_TABLE = str.maketrans({
    '\uff0c': ',',   # ，全角逗号
    '\uff1a': ':',   # ：全角冒号
    '\u201c': '"',   # " 左双引号
    '\u201d': '"',   # " 右双引号
    '\u2018': "'",   # ' 左单引号
    '\u2019': "'",   # ' 右单引号
    '\u3010': '[',   # 【
    '\u3011': ']',   # 】
    '\uff5b': '{',   # ｛全角左花括号
    '\uff5d': '}',   # ｝全角右花括号
})


def _fix_json(json_str: str) -> tuple:
    """
    修复常见 JSON 错误
    
    Returns:
        (fixed_str, fixes_list)
    """
    import re
    fixes = []
    s = json_str
    
    # 1. 中文标点 → 英文（一次 translate 完成）
    new_s = s.translate(_CHINESE_PUNCT_TABLE)
    if new_s != s:
        fixes.append("中文标点→英文")
        s = new_s
    
    # 2. undefined/NaN → null（一次正则）
    new_s = re.sub(r'\b(undefined|NaN)\b', 'null', s)
    if new_s != s:
        fixes.append("undefined/NaN→null")
        s = new_s
    
    # 3. 移除注释
    if '//' in s or '/*' in s:
        s = re.sub(r'//[^\n]*|/\*.*?\*/', '', s, flags=re.DOTALL)
        fixes.append("移除注释")
    
    # 4. 末尾多余逗号
    new_s = re.sub(r',(\s*[\]\}])', r'\1', s)
    if new_s != s:
        fixes.append("移除末尾逗号")
        s = new_s
    
    # 5. 无引号 key
    new_s = re.sub(r'([{\,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', s)
    if new_s != s:
        fixes.append("key加引号")
        s = new_s
    
    # 6. 单引号 → 双引号（需要逐字符处理）
    if "'" in s:
        new_s = _replace_single_quotes(s)
        if new_s != s:
            fixes.append("单引号→双引号")
            s = new_s
    
    return s, fixes


def _replace_single_quotes(s: str) -> str:
    """智能替换 JSON 中的单引号为双引号"""
    result = []
    i, n = 0, len(s)
    in_string = False
    quote_char = None
    
    while i < n:
        c = s[i]
        if not in_string:
            if c == '"':
                in_string, quote_char = True, '"'
                result.append(c)
            elif c == "'":
                in_string, quote_char = True, "'"
                result.append('"')
            else:
                result.append(c)
        else:
            if c == '\\' and i + 1 < n:
                result.append(c)
                result.append(s[i + 1])
                i += 1
            elif c == quote_char:
                in_string = False
                result.append('"' if quote_char == "'" else c)
            elif c == '"' and quote_char == "'":
                result.append('\\"')
            else:
                result.append(c)
        i += 1
    
    return ''.join(result)


def _build_error_context(json_str: str, error: Exception) -> dict:
    """构建 JSON 解析错误的上下文信息"""
    lines = json_str.split('\n')
    line_no, col_no = error.lineno, error.colno
    
    context = []
    for i, line in enumerate(lines, 1):
        if abs(i - line_no) <= 2:
            prefix = ">>> " if i == line_no else "    "
            context.append(f"{prefix}{i:3d} | {line}")
            if i == line_no:
                context.append("    " + " " * 6 + " " * (col_no - 1) + "^")
    
    return {
        "error_position": f"第 {line_no} 行，第 {col_no} 列",
        "context": "\n".join(context),
    }


def action_format_json(json_str: str) -> dict:
    """
    JSON 格式化：美化输出，自动修复常见错误
    """
    import json
    _start = time.time()
    
    if not json_str or not json_str.strip():
        return {"success": False, "action": "format_json", "error": "JSON 为空", "elapsed": 0}
    
    json_str = json_str.strip()
    
    # 先尝试直接解析
    try:
        parsed = json.loads(json_str)
        return {
            "success": True,
            "action": "format_json",
            "data": {"status": "valid", "formatted": json.dumps(parsed, indent=2, ensure_ascii=False)},
            "elapsed": time.time() - _start,
        }
    except json.JSONDecodeError:
        pass
    
    # 尝试修复
    fixed_str, fixes = _fix_json(json_str)
    
    try:
        parsed = json.loads(fixed_str)
        return {
            "success": True,
            "action": "format_json",
            "data": {
                "status": "fixed",
                "fixes": fixes,
                "formatted": json.dumps(parsed, indent=2, ensure_ascii=False),
            },
            "elapsed": time.time() - _start,
        }
    except json.JSONDecodeError as e:
        # 使用修复后的字符串构建错误上下文，因为错误位置是基于修复后的字符串
        ctx = _build_error_context(fixed_str, e)
        return {
            "success": False,
            "action": "format_json",
            "error": f"JSON 解析失败: {e.msg}",
            "data": {**ctx, "attempted_fixes": fixes or "无"},
            "elapsed": time.time() - _start,
        }


def action_compress_json(json_str: str) -> dict:
    """
    JSON 压缩：移除空白，自动修复常见错误
    """
    import json
    _start = time.time()
    
    if not json_str or not json_str.strip():
        return {"success": False, "action": "compress_json", "error": "JSON 为空", "elapsed": 0}
    
    json_str = json_str.strip()
    
    # 先尝试直接解析
    try:
        parsed = json.loads(json_str)
        return {
            "success": True,
            "action": "compress_json",
            "data": {"status": "valid", "compressed": json.dumps(parsed, separators=(',', ':'), ensure_ascii=False)},
            "elapsed": time.time() - _start,
        }
    except json.JSONDecodeError:
        pass
    
    # 尝试修复
    fixed_str, fixes = _fix_json(json_str)
    
    try:
        parsed = json.loads(fixed_str)
        return {
            "success": True,
            "action": "compress_json",
            "data": {
                "status": "fixed",
                "fixes": fixes,
                "compressed": json.dumps(parsed, separators=(',', ':'), ensure_ascii=False),
            },
            "elapsed": time.time() - _start,
        }
    except json.JSONDecodeError as e:
        # 使用修复后的字符串构建错误上下文，因为错误位置是基于修复后的字符串
        ctx = _build_error_context(fixed_str, e)
        return {
            "success": False,
            "action": "compress_json",
            "error": f"JSON 解析失败: {e.msg}",
            "data": {**ctx, "attempted_fixes": fixes or "无"},
            "elapsed": time.time() - _start,
        }
