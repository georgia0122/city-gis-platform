from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import httpx
from datetime import datetime
from dotenv import load_dotenv
import os

# 加载 .env 文件
load_dotenv()

app = FastAPI(title="City GIS Weather Decision Platform")

# 扩展城市/地点列表
PLACES = [
    {"id": "p1", "name": "天津市区", "lat": 39.0851, "lng": 117.1994, "city": "天津"},
    {"id": "p2", "name": "民园广场", "lat": 39.0649, "lng": 117.1217, "city": "天津"},
    {"id": "p3", "name": "天津机场", "lat": 39.1304, "lng": 117.3592, "city": "天津"},
    {"id": "p4", "name": "北京市区", "lat": 39.9042, "lng": 116.4074, "city": "北京"},
    {"id": "p5", "name": "上海市区", "lat": 31.2304, "lng": 121.4737, "city": "上海"},
    {"id": "p6", "name": "广州市区", "lat": 23.1291, "lng": 113.2644, "city": "广州"},
    {"id": "p7", "name": "深圳市区", "lat": 22.5431, "lng": 114.0579, "city": "深圳"},
    {"id": "p8", "name": "成都市区", "lat": 30.5728, "lng": 104.0668, "city": "成都"},
    {"id": "p9", "name": "杭州市区", "lat": 30.2741, "lng": 120.1551, "city": "杭州"},
    {"id": "p10", "name": "南京市区", "lat": 32.0603, "lng": 118.7969, "city": "南京"},
]

PLACE_BY_ID = {p["id"]: p for p in PLACES}

# 预警数据存储（模拟）
ALERTS = [
    {
        "id": "alert001",
        "type": "暴雨预警",
        "level": "橙色",
        "location": "天津市区",
        "description": "预计未来6小时内部分地区将出现暴雨，累计降雨量50-80毫米。",
        "time": "2026-01-12 08:00",
        "status": "active"
    },
    {
        "id": "alert002",
        "type": "大风预警",
        "level": "黄色",
        "location": "北京市区",
        "description": "预计未来12小时内阵风可达7-8级。",
        "time": "2026-01-12 09:30",
        "status": "active"
    },
    {
        "id": "alert003",
        "type": "高温预警",
        "level": "黄色",
        "location": "上海市区",
        "description": "预计未来3天最高气温将达到35-37℃。",
        "time": "2026-01-11 14:00",
        "status": "expired"
    }
]

# 日报简报存储
daily_brief_text = "系统初始化中，首次简报将在每日凌晨生成。"

PLACE_BY_ID = {p["id"]: p for p in PLACES}

# 定时任务：每天生成日报简报
def generate_daily_brief():
    global daily_brief_text
    now = datetime.now()
    
    # 模拟生成简报内容
    active_alerts = [a for a in ALERTS if a["status"] == "active"]
    alert_summary = f"当前有 {len(active_alerts)} 条活跃预警" if active_alerts else "暂无活跃预警"
    
    brief = f"""
=== 气象决策平台日报简报 ===
生成时间: {now.strftime('%Y-%m-%d %H:%M:%S')}

一、预警概况
{alert_summary}
"""
    
    if active_alerts:
        brief += "\n活跃预警列表:\n"
        for alert in active_alerts[:5]:  # 最多显示5条
            brief += f"  - [{alert['level']}] {alert['type']}: {alert['location']}\n"
    
    brief += f"""
二、城市监控
当前监控城市数量: {len(PLACES)} 个
覆盖区域: 京津冀、长三角、珠三角及成都等重点城市

三、系统状态
服务运行正常，所有API接口响应正常。

四、建议
1. 关注活跃预警区域的天气变化
2. 及时更新出行计划
3. 查看各地点的24小时趋势图获取详细信息

--- 本简报由系统自动生成 ---
"""
    
    daily_brief_text = brief
    print(f"[SCHEDULED] Daily brief generated at {now}")

# 初始化定时任务
scheduler = BackgroundScheduler()
scheduler.add_job(
    generate_daily_brief,
    CronTrigger(hour=0, minute=0),  # 每天凌晨0点执行
    id='daily_brief_job',
    name='Generate daily brief',
    replace_existing=True
)
scheduler.start()

