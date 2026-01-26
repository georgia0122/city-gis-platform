"""
测试出行规划 Agent
验证智能出行规划功能的各个方面
"""

import asyncio
import json
from app.agents.travel_planner_agent import get_travel_planner_agent
from app.models.schemas import WeatherData, TravelPlanningRequest


async def test_travel_planning():
    """测试出行规划功能"""
    
    print("=" * 60)
    print("智能出行规划 Agent 测试")
    print("=" * 60)
    
    # 获取 Agent 实例
    agent = get_travel_planner_agent()
    
    # 测试场景 1：晴天出行
    print("\n📝 测试场景 1：晴天出行")
    print("-" * 60)
    
    weather_data_1 = WeatherData(
        place_name="天津和平区",
        city="天津",
        current_temp=22.5,
        rain_probability=0.05,
        wind_speed=2.0,
        hourly_temps=[20.0, 21.0, 22.0, 23.0, 24.0, 25.0],
        hourly_rain_probs=[0.05, 0.05, 0.05, 0.05, 0.1, 0.1],
        hourly_winds=[2.0, 2.2, 2.5, 2.8, 3.0, 3.2],
        current_time="2026-01-26 09:00:00",
        humidity=60.0
    )
    
    request_1 = TravelPlanningRequest(
        origin="天津和平广场",
        destination="天津滨河公园",
        preferred_time="09:00",
        preferred_modes=["subway", "bus", "walking"],
        expected_duration=30,
        distance=8.5
    )
    
    try:
        result_1 = await agent.plan_travel(request_1, weather_data_1)
        print(f"✅ 场景 1 成功")
        print(f"   首选方式: {result_1.primary_mode}")
        print(f"   建议出发时间: {result_1.departure_time}")
        print(f"   预计时长: {result_1.travel_duration} 分钟")
        print(f"   置信度: {result_1.confidence_score:.2%}")
        print(f"   出行方式评级数: {len(result_1.modes_rating)}")
        print(f"   推荐路线数: {len(result_1.recommended_routes)}")
    except Exception as e:
        print(f"❌ 场景 1 失败: {str(e)}")
    
    # 测试场景 2：下雨天出行
    print("\n📝 测试场景 2：下雨天出行")
    print("-" * 60)
    
    weather_data_2 = WeatherData(
        place_name="北京朝阳区",
        city="北京",
        current_temp=15.0,
        rain_probability=0.75,
        wind_speed=4.5,
        hourly_temps=[14.0, 14.5, 15.0, 15.5, 16.0, 16.5],
        hourly_rain_probs=[0.7, 0.75, 0.80, 0.75, 0.65, 0.55],
        hourly_winds=[4.0, 4.2, 4.5, 4.8, 5.0, 4.8],
        current_time="2026-01-26 14:00:00",
        humidity=85.0
    )
    
    request_2 = TravelPlanningRequest(
        origin="北京中关村",
        destination="北京首都机场",
        preferred_time="15:00",
        preferred_modes=None,  # 考虑所有方式
        expected_duration=45,
        distance=28.0
    )
    
    try:
        result_2 = await agent.plan_travel(request_2, weather_data_2)
        print(f"✅ 场景 2 成功")
        print(f"   首选方式: {result_2.primary_mode}")
        print(f"   天气总体影响: {result_2.weather_impact['overall_impact']}")
        print(f"   具体风险数: {len(result_2.weather_impact['specific_risks'])}")
        print(f"   应对措施数: {len(result_2.weather_impact['precautions'])}")
        print(f"   路况预测: {result_2.traffic_prediction['current_level']}")
        print(f"   出行建议数: {len(result_2.suggestions)}")
        
        if result_2.weather_impact['specific_risks']:
            print(f"\n   🚨 具体风险:")
            for risk in result_2.weather_impact['specific_risks'][:3]:
                print(f"      - {risk}")
        
        if result_2.weather_impact['precautions']:
            print(f"\n   ✓ 应对措施:")
            for precaution in result_2.weather_impact['precautions'][:3]:
                print(f"      - {precaution}")
                
    except Exception as e:
        print(f"❌ 场景 2 失败: {str(e)}")
    
    # 测试场景 3：高温天气
    print("\n📝 测试场景 3：高温天气")
    print("-" * 60)
    
    weather_data_3 = WeatherData(
        place_name="深圳南山区",
        city="深圳",
        current_temp=38.0,
        rain_probability=0.1,
        wind_speed=3.5,
        hourly_temps=[36.0, 37.0, 38.0, 38.5, 38.0, 37.0],
        hourly_rain_probs=[0.05, 0.05, 0.1, 0.1, 0.15, 0.2],
        hourly_winds=[3.0, 3.2, 3.5, 3.8, 4.0, 3.8],
        current_time="2026-01-26 12:00:00",
        humidity=75.0
    )
    
    request_3 = TravelPlanningRequest(
        origin="深圳福田中心区",
        destination="深圳机场",
        preferred_time="12:30",
        preferred_modes=["subway", "bus", "driving"],
        expected_duration=40,
        distance=35.0
    )
    
    try:
        result_3 = await agent.plan_travel(request_3, weather_data_3)
        print(f"✅ 场景 3 成功")
        print(f"   首选方式: {result_3.primary_mode}")
        print(f"   出行建议数: {len(result_3.suggestions)}")
        
        print(f"\n   各出行方式状态:")
        for mode in result_3.modes_rating[:3]:
            status_emoji = "✓" if mode.status == "GO" else "⚠" if mode.status == "CAUTION" else "✗"
            print(f"      {status_emoji} {mode.name}: {mode.status}")
            
        if result_3.suggestions:
            print(f"\n   💡 建议:")
            for suggestion in result_3.suggestions[:3]:
                print(f"      - {suggestion}")
                
    except Exception as e:
        print(f"❌ 场景 3 失败: {str(e)}")
    
    # 测试场景 4：强风天气
    print("\n📝 测试场景 4：强风天气")
    print("-" * 60)
    
    weather_data_4 = WeatherData(
        place_name="上海浦东新区",
        city="上海",
        current_temp=18.0,
        rain_probability=0.3,
        wind_speed=9.5,
        hourly_temps=[17.0, 17.5, 18.0, 18.5, 19.0, 18.5],
        hourly_rain_probs=[0.2, 0.25, 0.3, 0.35, 0.4, 0.35],
        hourly_winds=[8.5, 9.0, 9.5, 10.0, 9.8, 9.5],
        current_time="2026-01-26 16:00:00",
        humidity=70.0
    )
    
    request_4 = TravelPlanningRequest(
        origin="上海人民广场",
        destination="上海浦东机场",
        preferred_time="16:30",
        preferred_modes=["driving", "cycling"],
        expected_duration=50,
        distance=42.0
    )
    
    try:
        result_4 = await agent.plan_travel(request_4, weather_data_4)
        print(f"✅ 场景 4 成功")
        print(f"   首选方式: {result_4.primary_mode}")
        print(f"   置信度: {result_4.confidence_score:.2%}")
        
        # 检查是否有 AVOID 状态的建议
        avoided_modes = [m for m in result_4.modes_rating if m.status == "AVOID"]
        if avoided_modes:
            print(f"\n   ⛔ 应该避免的出行方式:")
            for mode in avoided_modes:
                print(f"      - {mode.name}: {mode.reason}")
                
    except Exception as e:
        print(f"❌ 场景 4 失败: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)


async def test_response_structure():
    """测试响应数据结构的完整性"""
    
    print("\n📊 测试响应数据结构")
    print("-" * 60)
    
    agent = get_travel_planner_agent()
    
    weather_data = WeatherData(
        place_name="测试城市",
        city="测试",
        current_temp=20.0,
        rain_probability=0.2,
        wind_speed=3.0,
        hourly_temps=[18.0, 19.0, 20.0, 21.0, 22.0, 23.0],
        hourly_rain_probs=[0.1, 0.15, 0.2, 0.25, 0.2, 0.15],
        hourly_winds=[2.0, 2.5, 3.0, 3.5, 3.0, 2.5],
        current_time="2026-01-26 10:00:00"
    )
    
    request = TravelPlanningRequest(
        origin="起点",
        destination="终点",
        expected_duration=30,
        distance=10.0
    )
    
    try:
        result = await agent.plan_travel(request, weather_data)
        
        # 检查必需字段
        required_fields = [
            'primary_mode',
            'modes_rating',
            'recommended_routes',
            'departure_time',
            'travel_duration',
            'traffic_prediction',
            'weather_impact',
            'suggestions',
            'confidence_score'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not hasattr(result, field):
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ 缺少字段: {missing_fields}")
        else:
            print(f"✅ 所有必需字段完整")
            print(f"\n   字段详情:")
            print(f"   - primary_mode: {result.primary_mode}")
            print(f"   - modes_rating 数量: {len(result.modes_rating)}")
            print(f"   - recommended_routes 数量: {len(result.recommended_routes)}")
            print(f"   - traffic_prediction: {list(result.traffic_prediction.keys())}")
            print(f"   - weather_impact: {list(result.weather_impact.keys())}")
            print(f"   - suggestions 数量: {len(result.suggestions)}")
            print(f"   - confidence_score: {result.confidence_score}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚗 智能出行规划 Agent 测试套件\n")
    
    # 运行测试
    asyncio.run(test_travel_planning())
    asyncio.run(test_response_structure())
