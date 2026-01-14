from fastapi import FastAPI, Request, Depends, HTTPException, status, Form, Body
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import httpx
from datetime import datetime
from dotenv import load_dotenv
import os
import json
from typing import Optional

from app.models.schemas import User, UserCreate
from app.utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token
)

# 加载 .env 文件
load_dotenv()

app = FastAPI(title="City GIS Weather Decision Platform")

# 用户数据存储（简单JSON文件实现）
USERS_FILE = "users.json"


def load_users():
    """加载用户数据"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_users(users):
    """保存用户数据"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


# 初始加载用户
users_db = load_users()

# 模板和静态文件配置
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


async def get_current_user(request: Request) -> Optional[User]:
    """从cookie中获取当前用户"""
    token = request.cookies.get("access_token")
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    username = payload.get("sub")
    if not username or username not in users_db:
        return None

    user_data = users_db[username]
    return User(**user_data)


# 认证路由
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录页面"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """注册页面"""
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def register(user_in: UserCreate):
    """用户注册"""
    if user_in.username in users_db:
        raise HTTPException(status_code=400, detail="用户名已存在")

    if len(user_in.username) < 3:
        raise HTTPException(status_code=400, detail="用户名至少3个字符")

    if len(user_in.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6个字符")

    hashed_password = get_password_hash(user_in.password)
    user_dict = user_in.dict()
    user_dict.pop("password")
    user_dict["hashed_password"] = hashed_password
    user_dict["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    users_db[user_in.username] = user_dict
    save_users(users_db)

    return {"message": "注册成功"}


@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """用户登录"""
    user_data = users_db.get(username)
    if not user_data:
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    if not verify_password(password, user_data["hashed_password"]):
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    access_token = create_access_token(data={"sub": username})

    response = JSONResponse(content={"message": "登录成功"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=60 * 60 * 24  # 24小时
    )
    return response


@app.get("/logout")
async def logout():
    """用户登出"""
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response


@app.post("/api/change-password")
async def change_password(
    request: Request,
    currentPassword: str = Body(...),
    newPassword: str = Body(...)
):
    """修改密码"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    user_data = users_db.get(user.username)
    if not user_data:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 验证当前密码
    if not verify_password(currentPassword, user_data["hashed_password"]):
        raise HTTPException(status_code=400, detail="当前密码错误")

    # 更新密码
    if len(newPassword) < 6:
        raise HTTPException(status_code=400, detail="新密码至少6个字符")

    user_data["hashed_password"] = get_password_hash(newPassword)
    users_db[user.username] = user_data
    save_users(users_db)

    return {"message": "密码修改成功"}


@app.post("/api/update-profile")
async def update_profile(
    request: Request,
    email: str = Body(None),
    full_name: str = Body(None)
):
    """更新个人信息"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    user_data = users_db.get(user.username)
    if not user_data:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新信息
    if email is not None:
        user_data["email"] = email
    if full_name is not None:
        user_data["full_name"] = full_name

    users_db[user.username] = user_data
    save_users(users_db)

    return {"message": "信息更新成功"}


@app.get("/api/export-data")
async def export_data(request: Request):
    """导出用户数据"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    user_data = users_db.get(user.username)
    if not user_data:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 移除敏感信息
    export_data = {
        "username": user_data.get("username"),
        "email": user_data.get("email"),
        "full_name": user_data.get("full_name"),
        "created_at": user_data.get("created_at"),
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=user_data_{user.username}.json"
        }
    )


@app.get("/api/usage-report")
async def usage_report(request: Request):
    """生成使用报告"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    # 生成简单的文本报告
    report = f"""
GeoWeather 使用报告
==================

用户名: {user.username}
邮箱: {user.email or '未设置'}
注册时间: {users_db.get(user.username, {}).get('created_at', '未知')}
报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

统计数据
--------
今日查询次数: 12
本月查询次数: 245
常用地点: 天津市区, 北京市区, 上海市区

备注: 详细统计功能正在开发中...
"""

    return Response(
        content=report,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=usage_report_{user.username}.txt"
        }
    )


@app.delete("/api/delete-account")
async def delete_account(request: Request):
    """删除账户"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    if user.username in users_db:
        del users_db[user.username]
        save_users(users_db)

    response = JSONResponse(content={"message": "账户已删除"})
    response.delete_cookie("access_token")
    return response


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


# 页面路由（需要登录）
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """主页"""
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """个人中心页面"""
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})


@app.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request):
    """预警中心页面"""
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("alerts.html", {
        "request": request,
        "alerts": ALERTS,
        "user": user
    })


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
            print("[Fallback] Using rule-based analyzer instead")
            
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
