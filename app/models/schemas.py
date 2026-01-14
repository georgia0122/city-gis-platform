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


class UserCreate(BaseModel):
    """用户注册数据"""
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None


class User(BaseModel):
    """用户信息"""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = False


class UserInDB(User):
    """数据库中的用户"""
    hashed_password: str
