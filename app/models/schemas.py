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
    humidity: Optional[float] = None  # 可选的湿度字段


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

class TransportMode(BaseModel):
    """出行方式评级"""
    name: str  # "subway", "bus", "driving", "walking", "cycling"
    status: str  # "GO", "CAUTION", "AVOID"
    reason: str


class Route(BaseModel):
    """推荐路线"""
    name: str
    duration: int  # 分钟
    distance: float  # 公里
    traffic_level: str  # "smooth", "moderate", "congested", "severe"
    description: str


class TrafficPrediction(BaseModel):
    """路况预测"""
    current_level: str  # "smooth", "moderate", "congested", "severe"
    peak_hours: List[str]  # e.g., ["08:00-09:00", "17:00-19:00"]
    recommendation: str


class WeatherImpact(BaseModel):
    """天气影响分析"""
    overall_impact: str  # "minimal", "moderate", "significant", "severe"
    specific_risks: List[str]
    precautions: List[str]


class TravelPlanningRequest(BaseModel):
    """出行规划请求"""
    origin: str  # 出发地点
    destination: str  # 目的地
    preferred_time: Optional[str] = None  # 偏好出发时间
    preferred_modes: Optional[List[str]] = None  # 偏好出行方式
    expected_duration: Optional[int] = None  # 预期时长（分钟）
    distance: Optional[float] = None  # 距离（公里）


class TravelPlanningResponse(BaseModel):
    """出行规划响应"""
    primary_mode: str  # 首选出行方式
    modes_rating: List[TransportMode]  # 各出行方式评级
    recommended_routes: List[Route]  # 推荐路线
    departure_time: str  # 建议出发时间
    travel_duration: int  # 预计出行时长（分钟）
    traffic_prediction: TrafficPrediction  # 路况预测
    weather_impact: WeatherImpact  # 天气影响
    suggestions: List[str]  # 建议列表
    confidence_score: float  # 置信度