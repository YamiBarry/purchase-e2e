# -*- coding: utf-8 -*-
"""
MKT 服务 API 封装。

统一处理 central-mkt 后台接口调用，包括优惠券、促销活动、赠品活动等。

Example:
    mkt = MktApiClient(client, hub_token)
    resp = mkt.insert_promotion(body)
    if mkt.is_success(resp):
        ps_id = resp.get("body")
"""

from typing import Any, Dict, List, Optional

from core.http_client import HttpClient


class MktApiClient:
    """
    MKT 服务 API 客户端。
    
    封装 central-mkt 后台常用接口，统一处理 token 和错误响应。
    
    Attributes:
        client: HttpClient 实例。
        hub_token: Hub admin token。
        base_url: central API 基础 URL。
    """
    
    def __init__(self, client: HttpClient, hub_token: str) -> None:
        """
        初始化 MKT API 客户端。
        
        Args:
            client: HttpClient 实例。
            hub_token: Hub admin token。
        """
        self.client: HttpClient = client
        self.hub_token: str = hub_token
        self.base_url: str = client.central_base
    
    def post(
        self, 
        path: str, 
        body: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        发送 POST 请求到 MKT 服务。
        
        Args:
            path: API 路径（如 /mkt/promotion/v1/insert）。
            body: 请求体字典。
            timeout: 超时时间（秒），默认 30。
        
        Returns:
            响应字典，包含 _status 字段表示 HTTP 状态码。
        """
        status, resp = self.client.post_central(path, body, self.hub_token, timeout)
        resp["_status"] = status
        return resp
    
    def get(
        self, 
        path: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        发送 GET 请求到 MKT 服务。
        
        Args:
            path: API 路径。
            timeout: 超时时间（秒），默认 30。
        
        Returns:
            响应字典，包含 _status 字段表示 HTTP 状态码。
        """
        url = self.base_url + path
        headers: Dict[str, str] = {"token": self.hub_token}
        status, resp = self.client._request("GET", url, extra_headers=headers, timeout=timeout)
        resp["_status"] = status
        return resp
    
    def is_success(self, resp: Dict[str, Any]) -> bool:
        """
        判断响应是否成功。
        
        Args:
            resp: 响应字典。
        
        Returns:
            True 表示成功（status=200 且 messageId 为 200 或 10000）。
        """
        status = resp.get("_status", 0)
        return status == 200 and resp.get("messageId") in ("200", "10000")
    
    def get_error(self, resp: Dict[str, Any]) -> str:
        """
        从响应中提取错误信息。
        
        Args:
            resp: 响应字典。
        
        Returns:
            错误信息字符串。
        """
        return (
            resp.get("zhError")
            or resp.get("message")
            or resp.get("error")
            or str(resp)[:200]
        )
    
    # ==================== 优惠券相关接口 ====================
    
    def insert_coupon(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建优惠券。
        
        Args:
            body: 优惠券配置，包含 coupon_form、send_type、ps_content 等。
        
        Returns:
            响应字典，成功时 body 为 ps_id。
        """
        return self.post("/mkt/couponSchedule/v1/insert", body)
    
    def submit_coupon(self, ps_id: int) -> Dict[str, Any]:
        """
        提交优惠券。
        
        Args:
            ps_id: 优惠券活动 ID。
        
        Returns:
            响应字典。
        """
        return self.post("/mkt/couponSchedule/v1/submitCoupon", {"ps_id": ps_id})
    
    def confirm_coupon(self, ps_id: int) -> Dict[str, Any]:
        """
        确认优惠券生效。
        
        Args:
            ps_id: 优惠券活动 ID。
        
        Returns:
            响应字典。
        """
        return self.post("/mkt/couponSchedule/v1/confirmEffective", {"ps_id": ps_id})
    
    def query_coupon_list(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        查询优惠券列表。
        
        Args:
            body: 查询条件。
        
        Returns:
            响应字典，body 为优惠券列表。
        """
        return self.post("/mkt/couponSchedule/v1/queryCouponList", body)
    
    # ==================== 促销活动相关接口 ====================
    
    def insert_promotion(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建促销活动。
        
        Args:
            body: 促销活动配置。
        
        Returns:
            响应字典，成功时 body 为 ps_id。
        """
        return self.post("/mkt/promotion/v1/insert", body)
    
    def submit_promotion(self, ps_id: int, ps_version: int = 1, force: bool = False) -> Dict[str, Any]:
        """
        提交促销活动。
        
        Args:
            ps_id: 促销活动 ID。
            ps_version: 版本号，默认 1。
            force: 是否强制提交（忽略冲突），默认 False。
        
        Returns:
            响应字典。
        """
        return self.post("/mkt/promotion/v1/submit", {
            "ps_id": ps_id, 
            "ps_version": ps_version, 
            "force": force
        })
    
    def finish_promotion(self, ps_id: int, promo_type: int = 10) -> Dict[str, Any]:
        """
        结束促销活动。
        
        Args:
            ps_id: 促销活动 ID。
            promo_type: 促销类型，默认 10（直降）。
        
        Returns:
            响应字典。
        """
        return self.post("/mkt/promotion/v1/finishSchdule", {
            "ps_id": ps_id, 
            "type": promo_type
        })
    
    def query_promotion_list(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        查询促销活动列表。
        
        Args:
            body: 查询条件。
        
        Returns:
            响应字典，body 为促销活动列表。
        """
        return self.post("/mkt/promotion/v1/queryList", body)
    
    def query_promotion_goods(self, ps_id: int, start: int = 0, length: int = 200) -> Dict[str, Any]:
        """
        查询促销活动商品列表。
        
        Args:
            ps_id: 促销活动 ID。
            start: 起始位置，默认 0。
            length: 返回数量，默认 200。
        
        Returns:
            响应字典，body 为商品列表。
        """
        return self.post("/mkt/promotion/v1/queryPromotionGoodsList", {
            "ps_id": ps_id,
            "draw": 1,
            "start": start,
            "length": length,
        })
    
    # ==================== 秒杀相关接口 ====================
    
    def submit_seckill(self, ps_id: int, ps_version: int = 1, force: bool = False) -> Dict[str, Any]:
        """
        提交秒杀活动。
        
        Args:
            ps_id: 秒杀活动 ID。
            ps_version: 版本号，默认 1。
            force: 是否强制提交，默认 False。
        
        Returns:
            响应字典。
        """
        return self.post("/mkt/seckill/v1/submit", {
            "ps_id": ps_id, 
            "ps_version": ps_version, 
            "force": force
        })
    
    # ==================== 赠品活动相关接口 ====================
    
    def insert_gift_promotion(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建赠品活动。
        
        Args:
            body: 赠品活动配置。
        
        Returns:
            响应字典，成功时 body 为 ps_id。
        """
        return self.post("/mkt/giftPromotion/insert", body, timeout=60)
    
    def submit_gift_promotion(self, ps_id: int, step: int = 1) -> Dict[str, Any]:
        """
        提交赠品活动。
        
        Args:
            ps_id: 赠品活动 ID。
            step: 提交步骤，1=首次提交，2=确认提交（有重叠时）。
        
        Returns:
            响应字典。
        """
        return self.post(f"/mkt/giftPromotion/submit/{step}", {"ps_id": ps_id}, timeout=120)
    
    def finish_gift_promotion(self, ps_id: int) -> Dict[str, Any]:
        """
        结束赠品活动。
        
        Args:
            ps_id: 赠品活动 ID。
        
        Returns:
            响应字典。
        """
        return self.post("/mkt/giftPromotion/invalid", {"ps_id": ps_id})
    
    def query_gift_promotion_list(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        查询赠品活动列表。
        
        Args:
            body: 查询条件。
        
        Returns:
            响应字典，body 为赠品活动列表。
        """
        return self.post("/mkt/giftPromotion/queryList", body)
    
    # ==================== 商品查询接口 ====================
    
    def query_item_for_mkt(self, item_numbers: List[str]) -> Dict[str, Any]:
        """
        查询商品信息（用于促销活动）。
        
        Args:
            item_numbers: 商品编号列表。
        
        Returns:
            响应字典，body 为商品信息列表。
        """
        return self.post("/mkt/im/item/queryItemInfoForMkt", {
            "search_goods_id": "",
            "category_id": "",
            "brand_id": "",
            "status": None,
            "exclude_gift": 1,
            "exclude_giftcard": 0,
            "itemList": item_numbers,
        })
