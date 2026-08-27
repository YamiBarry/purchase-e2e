"""
禅道 API 客户端
封装认证、请求、图片上传等通用逻辑
"""
import os
import re
import json
import time
import base64
import tempfile
from typing import List, Dict, Any, Optional, Tuple
import httpx

# 禅道配置（从环境变量读取，支持 deploy.sh 注入）
# 兼容两种变量名：ZENTAO_URL/ZENTAO_BASE_URL, ZENTAO_USERNAME/ZENTAO_ACCOUNT
ZENTAO_BASE_URL = os.environ.get("ZENTAO_BASE_URL", os.environ.get("ZENTAO_URL", "https://bugs.yamibuy.tech"))
ZENTAO_ACCOUNT = os.environ.get("ZENTAO_ACCOUNT", os.environ.get("ZENTAO_USERNAME", "renee_zhang"))
ZENTAO_PASSWORD = os.environ.get("ZENTAO_PASSWORD", "Yamibuy@123")

# 业务常量
PURCHASE_PRODUCT_ID = 11
CANADA_WAREHOUSE_PRODUCT_ID = 21  # 加拿大仓 6.15
CANADA_WAREHOUSE_728_PRODUCT_ID = 22  # 加拿大仓 7.28
DEFAULT_BUILD = "trunk"

# OP 号 → 产品 ID 路由规则
OP_PRODUCT_ROUTING = {
    "OP-34696": CANADA_WAREHOUSE_PRODUCT_ID,
    "OP-36037": CANADA_WAREHOUSE_PRODUCT_ID,
    "OP-36840": CANADA_WAREHOUSE_PRODUCT_ID,
    "OP-36993": CANADA_WAREHOUSE_PRODUCT_ID,
    "OP-37140": CANADA_WAREHOUSE_PRODUCT_ID,
}


def get_product_id_by_op(op_number: str) -> int:
    """根据 OP 号返回对应的产品 ID，无 OP 时默认返回加拿大仓 7.28"""
    if not op_number:
        return CANADA_WAREHOUSE_728_PRODUCT_ID
    # 标准化格式，兼容 "34696" 和 "OP-34696"
    normalized = op_number if op_number.startswith("OP-") else f"OP-{op_number}"
    return OP_PRODUCT_ROUTING.get(normalized, PURCHASE_PRODUCT_ID)

# Bug 类型枚举
BUG_TYPES = {
    "代码错误": "codeerror",
    "设计缺陷": "designdefect",
    "功能缺失": "featurelost",
    "界面优化": "uioptimize",
    "安全相关": "security",
    "性能问题": "performance",
    "其他": "others",
}

# 严重程度枚举（1=致命, 2=严重, 3=一般, 4=轻微）
SEVERITY_MAP = {"致命": 1, "严重": 2, "一般": 3, "轻微": 4, "1": 1, "2": 2, "3": 3, "4": 4}

# 优先级枚举（1=紧急, 2=高, 3=中, 4=低）
PRIORITY_MAP = {"紧急": 1, "高": 2, "中": 3, "低": 4, "1": 1, "2": 2, "3": 3, "4": 4}