# 启动时生成一次
generate_daily_brief()

# 静态资源（css/js）
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 模板
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # 渲染网页
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    """个人中心页面"""
    return templates.TemplateResponse("profile.html", {"request": request})


@app.get("/api/places")
def get_places():
    return PLACES


@app.get("/api/search_places")
def search_places(q: str = ""):
    """搜索地点：支持按名称或城市搜索"""
    if not q:
        return PLACES
    
    q_lower = q.lower()
    results = [
        p for p in PLACES 
        if q_lower in p["name"].lower() or q_lower in p.get("city", "").lower()
    ]
    return results


@app.get("/alerts", response_class=HTMLResponse)
def alerts_page(request: Request):
    """预警中心页面"""
    return templates.TemplateResponse("alerts.html", {"request": request})


@app.get("/api/alerts")
def get_alerts(status: str = None):
    """获取预警信息"""
    if status:
        return [a for a in ALERTS if a["status"] == status]
    return ALERTS


@app.get("/api/daily_brief")
def get_daily_brief():
    """获取日报简报"""
    return {
        "content": daily_brief_text,
        "generated_at": datetime.now().isoformat()
    }


import httpx
from datetime import datetime

@app.get("/api/weather_hourly")
async def get_weather_hourly(place_id: str):
    place = PLACE_BY_ID.get(place_id)
    if not place:
        return {"error": f"unknown place_id: {place_id}"}

    lat = place["lat"]
    lon = place["lng"]

    # Open-Meteo：未来24小时逐小时预报
    # 使用 hourly: temperature_2m, precipitation_probability, windspeed_10m
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation_probability,windspeed_10m",
        "forecast_days": 2,
        "timezone": "auto",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    rain_probs = hourly.get("precipitation_probability", [])
    winds = hourly.get("windspeed_10m", [])

    # 取接下来24条
    # Open-Meteo 给的是按小时的时间字符串，比如 "2026-01-12T10:00"
    # 我们返回给前端 hours=0..23，同时也把 time 原样带回去，后面你想做更精细显示可用
    n = min(24, len(times), len(temps), len(rain_probs), len(winds))
    times = times[:n]
    temps = temps[:n]
    rain_probs = rain_probs[:n]
    winds = winds[:n]

    # 你的前端现在期望 rain_prob 是 0-1，所以这里把百分比转成 0-1
    rain_prob_01 = [(p or 0) / 100.0 for p in rain_probs]

    return {
        "place_id": place_id,
        "time": times,                      # 新增：真实时间
        "hours": list(range(n)),            # 保持：给图表x轴用
        "temp_c": temps,
        "rain_prob": rain_prob_01,
        "wind_mps": [round(w / 3.6, 1) for w in winds],  # Open-Meteo windspeed_10m 默认 km/h，转 m/s，保留1位小数
        "source": "open-meteo",
        "lat": lat,
        "lng": lon,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
    }



@app.post("/api/ai/travel_advice")
async def travel_advice(payload: dict):
    """
    先做一个“假AI”占位：根据雨概率给建议。
    后面你可以把这里替换成真正的 LLM/Agent 调用。
    """
    rain_prob = float(payload.get("rain_prob", 0.0))
    mode = payload.get("mode", "walk")

    if rain_prob >= 0.7:
        rec = "CAUTION"
        tips = [
            "未来时段降雨概率较高，建议携带雨具。",
            f"优先选择地铁/公交，避免 {mode} 暴露在户外太久。",
        ]
    elif rain_prob >= 0.4:
        rec = "GO"
        tips = [
            "存在一定降雨可能，建议备伞。",
            "尽量避开高风速路段或开阔区域。",
        ]
    else:
        rec = "GO"
        tips = [
            "天气相对稳定，适合外出。",
            "注意体感温度变化，适当增减衣物。",
        ]

    return JSONResponse(
        {
            "recommendation": rec,
            "top_risks": [
                {"risk": "RAIN", "level": "HIGH" if rain_prob >= 0.7 else "LOW", "evidence": f"rain_prob={rain_prob:.2f}"}
            ],
            "actionable_tips": tips,
            "confidence": 0.65,
        }
    )

