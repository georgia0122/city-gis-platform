"""
测试天气API数据返回
"""
import asyncio
import httpx

async def test_weather_api():
    """测试天气API返回的数据"""
    
    # 测试天津滨海新区的坐标
    lat = 39.0851
    lng = 117.1994
    
    url = f"http://localhost:8000/api/weather_hourly?lat={lat}&lng={lng}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            data = response.json()
            
            print("="*60)
            print("天气API返回数据:")
            print("="*60)
            print(f"纬度: {data.get('lat')}")
            print(f"经度: {data.get('lng')}")
            print(f"数据源: {data.get('source')}")
            print(f"是否来自缓存: {data.get('from_cache')}")
            print()
            print(f"当前UV指数: {data.get('current_uv')}")
            print(f"最大UV指数: {data.get('max_uv')}")
            print()
            print(f"雨概率 (前5小时):")
            rain_probs = data.get('rain_prob', [])
            for i, prob in enumerate(rain_probs[:5]):
                print(f"  {i}小时后: {prob * 100:.1f}%")
            print()
            print(f"UV指数 (前5小时):")
            uv_indices = data.get('uv_index', [])
            for i, uv in enumerate(uv_indices[:5]):
                print(f"  {i}小时后: {uv}")
            print()
            print("防晒建议:")
            sun_protection = data.get('sun_protection', {})
            print(f"  级别: {sun_protection.get('level')}")
            print(f"  颜色: {sun_protection.get('color')}")
            print(f"  建议: {sun_protection.get('advice')}")
            print("="*60)
            
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_weather_api())
