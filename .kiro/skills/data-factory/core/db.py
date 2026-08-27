# -*- coding: utf-8 -*-
"""
数据库客户端模块。

提供数据库连接管理和查询功能，支持连接复用、自动重连、批量操作。

连接策略:
    - 懒加载: 首次查询时建立连接
    - 连接复用: 同一实例的多次查询复用同一连接
    - 自动重连: 连接断开时自动重新建立
    - 显式关闭: 调用 close() 释放连接

Example:
    from core.db import DbClient
    
    # 使用 with 语句自动管理连接
    with DbClient("UAT") as db:
        user = db.query_one("SELECT * FROM users WHERE id = %s", (123,))
        items = db.query_all("SELECT * FROM items WHERE status = %s", ("A",))
    
    # 批量查询
    items = db.query_in(
        "SELECT * FROM items WHERE item_number IN ({placeholders})",
        ["item1", "item2", "item3"]
    )
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from config import DB_CONFIGS

# ==================== 写操作白名单 ====================
# 只有在白名单中的 SQL 才允许执行写操作
# 防止 LLM 被诱导执行任意 SQL 修改数据库
# 匹配规则：去除空白后检查是否以白名单前缀开头
WRITE_SQL_WHITELIST = [
    # 礼卡扣减（set_giftcard 减少余额时使用）
    "UPDATE yamibuy_master.xysc_egift_card SET use_amount",
    # 订单送达状态更新（delivered 操作）
    "UPDATE yamibuy_so.so_tracking_info SET status",
    # 订单送达时间更新（update_delivery_time 操作）
    "UPDATE yamibuy_so.so_tracking_info SET delivery_time",
    # VIP 等级降级（set_vip_level 降级时需要直接修改 DB）
    "UPDATE yamibuy_crm.crm_customer_vip_info SET level_id",
]


def _normalize_sql(sql: str) -> str:
    """
    标准化 SQL 语句，去除多余空白以便匹配。
    
    Args:
        sql: 原始 SQL 语句。
    
    Returns:
        标准化后的 SQL（多个空白字符合并为单个空格）。
    """
    import re
    # 去除首尾空白，将连续空白字符（空格、换行、制表符）替换为单个空格
    return re.sub(r'\s+', ' ', sql.strip())


def _check_write_whitelist(sql: str) -> None:
    """
    检查写操作 SQL 是否在白名单中。
    
    Args:
        sql: 要执行的 SQL 语句。
    
    Raises:
        PermissionError: SQL 不在白名单中时抛出。
    """
    sql_normalized = _normalize_sql(sql)
    sql_upper = sql_normalized.upper()
    
    # 只对写操作做白名单校验
    if not sql_upper.startswith(("UPDATE", "INSERT", "DELETE")):
        return
    
    # 检查是否匹配白名单中的任意前缀（标准化后比较）
    for allowed_prefix in WRITE_SQL_WHITELIST:
        if sql_normalized.startswith(allowed_prefix):
            return
    
    # 不在白名单中，拒绝执行
    raise PermissionError(
        f"SQL 写操作未在白名单中，拒绝执行。\n"
        f"SQL 前缀: {sql_normalized[:80]}...\n"
        f"如需添加新的写操作，请联系管理员更新 WRITE_SQL_WHITELIST"
    )


if TYPE_CHECKING:
    from mysql.connector.connection import MySQLConnection


class DbClient:
    """
    数据库客户端，按环境自动选择数据库配置。
    
    支持连接复用、自动重连、批量操作，可用于查询和写入。
    
    Attributes:
        env: 环境标识（UAT/GQC/DEV）。
        db_config: 数据库连接配置字典。
    
    Example:
        # 基本用法
        db = DbClient("UAT")
        result = db.query_one("SELECT * FROM users WHERE id = %s", (1,))
        db.close()
        
        # 使用 with 语句
        with DbClient("UAT") as db:
            users = db.query_all("SELECT * FROM users LIMIT 10")
    """

    def __init__(self, env: str) -> None:
        """
        初始化数据库客户端。
        
        Args:
            env: 环境标识，支持 UAT/GQC/DEV，默认回退到 UAT。
        """
        self.env: str = env
        self.db_config: Dict[str, Any] = DB_CONFIGS.get(env, DB_CONFIGS["UAT"])
        self._conn: Optional[MySQLConnection] = None

    def _get_conn(self) -> MySQLConnection:
        """
        获取数据库连接（懒加载 + 自动重连）。
        
        Returns:
            数据库连接对象。
        
        Raises:
            RuntimeError: 缺少 mysql-connector-python 依赖或连接失败时抛出。
        """
        try:
            import mysql.connector
        except ImportError:
            raise RuntimeError("缺少依赖，请执行: pip install mysql-connector-python")
        
        # 检查现有连接是否可用
        if self._conn is not None:
            try:
                # ping 检测连接是否存活
                self._conn.ping(reconnect=True, attempts=1, delay=0)
                return self._conn
            except Exception:
                # 连接已断开，关闭并重建
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None
        
        # 建立新连接
        try:
            self._conn = mysql.connector.connect(**self.db_config)
            return self._conn
        except Exception as e:
            raise RuntimeError(f"数据库连接失败 [{self.env}]: {e}")

    def query_one(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        查询单行数据。
        
        Args:
            sql: SQL 查询语句。
            params: 参数元组，用于参数化查询。
        
        Returns:
            查询结果字典，无结果时返回 None。
        
        Raises:
            RuntimeError: SQL 执行失败时抛出。
        
        Example:
            user = db.query_one(
                "SELECT * FROM users WHERE id = %s",
                (123,)
            )
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, params or ())
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            # 查询失败时重置连接，下次查询会重连
            self._conn = None
            raise RuntimeError(f"SQL 查询失败: {e}\nSQL: {sql}")

    def query_all(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None
    ) -> List[Dict[str, Any]]:
        """
        查询多行数据。
        
        Args:
            sql: SQL 查询语句。
            params: 参数元组，用于参数化查询。
        
        Returns:
            查询结果列表，每个元素为字典。
        
        Raises:
            RuntimeError: SQL 执行失败时抛出。
        
        Example:
            items = db.query_all(
                "SELECT * FROM items WHERE status = %s LIMIT 100",
                ("A",)
            )
        """
        conn = self._get_conn()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, params or ())
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            # 查询失败时重置连接，下次查询会重连
            self._conn = None
            raise RuntimeError(f"SQL 查询失败: {e}\nSQL: {sql}")

    def query_value(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None
    ) -> Optional[Any]:
        """
        查询单个值。
        
        Args:
            sql: SQL 查询语句。
            params: 参数元组，用于参数化查询。
        
        Returns:
            第一行第一列的值，无结果时返回 None。
        
        Example:
            count = db.query_value(
                "SELECT COUNT(*) FROM users WHERE status = %s",
                ("active",)
            )
        """
        row = self.query_one(sql, params)
        if row:
            return list(row.values())[0]
        return None

    def execute(
        self,
        sql: str,
        params: Optional[Tuple[Any, ...]] = None
    ) -> int:
        """
        执行写操作（INSERT/UPDATE/DELETE）。
        
        注意：写操作受白名单限制，只有在 WRITE_SQL_WHITELIST 中的 SQL 才允许执行。
        
        Args:
            sql: SQL 语句。
            params: 参数元组，用于参数化查询。
        
        Returns:
            受影响的行数。
        
        Raises:
            PermissionError: SQL 不在白名单中时抛出。
            RuntimeError: SQL 执行失败时抛出。
        
        Example:
            affected = db.execute(
                "UPDATE users SET status = %s WHERE id = %s",
                ("inactive", 123)
            )
        """
        # 白名单校验
        _check_write_whitelist(sql)
        
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected
        except Exception as e:
            # 执行失败时回滚并重置连接
            try:
                conn.rollback()
            except Exception:
                pass
            self._conn = None
            raise RuntimeError(f"SQL 执行失败: {e}\nSQL: {sql}")

    def execute_many(
        self,
        sql: str,
        params_list: List[Tuple[Any, ...]]
    ) -> int:
        """
        批量执行写操作（INSERT/UPDATE/DELETE）。
        
        使用 executemany 一次性执行多条相同结构的 SQL，比循环 execute 更高效。
        
        注意：写操作受白名单限制，只有在 WRITE_SQL_WHITELIST 中的 SQL 才允许执行。
        
        Args:
            sql: SQL 语句（带占位符）。
            params_list: 参数列表，每个元素是一个参数元组。
        
        Returns:
            受影响的总行数。
        
        Raises:
            PermissionError: SQL 不在白名单中时抛出。
            RuntimeError: SQL 执行失败时抛出。
        
        Example:
            affected = db.execute_many(
                "UPDATE orders SET status = %s WHERE order_id = %s",
                [("shipped", 1001), ("shipped", 1002), ("shipped", 1003)]
            )
        """
        if not params_list:
            return 0
        
        # 白名单校验
        _check_write_whitelist(sql)
        
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.executemany(sql, params_list)
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            return affected
        except Exception as e:
            # 执行失败时回滚并重置连接
            try:
                conn.rollback()
            except Exception:
                pass
            self._conn = None
            raise RuntimeError(f"SQL 批量执行失败: {e}\nSQL: {sql}")

    def close(self) -> None:
        """显式关闭数据库连接。"""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def __del__(self) -> None:
        """析构时关闭连接。"""
        self.close()

    def __enter__(self) -> DbClient:
        """
        支持 with 语句的上下文管理器入口。
        
        Returns:
            当前 DbClient 实例。
        """
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any]
    ) -> bool:
        """
        退出 with 语句时关闭连接。
        
        Args:
            exc_type: 异常类型。
            exc_val: 异常值。
            exc_tb: 异常追踪信息。
        
        Returns:
            False，不抑制异常。
        """
        self.close()
        return False

    # ==================== 安全的批量查询方法 ====================

    def query_in(
        self,
        sql_template: str,
        values: List[Any],
        extra_params: Optional[Tuple[Any, ...]] = None
    ) -> List[Dict[str, Any]]:
        """
        安全的 IN 查询，自动构建参数化占位符。
        
        Args:
            sql_template: SQL 模板，包含 {placeholders} 占位符。
            values: IN 子句的值列表。
            extra_params: 额外的参数元组（用于 IN 之外的其他占位符）。
        
        Returns:
            查询结果列表。
        
        Example:
            items = db.query_in(
                "SELECT * FROM items WHERE item_number IN ({placeholders}) AND status = %s",
                ["item1", "item2"],
                extra_params=("A",)
            )
        """
        if not values:
            return []
        
        # 构建占位符
        placeholders = ",".join(["%s"] * len(values))
        sql = sql_template.format(placeholders=placeholders)
        
        # 合并参数
        params = tuple(values)
        if extra_params:
            params = params + extra_params
        
        return self.query_all(sql, params)

    def query_or_conditions(
        self,
        sql_template: str,
        condition_template: str,
        params_list: List[Union[Tuple[Any, ...], Any]]
    ) -> List[Dict[str, Any]]:
        """
        安全的 OR 条件查询，自动构建参数化条件。
        
        Args:
            sql_template: SQL 模板，包含 {conditions} 占位符。
            condition_template: 单个条件模板。
            params_list: 参数列表，每个元素是一个条件的参数元组。
        
        Returns:
            查询结果列表。
        
        Example:
            rows = db.query_or_conditions(
                "SELECT * FROM inventory WHERE {conditions}",
                "(item_number = %s AND warehouse_number = %s)",
                [("item1", "001"), ("item2", "002")]
            )
        """
        if not params_list:
            return []
        
        # 构建 OR 条件
        conditions = " OR ".join([condition_template] * len(params_list))
        sql = sql_template.format(conditions=conditions)
        
        # 展平参数
        params: List[Any] = []
        for p in params_list:
            if isinstance(p, (list, tuple)):
                params.extend(p)
            else:
                params.append(p)
        
        return self.query_all(sql, tuple(params))
