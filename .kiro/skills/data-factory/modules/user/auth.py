# -*- coding: utf-8 -*-
"""
用户认证模块
支持：注册新用户、登录
"""

import time
from typing import Optional

from core.http_client import HttpClient
from core.auth import login, register, register_ca
from core.db import DbClient
from core.types import ActionResult, Environment
from core.exceptions import UserLoginError, UserRegisterError
from validators.user_validator import validate_register
from config import VALIDATION_WAIT


def action_register(
    client: HttpClient,
    db: DbClient,
    env: Environment,
    email: Optional[str] = None,
    pwd: str = "111111"
) -> ActionResult:
    """
    注册新用户
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境 (UAT/GQC/DEV)
        email: 邮箱，不传则自动生成
        pwd: 密码，默认 111111
    
    Returns:
        ActionResult: 包含 email/pwd/user_id/token
    """
    start = time.time()
    try:
        result = register(client, email, pwd, db=db, env=env)
        time.sleep(VALIDATION_WAIT)
        validation = validate_register(db, result["email"])
        return {
            "success": validation["passed"],
            "env": env,
            "action": "register",
            "data": {
                "email": result["email"],
                "pwd": result["pwd"],
                "user_id": result.get("uid", ""),
                "token": result["token"],
            },
            "validation": validation,
            "elapsed": time.time() - start,
        }
    except UserRegisterError as e:
        return {
            "success": False, "env": env, "action": "register",
            "data": {}, "error": str(e), "elapsed": time.time() - start,
        }
    except Exception as e:
        return {
            "success": False, "env": env, "action": "register",
            "data": {}, "error": str(e), "elapsed": time.time() - start,
        }


def action_register_ca(
    client: HttpClient,
    db: DbClient,
    env: Environment,
    email: Optional[str] = None,
    pwd: str = "111111",
    phone: Optional[str] = None,
) -> ActionResult:
    """
    注册 CA 站新用户（含手机验证）
    
    Args:
        client: HTTP 客户端
        db: 数据库客户端
        env: 环境 (UAT/GQC/DEV)
        email: 邮箱，不传则自动生成
        pwd: 密码，默认 111111
        phone: 手机号，不传则随机生成 +1-05XXXXXXXX
    
    Returns:
        ActionResult: 包含 email/pwd/user_id/token/phone
    """
    start = time.time()
    try:
        result = register_ca(client, email, pwd, phone, db=db, env=env)
        time.sleep(VALIDATION_WAIT)
        validation = validate_register(db, result["email"])
        return {
            "success": validation["passed"],
            "env": env,
            "action": "register_ca",
            "data": {
                "email": result["email"],
                "pwd": result["pwd"],
                "user_id": result.get("uid", ""),
                "token": result["token"],
                "phone": result["phone"],
            },
            "validation": validation,
            "elapsed": time.time() - start,
        }
    except UserRegisterError as e:
        return {
            "success": False, "env": env, "action": "register_ca",
            "data": {}, "error": str(e), "elapsed": time.time() - start,
        }
    except Exception as e:
        return {
            "success": False, "env": env, "action": "register_ca",
            "data": {}, "error": str(e), "elapsed": time.time() - start,
        }


def action_login(
    client: HttpClient,
    env: Environment,
    email: str,
    pwd: str
) -> ActionResult:
    """
    登录获取 token
    
    Args:
        client: HTTP 客户端
        env: 环境
        email: 用户邮箱
        pwd: 密码
    
    Returns:
        ActionResult: 包含 email/token
    """
    start = time.time()
    try:
        token = login(client, email, pwd)
        return {
            "success": True,
            "env": env,
            "action": "login",
            "data": {"email": email, "token": token},
            "validation": {"passed": True, "checks": [], "failed_checks": [], "suggestion": ""},
            "elapsed": time.time() - start,
        }
    except UserLoginError as e:
        return {
            "success": False, "env": env, "action": "login",
            "data": {"email": email}, "error": str(e), "elapsed": time.time() - start,
        }
    except Exception as e:
        return {
            "success": False, "env": env, "action": "login",
            "data": {}, "error": str(e), "elapsed": time.time() - start,
        }
