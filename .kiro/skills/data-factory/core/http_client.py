# -*- coding: utf-8 -*-
"""
HTTP 客户端封装。

统一处理请求头、token、错误响应，支持前台（ec）和后台（central）两套 API。
内置网络错误重试机制，自动处理临时性网络抖动。

Example:
    client = HttpClient(ec_base, central_base, token)
    status, resp = client.post("/path", body)
    if client.is_success(status, resp):
        data = resp["body"]
"""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, Optional, Tuple, Union

from config import REQUEST_TIMEOUT
from core.retry import retry_on_network_error


class HttpClient:
    """
    HTTP 客户端，支持前台和后台两套 base_url。
    
    Attributes:
        ec_base: 前台 API 基础 URL（如 https://uat-ecapi.yamibuy.tech）。
        central_base: 后台 API 基础 URL（如 https://uat-centralapi.yamibuy.tech）。
        token: 当前用户 token，会自动添加到请求头。
    """

    def __init__(self, ec_base: str, central_base: str, token: Optional[str] = None) -> None:
        """
        初始化 HTTP 客户端。
        
        Args:
            ec_base: 前台 API 基础 URL。
            central_base: 后台 API 基础 URL。
            token: 用户 token，可选。
        """
        self.ec_base: str = ec_base
        self.central_base: str = central_base
        self.token: Optional[str] = token

    @retry_on_network_error(max_retries=3, backoff_factor=0.5)
    def _request(
        self, 
        method: str, 
        url: str, 
        body: Optional[Union[Dict[str, Any], bytes]] = None, 
        extra_headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        content_type: str = "application/json"
    ) -> Tuple[int, Dict[str, Any]]:
        """
        发送 HTTP 请求（带自动重试）。
        
        网络错误（status=0）或服务端临时错误（502/503/504）时自动重试，
        最多重试 3 次，使用指数退避策略。
        
        Args:
            method: HTTP 方法（GET/POST/PUT/DELETE）。
            url: 完整请求 URL。
            body: 请求体，可以是字典或字节。
            extra_headers: 额外请求头，会合并到默认请求头。
            timeout: 超时时间（秒），默认使用 REQUEST_TIMEOUT。
            content_type: Content-Type 头，默认 application/json。
        
        Returns:
            元组 (status_code, response_dict)，网络错误时 status_code 为 0。
        """
        headers = {
            "Content-Type": content_type,
            "y_language": "zh_CN",
        }
        if self.token:
            headers["token"] = self.token
        if extra_headers:
            headers.update(extra_headers)

        # 处理请求体
        if body is not None:
            if isinstance(body, bytes):
                data = body
            elif content_type == "application/json":
                data = json.dumps(body).encode("utf-8")
            else:
                data = body if isinstance(body, bytes) else str(body).encode("utf-8")
        else:
            data = None
            
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        actual_timeout = timeout if timeout is not None else REQUEST_TIMEOUT

        try:
            with urllib.request.urlopen(req, timeout=actual_timeout) as resp:
                raw = resp.read().decode("utf-8")
                try:
                    return resp.status, json.loads(raw)
                except json.JSONDecodeError:
                    return resp.status, {"body": raw}
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8")
            try:
                return e.code, json.loads(raw)
            except (json.JSONDecodeError, Exception):
                return e.code, {"error": raw}
        except urllib.error.URLError as e:
            return 0, {"error": f"网络错误: {e.reason}"}
        except Exception as e:
            return 0, {"error": str(e)}

    def get(
        self, 
        path: str, 
        use_central: bool = False, 
        extra_headers: Optional[Dict[str, str]] = None, 
        service: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        发送 GET 请求。
        
        Args:
            path: API 路径（如 /ec-customer/users/get_token）。
            use_central: 是否使用后台 API，默认 False 使用前台。
            extra_headers: 额外请求头。
            service: 服务前缀，会拼接到 path 前面。
            timeout: 超时时间（秒）。
        
        Returns:
            元组 (status_code, response_dict)。
        """
        base = self.central_base if use_central else self.ec_base
        if service:
            path = f"/{service}{path}"
        return self._request("GET", base + path, extra_headers=extra_headers, timeout=timeout)

    def post(
        self, 
        path: str, 
        body: Optional[Dict[str, Any]] = None, 
        use_central: bool = False, 
        extra_headers: Optional[Dict[str, str]] = None, 
        service: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        发送 POST 请求。
        
        Args:
            path: API 路径。
            body: 请求体字典。
            use_central: 是否使用后台 API。
            extra_headers: 额外请求头。
            service: 服务前缀。
            timeout: 超时时间（秒）。
        
        Returns:
            元组 (status_code, response_dict)。
        """
        base = self.central_base if use_central else self.ec_base
        if service:
            path = f"/{service}{path}"
        return self._request("POST", base + path, body=body, extra_headers=extra_headers, timeout=timeout)

    def put(
        self, 
        path: str, 
        body: Optional[Dict[str, Any]] = None, 
        use_central: bool = False, 
        extra_headers: Optional[Dict[str, str]] = None, 
        service: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        发送 PUT 请求。
        
        Args:
            path: API 路径。
            body: 请求体字典。
            use_central: 是否使用后台 API。
            extra_headers: 额外请求头。
            service: 服务前缀。
            timeout: 超时时间（秒）。
        
        Returns:
            元组 (status_code, response_dict)。
        """
        base = self.central_base if use_central else self.ec_base
        if service:
            path = f"/{service}{path}"
        return self._request("PUT", base + path, body=body, extra_headers=extra_headers, timeout=timeout)

    def delete(
        self, 
        path: str, 
        body: Optional[Dict[str, Any]] = None, 
        use_central: bool = False, 
        extra_headers: Optional[Dict[str, str]] = None, 
        service: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        发送 DELETE 请求。
        
        Args:
            path: API 路径。
            body: 请求体字典。
            use_central: 是否使用后台 API。
            extra_headers: 额外请求头。
            service: 服务前缀。
            timeout: 超时时间（秒）。
        
        Returns:
            元组 (status_code, response_dict)。
        """
        base = self.central_base if use_central else self.ec_base
        if service:
            path = f"/{service}{path}"
        return self._request("DELETE", base + path, body=body, extra_headers=extra_headers, timeout=timeout)

    def post_raw(
        self,
        url: str,
        body: Union[Dict[str, Any], bytes, str],
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        content_type: str = "application/json"
    ) -> Tuple[int, Dict[str, Any]]:
        """
        发送原始 POST 请求到任意 URL。
        
        用于调用外部 API（如 Stripe），不会自动添加 token。
        
        Args:
            url: 完整请求 URL。
            body: 请求体，可以是字典、字节或字符串。
            headers: 请求头（不会自动添加 token）。
            timeout: 超时时间（秒）。
            content_type: Content-Type 头。
        
        Returns:
            元组 (status_code, response_dict)。
        """
        actual_headers = {"Content-Type": content_type}
        if headers:
            actual_headers.update(headers)
        
        # 处理请求体
        if isinstance(body, bytes):
            data = body
        elif isinstance(body, dict) and content_type == "application/json":
            data = json.dumps(body).encode("utf-8")
        elif isinstance(body, str):
            data = body.encode("utf-8")
        else:
            data = str(body).encode("utf-8")
        
        req = urllib.request.Request(url, data=data, headers=actual_headers, method="POST")
        actual_timeout = timeout if timeout is not None else REQUEST_TIMEOUT
        
        try:
            with urllib.request.urlopen(req, timeout=actual_timeout) as resp:
                raw = resp.read().decode("utf-8")
                try:
                    return resp.status, json.loads(raw)
                except json.JSONDecodeError:
                    return resp.status, {"body": raw}
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8")
            try:
                return e.code, json.loads(raw)
            except (json.JSONDecodeError, Exception):
                return e.code, {"error": raw}
        except urllib.error.URLError as e:
            return 0, {"error": f"网络错误: {e.reason}"}
        except Exception as e:
            return 0, {"error": str(e)}

    def post_central(
        self,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        hub_token: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        发送 POST 请求到 central 后台。
        
        常用于 mkt、customer 等后台服务。
        
        Args:
            path: API 路径。
            body: 请求体字典。
            hub_token: Hub admin token，如果提供则使用，否则使用 self.token。
            timeout: 超时时间（秒）。
        
        Returns:
            元组 (status_code, response_dict)。
        """
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if hub_token:
            headers["token"] = hub_token
        elif self.token:
            headers["token"] = self.token
        
        url = self.central_base + path
        return self._request("POST", url, body=body, extra_headers=headers, timeout=timeout)

    def is_success(self, status: int, resp: Dict[str, Any]) -> bool:
        """
        判断接口响应是否成功。
        
        Args:
            status: HTTP 状态码。
            resp: 响应字典。
        
        Returns:
            True 表示成功（status=200 且 messageId 为 200 或 10000）。
        """
        return status == 200 and resp.get("messageId") in ("200", "10000")

    def get_error(self, resp: Dict[str, Any]) -> str:
        """
        从响应中提取错误信息。
        
        Args:
            resp: 响应字典。
        
        Returns:
            错误信息字符串，优先返回 zhError，其次 message、error。
        """
        return (
            resp.get("zhError")
            or resp.get("message")
            or resp.get("error")
            or str(resp)[:120]
        )
