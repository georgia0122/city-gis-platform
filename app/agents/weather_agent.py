"""
天气 Agent 分析器
将天气数据转换为 Prompt，调用 LLM，解析响应
"""

import json
from typing import Dict, Any
from app.models.schemas import WeatherData, AgentResponse
from app.utils.llm import get_llm_provider


SYSTEM_PROMPT = """你是一个专业的气象决策分析助手。你的任务是基于实时天气数据，为用户提供科学、可靠的出行建议。

你需要：
1. 分析温度、降雨概率、风速等多维度气象数据
2. 识别潜在的天气风险
3. 给出明确的出行建议（GO/CAUTION/AVOID）
4. 推荐最优出行时间
5. 提供具体可执行的建议

你必须始终返回有效的JSON格式，包含以下字段：
- recommendation: "GO" | "CAUTION" | "AVOID"
- summary: 一句话总结
- risks: 风险数组，每个包含 risk_type, severity, confidence, evidence
- suggestions: 建议数组
- optimal_time: 最优出行时间段，格式如 "10:00-16:00"
- confidence_score: 0-1的置信度
- reasoning: 详细推理过程

风险评估标准：
- 降雨概率 > 70%：HIGH风险
- 降雨概率 50-70%：MEDIUM风险
- 风速 > 8 m/s：HIGH风险
- 风速 5-8 m/s：MEDIUM风险
- 温度过高(>35°C)或过低(<-10°C)：MEDIUM风险"""


PROMPT_TEMPLATE = """基于以下天气数据，请进行详细的出行决策分析：

【地点信息】
地点：{place_name} ({city})
当前时间：{current_time}

【实时天气数据】
当前气温：{current_temp}°C
降雨概率：{rain_probability}%
风速：{wind_speed} m/s

【24小时趋势】
气温变化：{hourly_temps}°C
降雨概率变化：{hourly_rain_probs}%
风速变化：{hourly_winds}m/s

请根据这些数据进行综合分析，并返回JSON格式的建议。"""


class WeatherAgent:
    """天气决策 Agent"""
    
    def __init__(self):
        self.llm_provider = get_llm_provider()
    
    def prepare_prompt(self, weather_data: WeatherData) -> str:
        """将天气数据转换为Prompt"""
        return PROMPT_TEMPLATE.format(
            place_name=weather_data.place_name,
            city=weather_data.city,
            current_time=weather_data.current_time,
            current_temp=round(weather_data.current_temp, 1),
            rain_probability=round(weather_data.rain_probability * 100),
            wind_speed=round(weather_data.wind_speed, 1),
            hourly_temps=", ".join([f"{t:.1f}" for t in weather_data.hourly_temps[:6]]),  # 前6小时
            hourly_rain_probs=", ".join([f"{p*100:.0f}%" for p in weather_data.hourly_rain_probs[:6]]),
            hourly_winds=", ".join([f"{w:.1f}" for w in weather_data.hourly_winds[:6]])
        )
    
    async def analyze(self, weather_data: WeatherData) -> AgentResponse:
        """
        分析天气数据并返回建议
        
        流程：
        1. 数据准备：转换为Prompt
        2. LLM调用：获取AI分析
        3. 响应解析：转换为结构化数据
        4. 返回：AgentResponse对象
        """
        try:
            # 1. 准备Prompt
            user_prompt = self.prepare_prompt(weather_data)
            
            # 2. 调用LLM
            llm_response = await self.llm_provider.call(SYSTEM_PROMPT, user_prompt)
            
            # 3. 解析JSON响应
            response_data = json.loads(llm_response)
            
            # 4. 转换为AgentResponse
            agent_response = AgentResponse(
                recommendation=response_data.get("recommendation", "GO"),
                summary=response_data.get("summary", ""),
                risks=[
                    {
                        "risk_type": r.get("risk_type", "UNKNOWN"),
                        "severity": r.get("severity", "LOW"),
                        "confidence": float(r.get("confidence", 0.5)),
                        "evidence": r.get("evidence", "")
                    }
                    for r in response_data.get("risks", [])
                ],
                suggestions=response_data.get("suggestions", []),
                optimal_time=response_data.get("optimal_time"),
                confidence_score=float(response_data.get("confidence_score", 0.5)),
                reasoning=response_data.get("reasoning", "")
            )
            
            return agent_response
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Weather analysis failed: {str(e)}")


# 全局实例
_agent_instance = None

def get_weather_agent() -> WeatherAgent:
    """获取全局Agent实例"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = WeatherAgent()
    return _agent_instance
