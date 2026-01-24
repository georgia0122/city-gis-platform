"""
缓存功能测试脚本

测试：同一地点 10 分钟内不重复请求 API

使用方法：
    python test_cache.py

测试流程：
1. 第一次请求获取天气数据（会调用 API）
2. 第二次立即请求相同地点（应该返回缓存数据）
3. 检查缓存统计信息
4. 清除缓存后再次请求（会重新调用 API）
"""

import asyncio
import httpx
import json
from datetime import datetime
import time


# API 基础 URL
BASE_URL = "http://localhost:8000"


async def test_cache_mechanism():
    """测试缓存机制"""
    
    print("=" * 80)
    print("City GIS Platform - 缓存机制测试")
    print("=" * 80)
    print()
    
    async with httpx.AsyncClient() as client:
        
        # ==================== 测试 1: /api/weather_hourly 缓存 ====================
        print("[Test 1] 测试 /api/weather_hourly 缓存")
        print("-" * 80)
        
        place_id = "p1"  # 天津市区
        
        # 第一次请求（应该调用 API）
        print(f"\n[请求 1] 首次请求地点 {place_id}...")
        start_time = time.time()
        response1 = await client.get(f"{BASE_URL}/api/weather_hourly", params={"place_id": place_id})
        duration1 = time.time() - start_time
        
        print(f"  状态码: {response1.status_code}")
        print(f"  耗时: {duration1:.3f}秒")
        data1 = response1.json()
        print(f"  from_cache: {data1.get('from_cache', False)}")
        print(f"  fetched_at: {data1.get('fetched_at')}")
        
        # 第二次请求（应该返回缓存）
        await asyncio.sleep(0.5)  # 稍等一下
        print(f"\n[请求 2] 0.5秒后再次请求同一地点...")
        start_time = time.time()
        response2 = await client.get(f"{BASE_URL}/api/weather_hourly", params={"place_id": place_id})
        duration2 = time.time() - start_time
        
        print(f"  状态码: {response2.status_code}")
        print(f"  耗时: {duration2:.3f}秒（应该比第一次快）")
        data2 = response2.json()
        print(f"  from_cache: {data2.get('from_cache', False)}")
        print(f"  cache_remaining_seconds: {data2.get('cache_remaining_seconds')}")
        
        # 验证缓存命中
        if data2.get("from_cache") and duration2 < duration1:
            print("  ✓ 缓存命中！")
        else:
            print("  ✗ 缓存未命中")
        
        # ==================== 测试 2: /api/ai_analysis 缓存 ====================
        print("\n" + "=" * 80)
        print("[Test 2] 测试 /api/ai_analysis 缓存")
        print("-" * 80)
        
        # 第一次请求
        print(f"\n[请求 1] 首次请求 AI 分析（地点 {place_id}）...")
        start_time = time.time()
        response3 = await client.post(
            f"{BASE_URL}/api/ai_analysis",
            json={"place_id": place_id, "place_name": "天津市区", "city": "天津"}
        )
        duration3 = time.time() - start_time
        
        print(f"  状态码: {response3.status_code}")
        print(f"  耗时: {duration3:.3f}秒")
        data3 = response3.json()
        print(f"  from_cache: {data3.get('from_cache', False)}")
        print(f"  analysis_method: {data3.get('analysis_method')}")
        
        # 第二次请求
        await asyncio.sleep(0.5)
        print(f"\n[请求 2] 0.5秒后再次请求 AI 分析...")
        start_time = time.time()
        response4 = await client.post(
            f"{BASE_URL}/api/ai_analysis",
            json={"place_id": place_id, "place_name": "天津市区", "city": "天津"}
        )
        duration4 = time.time() - start_time
        
        print(f"  状态码: {response4.status_code}")
        print(f"  耗时: {duration4:.3f}秒（应该比第一次快）")
        data4 = response4.json()
        print(f"  from_cache: {data4.get('from_cache', False)}")
        print(f"  cache_remaining_seconds: {data4.get('cache_remaining_seconds')}")
        
        if data4.get("from_cache") and duration4 < duration3:
            print("  ✓ 缓存命中！")
        else:
            print("  ✗ 缓存未命中")
        
        # ==================== 测试 3: 缓存统计信息 ====================
        print("\n" + "=" * 80)
        print("[Test 3] 获取缓存统计信息")
        print("-" * 80)
        
        response5 = await client.get(f"{BASE_URL}/api/cache/stats")
        print(f"\n状态码: {response5.status_code}")
        stats = response5.json()
        print(f"缓存统计:")
        print(f"  总缓存数量: {stats.get('total_cached')}")
        print(f"  缓存有效期: {stats.get('ttl_seconds')}秒")
        
        cached_places = stats.get('cached_places', {})
        if cached_places:
            print(f"  缓存的地点:")
            for cache_key, info in cached_places.items():
                print(f"    - {cache_key}")
                print(f"      缓存时间: {info.get('cached_at')}")
                print(f"      年龄: {info.get('age_seconds')}秒")
                print(f"      剩余: {info.get('remaining_seconds')}秒")
                print(f"      有效: {info.get('is_valid')}")
        
        # ==================== 测试 4: 清除缓存后重新请求 ====================
        print("\n" + "=" * 80)
        print("[Test 4] 清除缓存并重新请求")
        print("-" * 80)
        
        # 清除特定地点的缓存
        print(f"\n[操作] 清除地点 {place_id} 的缓存...")
        response6 = await client.get(f"{BASE_URL}/api/cache/clear", params={"place_id": place_id})
        print(f"  状态码: {response6.status_code}")
        print(f"  响应: {response6.json()}")
        
        # 再次请求（应该重新调用 API）
        await asyncio.sleep(0.5)
        print(f"\n[请求 3] 清除后再次请求...")
        start_time = time.time()
        response7 = await client.get(f"{BASE_URL}/api/weather_hourly", params={"place_id": place_id})
        duration7 = time.time() - start_time
        
        print(f"  状态码: {response7.status_code}")
        print(f"  耗时: {duration7:.3f}秒")
        data7 = response7.json()
        print(f"  from_cache: {data7.get('from_cache', False)}")
        
        if not data7.get("from_cache"):
            print("  ✓ 缓存已清除，重新请求 API")
        else:
            print("  ✗ 缓存清除失败")
        
        # ==================== 测试 5: 不同地点缓存独立性 ====================
        print("\n" + "=" * 80)
        print("[Test 5] 不同地点缓存独立性")
        print("-" * 80)
        
        place_id_2 = "p4"  # 北京市区
        
        print(f"\n[请求 1] 请求地点 {place_id_2}...")
        response8 = await client.get(f"{BASE_URL}/api/weather_hourly", params={"place_id": place_id_2})
        data8 = response8.json()
        print(f"  from_cache: {data8.get('from_cache', False)}")
        
        await asyncio.sleep(0.5)
        print(f"\n[请求 2] 0.5秒后再次请求地点 {place_id_2}...")
        response9 = await client.get(f"{BASE_URL}/api/weather_hourly", params={"place_id": place_id_2})
        data9 = response9.json()
        print(f"  from_cache: {data9.get('from_cache', False)}")
        
        if data9.get("from_cache"):
            print("  ✓ 地点缓存独立性验证成功")
        else:
            print("  ✗ 地点缓存独立性验证失败")
        
        # ==================== 最终统计 ====================
        print("\n" + "=" * 80)
        print("[最终] 缓存统计信息")
        print("-" * 80)
        
        response10 = await client.get(f"{BASE_URL}/api/cache/stats")
        final_stats = response10.json()
        print(f"\n最终缓存状态:")
        print(f"  总缓存数量: {final_stats.get('total_cached')}")
        print(json.dumps(final_stats, ensure_ascii=False, indent=2))
        
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(test_cache_mechanism())
    except KeyboardInterrupt:
        print("\n\n测试被中断")
    except Exception as e:
        print(f"\n\n错误: {e}")
        import traceback
        traceback.print_exc()