class ZentaoClient:
    """禅道 API 客户端"""
    
    def __init__(self):
        self._token: str = ""
        self._token_expire: float = 0.0
        self._browser_sid: str = ""
        self._browser_sid_expire: float = 0.0
    
    def _get_token(self) -> str:
        """登录禅道获取 token，缓存 25 分钟"""
        if self._token and time.time() < self._token_expire:
            return self._token
        
        resp = httpx.post(
            f"{ZENTAO_BASE_URL}/api.php/v1/tokens",
            json={"account": ZENTAO_ACCOUNT, "password": ZENTAO_PASSWORD},
            timeout=10,
        )
        resp.raise_for_status()
        token = resp.json().get("token")
        if not token:
            raise ValueError(f"登录失败: {resp.text}")
        
        self._token = token
        self._token_expire = time.time() + 25 * 60
        return token
    
    def request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """统一的禅道 API 请求封装"""
        token = self._get_token()
        resp = httpx.request(
            method,
            f"{ZENTAO_BASE_URL}{path}",
            headers={"Token": token, "Content-Type": "application/json"},
            timeout=15,
            **kwargs,
        )
        return {"status": resp.status_code, "data": resp.json() if resp.content else {}}
    
    def _get_browser_session(self) -> str:
        """获取浏览器 session，用于图片上传"""
        if self._browser_sid and time.time() < self._browser_sid_expire:
            return self._browser_sid
        
        resp = httpx.get(f"{ZENTAO_BASE_URL}/api-getsessionid.json", timeout=10)
        sid = json.loads(resp.json()["data"])["sessionID"]
        httpx.post(
            f"{ZENTAO_BASE_URL}/user-login.json",
            params={"zentaosid": sid},
            data={"account": ZENTAO_ACCOUNT, "password": ZENTAO_PASSWORD},
            timeout=10,
        )
        self._browser_sid = sid
        self._browser_sid_expire = time.time() + 20 * 60
        return sid
    
    def upload_image(self, image_path: str, bug_id: int) -> str:
        """上传图片到禅道，返回 img 标签"""
        sid = self._get_browser_session()
        with open(image_path, "rb") as f:
            img_data = f.read()
        filename = os.path.basename(image_path)
        resp = httpx.post(
            f"{ZENTAO_BASE_URL}/file-ajaxUpload-{bug_id}.html",
            params={"zentaosid": sid, "dir": "image"},
            files={"imgFile": (filename, img_data)},
            timeout=30,
        )
        result = resp.json() if resp.content else {}
        url = result.get("url", "")
        if url:
            return f'<img src="{url}" />'
        raise ValueError(f"图片上传失败: {result}")


def build_steps_html(steps: str, img_tags: List[str] = None) -> str:
    """构建 steps HTML"""
    # 命令行传入的 \n 是字面量，需先转为真正换行符
    steps_html = steps.replace("\\n", "\n").replace("\n", "<br>")
    if img_tags:
        steps_html += "<br>" + "<br>".join(img_tags)
    return steps_html


def collect_recent_images(used_names: set = None) -> List[Tuple[str, str]]:
    """从企业微信会话图片目录收集未使用过的图片"""
    if used_names is None:
        used_names = set()
    
    images_dir = os.environ.get(
        "WECOM_IMAGES_DIR",
        "",
    )
    # Windows 路径兼容
    if os.name == "nt" and images_dir.startswith("/mnt/"):
        images_dir = images_dir.replace("/mnt/d/", "D:/")
    
    if not os.path.isdir(images_dir):
        return []
    
    files = []
    for fname in os.listdir(images_dir):
        if fname.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            if fname not in used_names:
                fpath = os.path.join(images_dir, fname)
                files.append((os.path.getmtime(fpath), fpath, fname))
    files.sort()
    return [(p, n) for _, p, n in files]


def process_images(
    images_base64: str = "",
    image_paths: str = "",
    image_count: int = 0,
    used_names: set = None
) -> Tuple[List[str], List[str], List[str]]:
    """
    处理图片来源，返回 (paths, used_names, tmp_files)
    优先级：images_base64 > image_paths > image_count
    """
    if used_names is None:
        used_names = set()
    
    paths: List[str] = []
    new_used_names: List[str] = []
    tmp_files: List[str] = []
    
    if images_base64:
        try:
            items = json.loads(images_base64)
            for i, item in enumerate(items):
                b64_data = item.get("data", "")
                mime = item.get("mime", "image/png")
                ext_map = {"image/jpeg": ".jpg", "image/gif": ".gif", "image/webp": ".webp"}
                ext = ext_map.get(mime, ".png")
                img_bytes = base64.b64decode(b64_data)
                tmp_path = os.path.join(tempfile.gettempdir(), f"zentao_img_{i}{ext}")
                with open(tmp_path, "wb") as f:
                    f.write(img_bytes)
                paths.append(tmp_path)
                tmp_files.append(tmp_path)
        except Exception:
            pass
    elif image_paths:
        paths = [p.strip() for p in image_paths.split(",") if p.strip() and os.path.exists(p.strip())]
    elif image_count > 0:
        collected = collect_recent_images(used_names)
        recent = collected[-image_count:]
        paths = [p for p, _ in recent]
        new_used_names = [n for _, n in recent]
    
    return paths, new_used_names, tmp_files


def cleanup_tmp_files(tmp_files: List[str]):
    """清理临时文件"""
    for tmp in tmp_files:
        try:
            os.remove(tmp)
        except Exception:
            pass


# 全局客户端实例
_client: Optional[ZentaoClient] = None


def get_client() -> ZentaoClient:
    """获取全局客户端实例"""
    global _client
    if _client is None:
        _client = ZentaoClient()
    return _client
