import asyncio
import json

# 测试模块导入
print("=" * 60)
print("测试 1: 验证模块导入")
print("=" * 60)

try:
    from app.models.schemas import WeatherData, RiskAssessment, AgentResponse
    print("✅ app.models.schemas 导入成功")
    print(f"   - WeatherData: {WeatherData.__name__}")
    print(f"   - RiskAssessment: {RiskAssessment.__name__}")
    print(f"   - AgentResponse: {AgentResponse.__name__}")
except Exception as e:
    print(f"❌ app.models.schemas 导入失败: {e}")

try:
    from app.utils.llm import LLMProvider, OpenAIProvider, MockLLMProvider, get_llm_provider
    print("✅ app.utils.llm 导入成功")
    print(f"   - LLMProvider (base): {LLMProvider.__name__}")
    print(f"   - OpenAIProvider: {OpenAIProvider.__name__}")
    print(f"   - MockLLMProvider: {MockLLMProvider.__name__}")
except Exception as e:
    print(f"❌ app.utils.llm 导入失败: {e}")

try:
    from app.agents.weather_agent import WeatherAgent, get_weather_agent, SYSTEM_PROMPT, PROMPT_TEMPLATE
    print("✅ app.agents.weather_agent 导入成功")
    print(f"   - WeatherAgent: {WeatherAgent.__name__}")
    print(f"   - SYSTEM_PROMPT length: {len(SYSTEM_PROMPT)} chars")
    print(f"   - PROMPT_TEMPLATE length: {len(PROMPT_TEMPLATE)} chars")
except Exception as e:
    print(f"❌ app.agents.weather_agent 导入失败: {e}")

# 测试 WeatherData 模型
print("\n" + "=" * 60)
print("测试 2: WeatherData 数据验证")
print("=" * 60)

try:
    weather_data = WeatherData(
        place_name="北京市",
        city="北京",
        current_temp=15.5,
        rain_probability=0.4,
        wind_speed=3.2,
        hourly_temps=[15.5] * 24,
        hourly_rain_probs=[0.4] * 24,
        hourly_winds=[3.2] * 24,
        current_time="2026-01-13 12:30"
    )
    print("✅ WeatherData 对象创建成功")
    print(f"   - place_name: {weather_data.place_name}")
    print(f"   - current_temp: {weather_data.current_temp}°C")
    print(f"   - rain_probability: {weather_data.rain_probability * 100:.0f}%")
    print(f"   - wind_speed: {weather_data.wind_speed} m/s")
except Exception as e:
    print(f"❌ WeatherData 创建失败: {e}")

# 测试 Mock LLM Provider
print("\n" + "=" * 60)
print("测试 3: Mock LLM Provider")
print("=" * 60)

async def test_mock_llm():
    try:
        mock_provider = MockLLMProvider()
        result = await mock_provider.call(SYSTEM_PROMPT, "Test prompt")
        result_data = json.loads(result)
        print("✅ Mock LLM Provider 调用成功")
        print(f"   - 响应类型: {type(result_data)}")
        print(f"   - recommendation: {result_data.get('recommendation')}")
        print(f"   - confidence_score: {result_data.get('confidence_score')}")
        print(f"   - risks count: {len(result_data.get('risks', []))}")
        return True
    except Exception as e:
        print(f"❌ Mock LLM Provider 调用失败: {e}")
        return False

# 测试 WeatherAgent
print("\n" + "=" * 60)
print("测试 4: WeatherAgent 分析器")
print("=" * 60)

async def test_weather_agent():
    try:
        weather_data = WeatherData(
            place_name="上海市",
            city="上海",
            current_temp=18.0,
            rain_probability=0.6,
            wind_speed=2.5,
            hourly_temps=[18.0] * 24,
            hourly_rain_probs=[0.6] * 24,
            hourly_winds=[2.5] * 24,
            current_time="2026-01-13 12:30"
        )
        
        agent = get_weather_agent()
        analysis = await agent.analyze(weather_data)
        
        print("✅ WeatherAgent 分析成功")
        print(f"   - recommendation: {analysis.recommendation}")
        print(f"   - summary: {analysis.summary[:50]}...")
        print(f"   - risks: {len(analysis.risks)}")
        print(f"   - suggestions: {len(analysis.suggestions)}")
        print(f"   - confidence_score: {analysis.confidence_score}")
        return True
    except Exception as e:
        print(f"❌ WeatherAgent 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False

# 运行异步测试
async def main():
    await test_mock_llm()
    await test_weather_agent()

asyncio.run(main())

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
