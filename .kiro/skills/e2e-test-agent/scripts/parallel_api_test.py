#!/usr/bin/env python3
"""
并行接口测试执行器

从测试用例中提取接口测试用例，并行执行 HTTP 请求验证。
供 LLM 通过 shell 调用。

使用方式:
    # 执行接口测试（从用例文件读取）
    python scripts/parallel_api_test.py --op OP-123456 --env UAT \
        --cases-file docs/recordings/OP-123456/api_test_cases.json \
        --concurrency 5

    # 执行接口测试（从 pipeline-context 读取配置）
    python scripts/parallel_api_test.py --op OP-123456 --env UAT \
        --cases-file docs/recordings/OP-123456/api_test_cases.json

输入文件格式 (api_test_cases.json):
[
  {
    "case_number": "API_ADDRESS_001",
    "case_name": "获取地址列表",
    "method": "GET",
    "url": "/api/v2/customer/address/list",
    "headers": {"Authorization": "Bearer {token}"},
    "params": {},
    "body": null,
    "expected_status": 200,
    "expected_body": {"code": 0},
    "assertions": [
      {"path": "$.code", "operator": "eq", "value": 0},
      {"path": "$.data", "operator": "not_null"}
    ]
  }
]

输出文件: docs/recordings/{op_number}/api_test_results.json
"""

import argparse
import json
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


# 环境 Base URL 映射
ENV_BASE_URLS = {
    "UAT": "https://uat-ec-api.yamibuy.com",
    "GQC": "https://gqc-ec-api.yamibuy.com",
    "DEV": "https://dev-ec-api.yamibuy.com",
}

# 请求超时（秒）
REQUEST_TIMEOUT = 30


