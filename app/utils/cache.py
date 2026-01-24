"""
地点缓存管理
防止同一地点 10 分钟内重复请求 API
"""

from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import json


class LocationCache:
    """
    地点数据缓存管理器
    
    功能：
    - 缓存同一地点的天气数据
    - 自动过期检查（10分钟）
    - 支持多个地点的并发缓存
    
    使用示例：
    ```python
    cache = LocationCache()
    
    # 设置缓存
    cache.set("p1", {"temp": 20, "rain": 0.3})
    
    # 检查是否有有效缓存
    if cache.is_valid("p1"):
        data = cache.get("p1")
    else:
        # 重新请求 API
        pass
    
    # 清除缓存
    cache.clear("p1")
    ```
    """
    
    # 缓存过期时间（10分钟）
    CACHE_TTL = 600  # 秒
    
    def __init__(self):
        """初始化缓存"""
        # 缓存存储结构: {place_id: {"data": ..., "timestamp": ...}}
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def set(self, place_id: str, data: dict) -> None:
        """
        设置缓存
        
        Args:
            place_id: 地点ID（如 "p1"）
            data: 要缓存的数据字典
        """
        self._cache[place_id] = {
            "data": data,
            "timestamp": datetime.now()
        }
        print(f"[Cache] Set cache for place_id={place_id} at {datetime.now().strftime('%H:%M:%S')}")
    
    def get(self, place_id: str) -> Optional[dict]:
        """
        获取缓存数据
        
        Args:
            place_id: 地点ID
            
        Returns:
            缓存数据，若不存在或已过期则返回 None
        """
        if not self.is_valid(place_id):
            return None
        
        return self._cache[place_id]["data"]
    
    def is_valid(self, place_id: str) -> bool:
        """
        检查缓存是否有效（存在且未过期）
        
        Args:
            place_id: 地点ID
            
        Returns:
            True 表示缓存有效，False 表示缓存不存在或已过期
        """
        if place_id not in self._cache:
            return False
        
        cache_entry = self._cache[place_id]
        cached_time = cache_entry["timestamp"]
        
        # 计算缓存年龄（秒）
        age = (datetime.now() - cached_time).total_seconds()
        
        if age > self.CACHE_TTL:
            # 缓存已过期，删除它
            self.clear(place_id)
            print(f"[Cache] Cache for place_id={place_id} expired after {age:.0f}s")
            return False
        
        print(f"[Cache] Cache for place_id={place_id} is valid (age: {age:.0f}s, TTL: {self.CACHE_TTL}s)")
        return True
    
    def clear(self, place_id: str) -> None:
        """
        清除指定地点的缓存
        
        Args:
            place_id: 地点ID
        """
        if place_id in self._cache:
            del self._cache[place_id]
            print(f"[Cache] Cleared cache for place_id={place_id}")
    
    def clear_all(self) -> None:
        """清除所有缓存"""
        self._cache.clear()
        print("[Cache] Cleared all caches")
    
    def get_remaining_time(self, place_id: str) -> Optional[int]:
        """
        获取缓存的剩余有效时间（秒）
        
        Args:
            place_id: 地点ID
            
        Returns:
            剩余时间（秒），若缓存不存在或已过期则返回 None
        """
        if place_id not in self._cache:
            return None
        
        cache_entry = self._cache[place_id]
        cached_time = cache_entry["timestamp"]
        age = (datetime.now() - cached_time).total_seconds()
        remaining = self.CACHE_TTL - age
        
        if remaining <= 0:
            return None
        
        return int(remaining)
    
    def get_cache_info(self, place_id: str) -> Optional[dict]:
        """
        获取缓存信息（用于调试）
        
        Args:
            place_id: 地点ID
            
        Returns:
            缓存信息，包括时间戳和数据摘要
        """
        if place_id not in self._cache:
            return None
        
        cache_entry = self._cache[place_id]
        age = (datetime.now() - cache_entry["timestamp"]).total_seconds()
        remaining = self.get_remaining_time(place_id)
        
        return {
            "place_id": place_id,
            "cached_at": cache_entry["timestamp"].isoformat(),
            "age_seconds": int(age),
            "remaining_seconds": remaining,
            "is_valid": self.is_valid(place_id)
        }
    
    def export_stats(self) -> dict:
        """
        导出缓存统计信息
        
        Returns:
            包含缓存数量和各地点信息的统计字典
        """
        stats = {
            "total_cached": len(self._cache),
            "ttl_seconds": self.CACHE_TTL,
            "cached_places": {}
        }
        
        for place_id in self._cache.keys():
            info = self.get_cache_info(place_id)
            if info:
                stats["cached_places"][place_id] = info
        
        return stats


# 全局缓存实例（单例模式）
_cache_instance: Optional[LocationCache] = None


def get_location_cache() -> LocationCache:
    """
    获取全局缓存实例
    
    Returns:
        LocationCache 单例实例
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LocationCache()
    return _cache_instance
