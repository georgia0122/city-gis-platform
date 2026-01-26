"""
出行规划 Agent 分析器
基于天气情况智能规划出行方式、路线、时间和路况
支持地铁、公交、自驾、步行等多种出行方式
"""

import json
from typing import List, Optional
from app.models.schemas import WeatherData, TravelPlanningRequest, TravelPlanningResponse, TransportMode
from app.utils.llm import get_llm_provider


SYSTEM_PROMPT = """你是一个专业的智能出行规划助手。你的任务是基于实时天气数据和用户出行需求，为用户提供最优的出行方案。

你需要：
1. 分析天气条件（温度、降雨、风速等）
2. 评估各种出行方式的可行性（地铁、公交、自驾、步行、骑车）
3. 根据天气情况推荐最合理的出行方式
4. 规划具体的出行路线和时间
5. 预测路况信息和出行时长
6. 提供应对恶劣天气的建议

出行方式选择标准：
- GO（推荐）: 天气条件良好，该出行方式可正常使用
- CAUTION（谨慎）: 天气条件一般，该出行方式可用但需注意
- AVOID（避免）: 天气条件恶劣，不建议使用该出行方式
  * 降雨概率 > 80% 且风速 > 6 m/s：避免步行、骑车、自驾
  * 降雨概率 > 70%：避免开放式交通（步行、骑车）
  * 风速 > 10 m/s：避免自驾
  * 温度 < -10°C 或 > 40°C：避免步行和骑车
  * 地铁和公交基本不受天气影响

你必须始终返回有效的JSON格式，包含以下字段：
- primary_mode: 首选出行方式（"subway", "bus", "driving", "walking", "cycling"）
- modes_rating: 各出行方式评级
  * 每个mode包含: name, status ("GO"/"CAUTION"/"AVOID"), reason
- recommended_routes: 推荐路线数组
  * 每条路线包含: name, duration, distance, traffic_level, description
- departure_time: 建议出发时间，格式如 "09:00"
- travel_duration: 预计出行时长，单位分钟
- traffic_prediction: 路况预测
  * 包含: current_level ("smooth"/"moderate"/"congested"/"severe"), peak_hours, recommendation
- weather_impact: 天气影响分析
  * 包含: overall_impact, specific_risks, precautions
- suggestions: 建议数组
- confidence_score: 0-1的置信度"""


PROMPT_TEMPLATE = """基于以下信息，请为用户规划最优出行方案：

【用户出行需求】
出发地点：{origin}
目的地：{destination}
出发时间：{preferred_time}
出行方式偏好：{preferred_modes}
预计旅程：{expected_duration}分钟
距离：{distance}公里

【地点信息】
地点：{place_name} ({city})
当前时间：{current_time}

【实时天气数据】
当前气温：{current_temp}°C
降雨概率：{rain_probability}%
风速：{wind_speed} m/s
湿度：{humidity}%

【24小时趋势】
气温变化：{hourly_temps}°C
降雨概率变化：{hourly_rain_probs}%
风速变化：{hourly_winds}m/s

【交通信息】
当前路况：{current_traffic}
拥堵指数：{congestion_index}

请根据这些数据进行综合分析，提供详细的出行规划方案，并返回JSON格式的建议。"""


