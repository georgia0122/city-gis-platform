from pydantic import BaseModel
from typing import List, Optional


class WeatherData(BaseModel):
    """天气数据输入结构"""
    place_name: str
    city: str
    current_temp: float
    rain_probability: float
    wind_speed: float
    hourly_temps: List[float]
    hourly_rain_probs: List[float]
    hourly_winds: List[float]
    current_time: str


class RiskAssessment(BaseModel):
    """风险评估结构"""
    risk_type: str  # e.g., "RAIN", "WIND", "TEMPERATURE"
    severity: str   # "LOW", "MEDIUM", "HIGH"
    confidence: float
    evidence: str


class AgentResponse(BaseModel):
    """Agent响应结构"""
    recommendation: str  # "GO", "CAUTION", "AVOID"
    summary: str
    risks: List[RiskAssessment]
    suggestions: List[str]
    optimal_time: Optional[str]
    confidence_score: float
    reasoning: str
