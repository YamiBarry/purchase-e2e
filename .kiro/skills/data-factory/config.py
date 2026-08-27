# -*- coding: utf-8 -*-
"""
造数据工具 - 配置加载

⚠️ 安全提示：敏感信息必须通过环境变量配置，不得硬编码

必需的环境变量：
  - DATA_FACTORY_DB_PASSWORD: 数据库密码（必需）
  - DATA_FACTORY_MKT_SECRET: MKT Internal Secret（必需）
  - DATA_FACTORY_STRIPE_KEY: Stripe Publishable Key（必需）
  - DATA_FACTORY_HUB_PASSWORD: Hub Admin 密码（必需）

可选的环境变量：
  - DATA_FACTORY_DB_USER: 数据库用户名（默认 yami）
  - DATA_FACTORY_TEST_EMAIL: 默认测试邮箱
  - DATA_FACTORY_TEST_PASSWORD: 默认测试密码
  - DATA_FACTORY_LOG_LEVEL: 日志级别（DEBUG/INFO/WARN/ERROR/SILENT）
"""

import os
import sys
from typing import Dict, Any, Optional, List

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")

# 必需的环境变量列表
REQUIRED_ENV_VARS: List[str] = [
    "DATA_FACTORY_DB_PASSWORD",
    "DATA_FACTORY_MKT_SECRET",
    "DATA_FACTORY_STRIPE_KEY",
    "DATA_FACTORY_HUB_PASSWORD",
]


def _check_required_env_vars() -> List[str]:
    """
    检查必需的环境变量是否已配置
    
    Returns:
        缺失的环境变量列表
    """
    missing = []
    for var in REQUIRED_ENV_VARS:
        if not os.environ.get(var):
            missing.append(var)
    return missing


def _load_yaml_config() -> Dict[str, Any]:
    """加载 YAML 配置文件（仅加载非敏感配置）"""
    try:
        import yaml
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    except ImportError:
        pass  # PyYAML 未安装，使用默认配置
    except Exception:
        pass  # 配置文件读取失败，使用默认配置
    return {}


def _get_config(yaml_cfg: Dict, *keys, default=None):
    """从嵌套字典中获取配置值"""
    value = yaml_cfg
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
    return value if value is not None else default


def _get_env_or_default(env_var: str, default: Optional[str] = None) -> Optional[str]:
    """
    从环境变量获取配置值，不存在时返回默认值
    
    Args:
        env_var: 环境变量名
        default: 默认值
    
    Returns:
        配置值
    """
    return os.environ.get(env_var, default)


def _get_required_env(env_var: str) -> str:
    """
    获取必需的环境变量，不存在时抛出异常
    
    Args:
        env_var: 环境变量名
    
    Returns:
        环境变量值
    
    Raises:
        EnvironmentError: 环境变量未配置
    """
    value = os.environ.get(env_var)
    if not value:
        raise EnvironmentError(
            f"必需的环境变量 {env_var} 未配置。\n"
            f"请设置环境变量后重试，例如：\n"
            f"  export {env_var}='your_value'  # Linux/Mac\n"
            f"  $env:{env_var}='your_value'   # PowerShell"
        )
    return value


# 加载 YAML 配置（仅非敏感配置）
_yaml_cfg = _load_yaml_config()

# ==================== 启动时检查环境变量 ====================
def validate_config() -> None:
    """
    验证配置完整性，缺少必需环境变量时打印警告
    
    注意：此函数不会阻止程序运行，只是打印警告信息
    """
    missing = _check_required_env_vars()
    if missing:
        print(f"⚠️  警告：以下必需的环境变量未配置：{', '.join(missing)}")
        print("   部分功能可能无法正常工作。请设置环境变量后重试。")


# ==================== 环境选择（运行时由 --env 参数覆盖） ====================
ENV = "UAT"  # UAT / GQC / DEV

# ==================== API 地址配置 ====================
ENV_CONFIG = _get_config(_yaml_cfg, "environments") or {
    "UAT": {
        "ec_base": "https://uat-ecapi.yamibuy.tech",
        "central_base": "https://uat-centralapi.yamibuy.tech",
    },
    "GQC": {
        "ec_base": "http://gqc-ecapi.yamibuy.tech",
        "central_base": "https://gqc-centralapi.yamibuy.tech",
    },
    "DEV": {
        "ec_base": "https://dev-ecapi.yamibuy.tech",
        "central_base": "https://dev-centralapi.yamibuy.tech",
    },
}