class TravelPlannerAgent:
    """出行规划 Agent"""
    
    def __init__(self):
        self.llm_provider = get_llm_provider()
    
    def prepare_prompt(
        self,
        travel_request: TravelPlanningRequest,
        weather_data: WeatherData,
        traffic_info: Optional[dict] = None
    ) -> str:
        """将出行需求和天气数据转换为Prompt"""
        if traffic_info is None:
            traffic_info = {
                "current_traffic": "moderate",
                "congestion_index": 0.5
            }
        
        # 处理出行方式偏好
        preferred_modes = ", ".join(travel_request.preferred_modes) if travel_request.preferred_modes else "all"
        
        return PROMPT_TEMPLATE.format(
            origin=travel_request.origin,
            destination=travel_request.destination,
            preferred_time=travel_request.preferred_time or "immediately",
            preferred_modes=preferred_modes,
            expected_duration=travel_request.expected_duration or 30,
            distance=travel_request.distance or 10,
            place_name=weather_data.place_name,
            city=weather_data.city,
            current_time=weather_data.current_time,
            current_temp=round(weather_data.current_temp, 1),
            rain_probability=round(weather_data.rain_probability * 100),
            wind_speed=round(weather_data.wind_speed, 1),
            humidity=weather_data.humidity if hasattr(weather_data, 'humidity') else 50,
            hourly_temps=", ".join(
                [f"{t:.1f}" for t in weather_data.hourly_temps[:6]]
            ),
            hourly_rain_probs=", ".join(
                [f"{p*100:.0f}%" for p in weather_data.hourly_rain_probs[:6]]
            ),
            hourly_winds=", ".join(
                [f"{w:.1f}" for w in weather_data.hourly_winds[:6]]
            ),
            current_traffic=traffic_info.get("current_traffic", "moderate"),
            congestion_index=traffic_info.get("congestion_index", 0.5)
        )
    
    async def plan_travel(
        self,
        travel_request: TravelPlanningRequest,
        weather_data: WeatherData,
        traffic_info: Optional[dict] = None
    ) -> TravelPlanningResponse:
        """
        规划出行方案
        
        流程：
        1. 数据准备：转换为Prompt
        2. LLM调用：获取AI规划
        3. 响应解析：转换为结构化数据
        4. 返回：TravelPlanningResponse对象
        """
        try:
            # 1. 准备Prompt
            user_prompt = self.prepare_prompt(travel_request, weather_data, traffic_info)
            
            # 2. 调用LLM
            llm_response = await self.llm_provider.call(
                SYSTEM_PROMPT, user_prompt
            )
            
            # 3. 解析JSON响应
            response_data = json.loads(llm_response)
            
            # 4. 转换为TravelPlanningResponse
            travel_response = TravelPlanningResponse(
                primary_mode=response_data.get("primary_mode", "subway"),
                modes_rating=[
                    {
                        "name": m.get("name", "unknown"),
                        "status": m.get("status", "CAUTION"),
                        "reason": m.get("reason", "")
                    }
                    for m in response_data.get("modes_rating", [])
                ],
                recommended_routes=[
                    {
                        "name": r.get("name", "Route"),
                        "duration": r.get("duration", 30),
                        "distance": r.get("distance", 10),
                        "traffic_level": r.get("traffic_level", "moderate"),
                        "description": r.get("description", "")
                    }
                    for r in response_data.get("recommended_routes", [])
                ],
                departure_time=response_data.get("departure_time", "09:00"),
                travel_duration=response_data.get("travel_duration", 30),
                traffic_prediction={
                    "current_level": response_data.get("traffic_prediction", {}).get("current_level", "moderate"),
                    "peak_hours": response_data.get("traffic_prediction", {}).get("peak_hours", []),
                    "recommendation": response_data.get("traffic_prediction", {}).get("recommendation", "")
                },
                weather_impact={
                    "overall_impact": response_data.get("weather_impact", {}).get("overall_impact", "minimal"),
                    "specific_risks": response_data.get("weather_impact", {}).get("specific_risks", []),
                    "precautions": response_data.get("weather_impact", {}).get("precautions", [])
                },
                suggestions=response_data.get("suggestions", []),
                confidence_score=float(response_data.get("confidence_score", 0.5))
            )
            
            return travel_response
            
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse LLM response as JSON: {str(e)}"
            )
        except Exception as e:
            raise RuntimeError(f"Travel planning failed: {str(e)}")


# 全局实例
_agent_instance = None

def get_travel_planner_agent() -> TravelPlannerAgent:
    """获取全局Travel Planner Agent实例"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = TravelPlannerAgent()
    return _agent_instance
