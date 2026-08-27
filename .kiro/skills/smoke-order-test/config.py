# -*- coding: utf-8 -*-
"""
环境配置
"""

# ==================== 环境选择 ====================
ENV = "UAT"  # UAT / GQC / DEV

ENV_CONFIG = {
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

# ==================== 测试账号（按环境配置） ====================
# 运行时可通过 --email / --pwd 参数覆盖
ENV_ACCOUNT = {
    "UAT": {"email": "renee01@yamibuy.com", "pwd": "111111"},
    "GQC": {"email": "renee01@yamibuy.com", "pwd": "111111"},
    "DEV": {"email": "renee01@yamibuy.com", "pwd": "111111"},
}

# 当前环境账号（运行时由脚本根据 ENV 自动选择，可被命令行参数覆盖）
TEST_ACCOUNT = ENV_ACCOUNT[ENV]

# ==================== 支付配置 ====================
# 冒烟测试使用 Stripe 测试卡（4242）
# enroll 接口的 billing zipcode，与测试卡绑定地址一致
PAYMENT_CONFIG = {
    "zip": "91789",
}

# Stripe publishable key（UAT/GQC 共用同一个测试 key）
STRIPE_PUBLISHABLE_KEY = "pk_test_51Lzo0KA1KmcXQec8x6pOMeHMdRGaU04mRPTrTB13LeGpOfbKFWY8GB97Tb8A0IIwNnOfUTbOSY12RJjGBhdMJetJ00sfkkZOMI"

# ==================== 请求超时 ====================
REQUEST_TIMEOUT = 30  # 秒