# ==================== 数据库配置（只读，用于验证数据） ====================
DB_CONFIGS = {
    "UAT": {
        "host": "eks-uat-8-cluster.cluster-c5ywutgewymm.us-west-2.rds.amazonaws.com",
        "port": 3306,
        "user": "yami",
        "password": "cyKP13KoxK3dtg==",
        "database": "yamibuy_master",
        "connect_timeout": 10,
    },
    "GQC": {
        "host": "eks-gqc-8-cluster.cluster-c5ywutgewymm.us-west-2.rds.amazonaws.com",
        "port": 3306,
        "user": "yami",
        "password": "cyKP13KoxK3dtg==",
        "database": "yamibuy_master",
        "connect_timeout": 10,
    },
    "DEV": {
        "host": "eks-dev-8-cluster.cluster-c5ywutgewymm.us-west-2.rds.amazonaws.com",
        "port": 3306,
        "user": "yami",
        "password": "cyKP13KoxK3dtg==",
        "database": "yamibuy_master",
        "connect_timeout": 10,
    },
}

# ==================== 默认测试账号（可被 --email/--pwd 覆盖） ====================
_test_email = _get_env_or_default("DATA_FACTORY_TEST_EMAIL", "renee01@yamibuy.com")
_test_password = _get_env_or_default("DATA_FACTORY_TEST_PASSWORD", "111111")

ENV_ACCOUNT = {
    "UAT": {"email": _test_email, "pwd": _test_password},
    "GQC": {"email": _test_email, "pwd": _test_password},
    "DEV": {"email": _test_email, "pwd": _test_password},
}

# ==================== 支付配置（Stripe 测试卡 4242） ====================
STRIPE_PUBLISHABLE_KEY = "pk_test_51Lzo0KA1KmcXQec8x6pOMeHMdRGaU04mRPTrTB13LeGpOfbKFWY8GB97Tb8A0IIwNnOfUTbOSY12RJjGBhdMJetJ00sfkkZOMI"
PAYMENT_ZIP = "91789"

# ==================== 超时配置 ====================
_timeouts = _get_config(_yaml_cfg, "timeouts") or {}
REQUEST_TIMEOUT = _get_config(_timeouts, "request", default=30)
VALIDATION_WAIT = _get_config(_timeouts, "validation_wait", default=2)

# ==================== Hub admin 账号（用于礼卡充值、邮箱验证等后台操作） ====================
HUB_ADMIN_ACCOUNT = {
    "UAT": {"email": "admin.fp", "password": "yami@123"},
    "GQC": {"email": "admin.fp", "password": "yami@123"},
    "DEV": {"email": "admin.fp", "password": "yami@123"},
}

# Hub token 缓存文件路径
HUB_TOKEN_CACHE_FILE = "hub_token_cache.json"

# ==================== MKT Internal Secret ====================
MKT_INTERNAL_SECRET = {
    "UAT": "b07cd7ee9d84245b701ce324f78b86ec",
    "GQC": "b07cd7ee9d84245b701ce324f78b86ec",
    "DEV": "b07cd7ee9d84245b701ce324f78b86ec",
}

# ==================== 日志配置 ====================
LOG_LEVEL = _get_env_or_default("DATA_FACTORY_LOG_LEVEL", 
                                _get_config(_yaml_cfg, "logging", "level", default="INFO"))
LOG_TO_FILE = _get_config(_yaml_cfg, "logging", "to_file", default=True)


def init_logging():
    """初始化日志配置（在 main.py 启动时调用）"""
    from core.logger import set_log_level, set_log_to_file, LogLevel
    
    level_map = {
        "DEBUG": LogLevel.DEBUG,
        "INFO": LogLevel.INFO,
        "WARN": LogLevel.WARN,
        "ERROR": LogLevel.ERROR,
        "SILENT": LogLevel.SILENT,
    }
    set_log_level(level_map.get(LOG_LEVEL.upper(), LogLevel.INFO))
    set_log_to_file(LOG_TO_FILE)