@app.post("/api/ai_analysis")
async def ai_analysis(payload: dict):
    """
    AI Agent 分析路由
    
    优先使用 AI 分析，失败时自动降级到规则-based 分析
    
    请求体：
    {
        "place_id": "p1",
        "place_name": "天津市区",
        "city": "天津"
    }
    """
    from app.agents.weather_agent import get_weather_agent
    from app.agents.rule_based_analyzer import RuleBasedAnalyzer
    from app.models.schemas import WeatherData
    
    try:
        place_id = payload.get("place_id")
        if not place_id or place_id not in PLACE_BY_ID:
            return JSONResponse(
                {"error": f"Unknown place_id: {place_id}"},
                status_code=400
            )
        
        place = PLACE_BY_ID[place_id]
        
        # 获取最新天气数据
        weather_resp = await fetch_weather_data(place_id)
        if "error" in weather_resp:
            return JSONResponse(weather_resp, status_code=400)
        
        # 构建 WeatherData
        weather_data = WeatherData(
            place_name=place.get("name", "Unknown"),
            city=place.get("city", "Unknown"),
            current_temp=weather_resp.get("temp_c", [20.0])[0],
            rain_probability=weather_resp.get("rain_prob", [0.3])[0],
            wind_speed=weather_resp.get("wind_mps", [3.0])[0],
            hourly_temps=weather_resp.get("temp_c", [20.0] * 24),
            hourly_rain_probs=weather_resp.get("rain_prob", [0.3] * 24),
            hourly_winds=weather_resp.get("wind_mps", [3.0] * 24),
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        
        # 先尝试 AI 分析
        analysis = None
        analysis_method = "rule"  # 默认为规则分析
        
        try:
            agent = get_weather_agent()
            analysis = await agent.analyze(weather_data)
            analysis_method = "ai"  # 标记为 AI 分析
        except Exception as ai_error:
            # AI 失败，记录错误并降级到规则分析
            print(f"[AI Analysis Failed] {str(ai_error)}")
            print(f"[Fallback] Using rule-based analyzer instead")
            
            # 使用规则分析器
            analysis = RuleBasedAnalyzer.analyze(
                place_name=weather_data.place_name,
                city=weather_data.city,
                current_temp=weather_data.current_temp,
                rain_probability=weather_data.rain_probability,
                wind_speed=weather_data.wind_speed,
                hourly_temps=weather_data.hourly_temps,
                hourly_rain_probs=weather_data.hourly_rain_probs,
                hourly_winds=weather_data.hourly_winds
            )
            analysis_method = "rule"
        
        return {
            "place_id": place_id,
            "place_name": place.get("name"),
            "city": place.get("city"),
            "analysis": analysis.dict(),
            "analysis_method": analysis_method,  # 新增：标记分析方法
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"[Error] {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 最后的降级：即使规则分析也失败了，返回基础建议
        return JSONResponse(
            {"error": f"Analysis failed: {str(e)}", "fallback": "basic"},
            status_code=500
        )


async def fetch_weather_data(place_id: str) -> dict:
    """获取天气数据（复用现有逻辑）"""
    place = PLACE_BY_ID.get(place_id)
    if not place:
        return {"error": f"unknown place_id: {place_id}"}
    
    lat = place["lat"]
    lon = place["lng"]
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation_probability,windspeed_10m",
        "forecast_days": 2,
        "timezone": "auto",
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        return {"error": f"Failed to fetch weather: {str(e)}"}
    
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    rain_probs = hourly.get("precipitation_probability", [])
    winds = hourly.get("windspeed_10m", [])
    
    n = min(24, len(times), len(temps), len(rain_probs), len(winds))
    
    return {
        "place_id": place_id,
        "time": times[:n],
        "hours": list(range(n)),
        "temp_c": temps[:n],
        "rain_prob": [(p or 0) / 100.0 for p in rain_probs[:n]],
        "wind_mps": [round(w / 3.6, 1) for w in winds[:n]],
        "source": "open-meteo",
        "lat": lat,
        "lng": lon,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
    }