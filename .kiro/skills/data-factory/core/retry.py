# -*- coding: utf-8 -*-
"""
HTTP 请求重试机制模块。

提供指数退避重试装饰器，用于处理网络抖动导致的临时失败。

Example:
    from core.retry import retry_on_network_error
    
    @retry_on_network_error(max_retries=3, backoff_factor=0.5)
    def make_request():
        # 网络请求逻辑
        pass
"""

import time
from functools import wraps
from typing import Any, Callable, Dict, Tuple, TypeVar

from core.logger import debug, warn

# 泛型类型变量
F = TypeVar("F", bound=Callable[..., Tuple[int, Dict[str, Any]]])


def retry_on_network_error(
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    retry_on_status: Tuple[int, ...] = (0, 502, 503, 504)
) -> Callable[[F], F]:
    """
    网络错误重试装饰器，使用指数退避策略。
    
    当请求返回指定的错误状态码时，自动重试。
    重试间隔按指数增长：backoff_factor * (2 ** attempt)
    
    Args:
        max_retries: 最大重试次数，默认 3
        backoff_factor: 退避因子，默认 0.5 秒
        retry_on_status: 需要重试的状态码元组，默认 (0, 502, 503, 504)
            - 0: 网络错误（连接失败、超时等）
            - 502/503/504: 服务端临时错误
    
    Returns:
        装饰器函数
    
    Example:
        @retry_on_network_error(max_retries=3)
        def _request(self, method, url, body=None):
            # 原有请求逻辑
            pass
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Tuple[int, Dict[str, Any]]:
            last_error = None
            last_status = 0
            last_resp: Dict[str, Any] = {}
            
            for attempt in range(max_retries):
                status, resp = func(*args, **kwargs)
                
                # 成功或不需要重试的状态码，直接返回
                if status not in retry_on_status:
                    return status, resp
                
                # 记录最后一次错误
                last_status = status
                last_resp = resp
                last_error = resp.get("error", f"HTTP {status}")
                
                # 如果还有重试机会，等待后重试
                if attempt < max_retries - 1:
                    sleep_time = backoff_factor * (2 ** attempt)
                    warn(f"请求失败 (status={status})，{sleep_time:.1f}s 后重试 ({attempt + 1}/{max_retries})")
                    time.sleep(sleep_time)
            
            # 所有重试都失败
            warn(f"重试 {max_retries} 次后仍失败: {last_error}")
            return last_status, {
                **last_resp,
                "retry_exhausted": True,
                "retry_count": max_retries,
            }
        
        return wrapper  # type: ignore
    return decorator


def retry_on_exception(
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    exceptions: Tuple[type, ...] = (Exception,)
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    异常重试装饰器，用于非 HTTP 请求场景。
    
    当函数抛出指定异常时，自动重试。
    
    Args:
        max_retries: 最大重试次数
        backoff_factor: 退避因子
        exceptions: 需要重试的异常类型元组
    
    Returns:
        装饰器函数
    
    Example:
        @retry_on_exception(max_retries=3, exceptions=(ConnectionError, TimeoutError))
        def connect_to_db():
            # 数据库连接逻辑
            pass
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        sleep_time = backoff_factor * (2 ** attempt)
                        debug(f"异常 {type(e).__name__}，{sleep_time:.1f}s 后重试 ({attempt + 1}/{max_retries})")
                        time.sleep(sleep_time)
            
            # 所有重试都失败，抛出最后一个异常
            raise last_exception  # type: ignore
        
        return wrapper
    return decorator