def execute_single_case(case: Dict[str, Any], base_url: str, token: str = "") -> Dict[str, Any]:
    """
    执行单个接口测试用例

    Args:
        case: 测试用例
        base_url: 环境 Base URL
        token: 认证 token

    Returns:
        测试结果
    """
    case_number = case.get("case_number", "UNKNOWN")
    case_name = case.get("case_name", "")
    method = case.get("method", "GET").upper()
    url = case.get("url", "")
    headers = case.get("headers", {})
    params = case.get("params", {})
    body = case.get("body")
    expected_status = case.get("expected_status", 200)
    assertions = case.get("assertions", [])

    # 拼接完整 URL
    full_url = f"{base_url}{url}" if url.startswith("/") else url

    # 替换 token 占位符
    if token:
        for key, value in headers.items():
            if isinstance(value, str) and "{token}" in value:
                headers[key] = value.replace("{token}", token)

    result = {
        "case_number": case_number,
        "case_name": case_name,
        "method": method,
        "url": full_url,
        "status": "fail",
        "error": "",
        "response_status": None,
        "response_time_ms": 0,
        "assertions_passed": 0,
        "assertions_total": len(assertions),
        "timestamp": datetime.now().isoformat()
    }

    try:
        start_time = time.time()

        # 发送请求
        response = requests.request(
            method=method,
            url=full_url,
            headers=headers,
            params=params,
            json=body if body and method in ("POST", "PUT", "PATCH") else None,
            timeout=REQUEST_TIMEOUT
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        result["response_time_ms"] = elapsed_ms
        result["response_status"] = response.status_code

        # 检查状态码
        if response.status_code != expected_status:
            result["error"] = f"状态码不匹配: 期望 {expected_status}, 实际 {response.status_code}"
            return result

        # 解析响应体
        try:
            response_body = response.json()
        except ValueError:
            response_body = response.text

        # 执行断言
        passed = 0
        failed_assertions = []

        for assertion in assertions:
            path = assertion.get("path", "")
            operator = assertion.get("operator", "eq")
            expected = assertion.get("value")

            actual = _extract_json_path(response_body, path)
            assertion_result = _check_assertion(actual, operator, expected)

            if assertion_result:
                passed += 1
            else:
                failed_assertions.append({
                    "path": path,
                    "operator": operator,
                    "expected": expected,
                    "actual": actual
                })

        result["assertions_passed"] = passed

        if failed_assertions:
            result["error"] = f"断言失败: {json.dumps(failed_assertions, ensure_ascii=False)}"
        else:
            result["status"] = "pass"

    except requests.Timeout:
        result["error"] = f"请求超时 ({REQUEST_TIMEOUT}s)"
    except requests.ConnectionError:
        result["error"] = f"连接失败: {full_url}"
    except Exception as e:
        result["error"] = f"执行异常: {str(e)}"

    return result


def _extract_json_path(data: Any, path: str) -> Any:
    """
    简单的 JSON Path 提取（支持 $.field.subfield 格式）

    Args:
        data: JSON 数据
        path: JSON Path（如 $.code, $.data.list[0].id）

    Returns:
        提取的值
    """
    if not path or path == "$":
        return data

    # 去掉 $. 前缀
    path = path.lstrip("$").lstrip(".")

    parts = path.split(".")
    current = data

    for part in parts:
        if current is None:
            return None

        # 处理数组索引 field[0]
        if "[" in part:
            field = part[:part.index("[")]
            index = int(part[part.index("[") + 1:part.index("]")])
            if isinstance(current, dict):
                current = current.get(field)
            if isinstance(current, list) and index < len(current):
                current = current[index]
            else:
                return None
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None

    return current


def _check_assertion(actual: Any, operator: str, expected: Any) -> bool:
    """
    检查断言

    Args:
        actual: 实际值
        operator: 操作符
        expected: 期望值

    Returns:
        是否通过
    """
    if operator == "eq":
        return actual == expected
    elif operator == "ne":
        return actual != expected
    elif operator == "gt":
        return actual is not None and actual > expected
    elif operator == "gte":
        return actual is not None and actual >= expected
    elif operator == "lt":
        return actual is not None and actual < expected
    elif operator == "lte":
        return actual is not None and actual <= expected
    elif operator == "not_null":
        return actual is not None
    elif operator == "is_null":
        return actual is None
    elif operator == "contains":
        return expected in str(actual) if actual else False
    elif operator == "not_contains":
        return expected not in str(actual) if actual else True
    elif operator == "in":
        return actual in expected if isinstance(expected, list) else False
    elif operator == "type":
        type_map = {"string": str, "int": int, "float": float, "list": list, "dict": dict, "bool": bool}
        return isinstance(actual, type_map.get(expected, object))
    else:
        return False


def run_parallel_tests(
    cases: List[Dict[str, Any]],
    base_url: str,
    token: str = "",
    concurrency: int = 5
) -> List[Dict[str, Any]]:
    """
    并行执行接口测试

    Args:
        cases: 测试用例列表
        base_url: 环境 Base URL
        token: 认证 token
        concurrency: 并发数

    Returns:
        测试结果列表
    """
    results = []

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_case = {
            executor.submit(execute_single_case, case, base_url, token): case
            for case in cases
        }

        for future in as_completed(future_to_case):
            case = future_to_case[future]
            try:
                result = future.result()
                results.append(result)
                status_icon = "✅" if result["status"] == "pass" else "❌"
                print(f"  {status_icon} {result['case_number']} - {result['case_name']} ({result['response_time_ms']}ms)",
                      file=sys.stderr)
            except Exception as e:
                results.append({
                    "case_number": case.get("case_number", "UNKNOWN"),
                    "case_name": case.get("case_name", ""),
                    "status": "fail",
                    "error": f"执行器异常: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })

    return results


def main():
    parser = argparse.ArgumentParser(description='并行接口测试执行器')
    parser.add_argument('--op', required=True, help='OP 编号')
    parser.add_argument('--env', default='UAT', choices=['UAT', 'GQC', 'DEV'], help='测试环境')
    parser.add_argument('--cases-file', required=True, help='测试用例 JSON 文件路径')
    parser.add_argument('--token', default='', help='认证 token')
    parser.add_argument('--token-file', help='token 文件路径（优先于 --token）')
    parser.add_argument('--concurrency', type=int, default=5, help='并发数（默认 5）')
    parser.add_argument('--base-url', help='自定义 Base URL（覆盖环境默认值）')
    parser.add_argument('--output', help='结果输出文件路径')

    args = parser.parse_args()

    # 读取用例
    cases_path = Path(args.cases_file)
    if not cases_path.exists():
        print(json.dumps({"error": f"用例文件不存在: {args.cases_file}"}), file=sys.stderr)
        sys.exit(1)

    with open(cases_path, 'r', encoding='utf-8') as f:
        cases = json.load(f)

    if not cases:
        print(json.dumps({"success": True, "total": 0, "passed": 0, "failed": 0, "message": "无测试用例"}))
        return

    # 确定 Base URL
    base_url = args.base_url or ENV_BASE_URLS.get(args.env, ENV_BASE_URLS["UAT"])

    # 读取 token
    token = args.token
    if args.token_file:
        token_path = Path(args.token_file)
        if token_path.exists():
            token = token_path.read_text(encoding='utf-8').strip()

    # 执行测试
    print(f"开始执行接口测试: {len(cases)} 个用例, 并发数 {args.concurrency}, 环境 {args.env}", file=sys.stderr)
    print(f"Base URL: {base_url}", file=sys.stderr)
    print("-" * 60, file=sys.stderr)

    start_time = time.time()
    results = run_parallel_tests(cases, base_url, token, args.concurrency)
    elapsed = time.time() - start_time

    # 统计
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = total - passed

    print("-" * 60, file=sys.stderr)
    print(f"完成: 总计 {total}, 通过 {passed}, 失败 {failed}, 耗时 {elapsed:.1f}s", file=sys.stderr)

    # 输出结果
    output_data = {
        "success": True,
        "op_number": args.op,
        "env": args.env,
        "total": total,
        "passed": passed,
        "failed": failed,
        "elapsed_seconds": round(elapsed, 1),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

    # 保存到文件
    output_path = args.output or f"docs/recordings/{args.op}/api_test_results.json"
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    # 输出摘要到 stdout
    summary = {
        "success": failed == 0,
        "total": total,
        "passed": passed,
        "failed": failed,
        "elapsed_seconds": round(elapsed, 1),
        "results_file": str(output_file),
        "failed_cases": [r for r in results if r["status"] == "fail"]
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
