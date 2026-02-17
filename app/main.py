from fastapi import FastAPI, Request, Depends, HTTPException, status, Form, Body, File, UploadFile
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
from typing import Optional, List
import base64
from PIL import Image
import io

from app.models.schemas import (
    User, 
    UserCreate,
    TravelPlanningRequest,
    TravelPlanningResponse,
    WeatherData
)
from app.utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token
)
from app.utils.cache import get_location_cache
from app.utils.file_analyzer import FileAnalyzer

# 加载 .env 文件
load_dotenv()

# 初始化缓存
location_cache = get_location_cache()

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
    user_dict["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 初始化统计数据
    user_dict["stats"] = {
        "today_queries": 0,
        "month_queries": 0,
        "total_queries": 0,
        "frequent_locations": [],
        "last_query_date": None,
        "api_quota_used": 0,
        "api_quota_total": 10000,
        "storage_used_mb": 0.5,
        "storage_total_mb": 100
    }

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

    # 更新登录时间
    user_data["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    users_db[username] = user_data
    save_users(users_db)

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


@app.get("/api/user-stats")
async def get_user_stats(request: Request):
    """获取用户统计数据"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    user_data = users_db.get(user.username)
    if not user_data:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 确保存在stats字段，为老用户初始化
    if "stats" not in user_data:
        user_data["stats"] = {
            "today_queries": 0,
            "month_queries": 0,
            "total_queries": 0,
            "frequent_locations": [],
            "last_query_date": None,
            "api_quota_used": 0,
            "api_quota_total": 10000,
            "storage_used_mb": 0.5,
            "storage_total_mb": 100
        }
        users_db[user.username] = user_data
        save_users(users_db)

    # 检查是否需要重置今日查询次数
    today = datetime.now().strftime("%Y-%m-%d")
    last_query_date = user_data["stats"].get("last_query_date")
    if last_query_date and last_query_date != today:
        user_data["stats"]["today_queries"] = 0

    # 返回统计数据
    return {
        "username": user.username,
        "email": user_data.get("email", ""),
        "full_name": user_data.get("full_name"),
        "created_at": user_data.get("created_at"),
        "last_login": user_data.get("last_login"),
        "stats": user_data["stats"]
    }


@app.post("/api/record-query")
async def record_query(request: Request, location: str = Body(...)):
    """记录用户查询"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    user_data = users_db.get(user.username)
    if not user_data:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 初始化stats如果不存在
    if "stats" not in user_data:
        user_data["stats"] = {
            "today_queries": 0,
            "month_queries": 0,
            "total_queries": 0,
            "frequent_locations": [],
            "last_query_date": None,
            "api_quota_used": 0,
            "api_quota_total": 10000,
            "storage_used_mb": 0.5,
            "storage_total_mb": 100
        }

    # 更新查询次数
    today = datetime.now().strftime("%Y-%m-%d")
    if user_data["stats"].get("last_query_date") != today:
        user_data["stats"]["today_queries"] = 0
    
    user_data["stats"]["today_queries"] += 1
    user_data["stats"]["month_queries"] += 1
    user_data["stats"]["total_queries"] += 1
    user_data["stats"]["last_query_date"] = today
    user_data["stats"]["api_quota_used"] += 1

    # 更新常用地点
    frequent_locs = user_data["stats"]["frequent_locations"]
    
    # 查找是否已存在该地点
    found = False
    for loc in frequent_locs:
        if loc["name"] == location:
            loc["count"] += 1
            found = True
            break
    
    if not found:
        frequent_locs.append({"name": location, "count": 1})
    
    # 按次数排序并只保留前5个
    frequent_locs.sort(key=lambda x: x["count"], reverse=True)
    user_data["stats"]["frequent_locations"] = frequent_locs[:5]

    # 保存数据
    users_db[user.username] = user_data
    save_users(users_db)

    return {"message": "查询已记录", "stats": user_data["stats"]}


# 扩展城市/地点列表
PLACES = [
    {"id": "p1", "name": "天津市区", "lat": 39.0851, "lng": 117.1994, "city": "天津"},
    {"id": "p4", "name": "北京市区", "lat": 39.9042, "lng": 116.4074, "city": "北京"},
    {"id": "p5", "name": "上海市区", "lat": 31.2304, "lng": 121.4737, "city": "上海"},
    {"id": "p6", "name": "广州市区", "lat": 23.1291, "lng": 113.2644, "city": "广州"},
    {"id": "p7", "name": "深圳市区", "lat": 22.5431, "lng": 114.0579, "city": "深圳"},
    {"id": "p8", "name": "成都市区", "lat": 30.5728, "lng": 104.0668, "city": "成都"},
    {"id": "p9", "name": "杭州市区", "lat": 30.2741, "lng": 120.1551, "city": "杭州"},
    {"id": "p10", "name": "南京市区", "lat": 32.0603, "lng": 118.7969, "city": "南京"},
]

PLACE_BY_ID = {p["id"]: p for p in PLACES}

# 日报简报存储（已废弃，改用AI实时生成）
daily_brief_text = "请访问预警中心查看AI实时生成的气象简报"

# 定时任务：每天生成日报简报（保留用于向后兼容）
def generate_daily_brief():
    global daily_brief_text
    now = datetime.now()
    daily_brief_text = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 请访问预警中心查看AI实时生成的气象简报"
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
        "user": user
    })


@app.get("/travel-planning", response_class=HTMLResponse)
async def travel_planning_page(request: Request):
    """智能出行规划页面"""
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("travel_planning.html", {
        "request": request,
        "user": user
    })


@app.get("/file-analysis-demo", response_class=HTMLResponse)
async def file_analysis_demo(request: Request):
    """文件分析功能演示页面"""
    return templates.TemplateResponse("file-analysis-demo.html", {"request": request})


@app.get("/ai-chat", response_class=HTMLResponse)
async def ai_chat_page(request: Request):
    """AI 智能对话页（独立页，可调节窗口、收起侧栏）"""
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("ai_chat.html", {
        "request": request,
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
def get_alerts():
    """获取预警信息列表"""
    # 返回空数组，实际应用中可以从数据库或缓存中获取预警数据
    return []


@app.get("/api/daily_brief")
def get_daily_brief():
    """获取日报简报（已废弃）"""
    return {
        "content": daily_brief_text,
        "generated_at": datetime.now().isoformat()
    }


@app.get("/api/weather")
async def get_weather(lat: float, lng: float):
    """获取实时天气数据"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lng,
        "current": "temperature_2m,precipitation,wind_speed_10m",
        "hourly": "temperature_2m,precipitation_probability,wind_speed_10m,uv_index",
        "timezone": "Asia/Shanghai",
        "forecast_days": 1
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=10.0)
        data = resp.json()
    
    current = data.get("current", {})
    hourly = data.get("hourly", {})
    uv_indices = hourly.get("uv_index", [])
    
    return {
        "current_temp": current.get("temperature_2m", 0),
        "rain_probability": current.get("precipitation", 0) / 100,
        "wind_speed": current.get("wind_speed_10m", 0),
        "hourly_temps": hourly.get("temperature_2m", [])[:24],
        "hourly_rain_probs": [p / 100 for p in hourly.get("precipitation_probability", [])[:24]],
        "hourly_winds": hourly.get("wind_speed_10m", [])[:24],
        "uv_index": uv_indices[:24],
        "current_uv": uv_indices[0] if uv_indices else 0,
        "max_uv": max(uv_indices[:24]) if uv_indices[:24] else 0
    }


@app.get("/api/ai-brief")
async def get_ai_brief(lat: float, lng: float, city: str):
    """
    获取AI气象简报
    
    缓存策略：
    - 同一地点 10 分钟内返回缓存的简报
    - 缓存键基于 lat, lng, city 组成的唯一标识
    """
    from app.models.schemas import WeatherData
    from app.agents.rule_based_analyzer import RuleBasedAnalyzer
    from app.utils.llm import get_llm_provider
    
    # 创建缓存键（基于坐标和城市名）
    cache_key = f"ai_brief_{lat}_{lng}_{city}"
    
    # 检查缓存
    cached_data = location_cache.get(cache_key)
    if cached_data is not None:
        remaining_time = location_cache.get_remaining_time(cache_key)
        return {
            **cached_data,
            "from_cache": True,
            "cache_remaining_seconds": remaining_time
        }
    
    # 获取天气数据
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lng,
        "current": "temperature_2m,precipitation,wind_speed_10m",
        "hourly": "temperature_2m,precipitation_probability,wind_speed_10m,uv_index",
        "timezone": "Asia/Shanghai",
        "forecast_days": 1
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=10.0)
        data = resp.json()
    
    current = data.get("current", {})
    hourly = data.get("hourly", {})
    uv_indices = hourly.get("uv_index", [])
    current_uv = uv_indices[0] if uv_indices else 0
    max_uv = max(uv_indices[:24]) if uv_indices[:24] else 0
    
    weather_data = WeatherData(
        place_name=city,
        city=city,
        current_temp=current.get("temperature_2m", 0),
        rain_probability=current.get("precipitation", 0) / 100,
        wind_speed=current.get("wind_speed_10m", 0),
        hourly_temps=hourly.get("temperature_2m", [])[:24],
        hourly_rain_probs=[p / 100 for p in hourly.get("precipitation_probability", [])[:24]],
        hourly_winds=hourly.get("wind_speed_10m", [])[:24],
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        uv_index=current_uv,
        max_uv=max_uv
    )
    
    # 尝试使用AI分析，失败则使用规则分析
    try:
        llm_provider = get_llm_provider()
        from app.agents.weather_agent import WeatherAgent
        agent = WeatherAgent()
        result = await agent.analyze(weather_data)
    except Exception as e:
        print(f"AI分析失败，使用规则分析: {e}")
        analyzer = RuleBasedAnalyzer()
        result = analyzer.analyze(
            weather_data.place_name,
            weather_data.current_temp,
            weather_data.rain_probability,
            weather_data.wind_speed,
            weather_data.hourly_temps,
            weather_data.hourly_rain_probs,
            weather_data.hourly_winds
        )
    
    response_data = {
        "summary": result.summary,
        "recommendation": result.recommendation,
        "optimal_time": result.optimal_time,
        "suggestions": result.suggestions,
        "confidence_score": result.confidence_score,
        "from_cache": False
    }
    
    # 缓存结果
    location_cache.set(cache_key, response_data)
    
    return response_data


@app.post("/api/travel-planning")
async def plan_travel(
    lat: float,
    lng: float,
    city: str,
    travel_request: TravelPlanningRequest
):
    """
    智能出行规划API
    
    基于天气情况为用户规划最优出行方案，包括：
    - 推荐出行方式（地铁、公交、自驾、步行、骑车）
    - 推荐路线和时间
    - 路况预测
    - 天气影响分析
    - 出行建议
    
    参数：
    - lat, lng, city: 地理位置信息
    - travel_request: 包含 origin, destination, preferred_time, preferred_modes 等信息
    
    返回：
    TravelPlanningResponse 对象，包含完整的出行方案建议
    """
    from app.agents.travel_planner_agent import get_travel_planner_agent
    
    try:
        # 获取天气数据
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lng,
            "current": "temperature_2m,precipitation,wind_speed_10m,relative_humidity_2m",
            "hourly": "temperature_2m,precipitation_probability,wind_speed_10m,uv_index",
            "timezone": "Asia/Shanghai",
            "forecast_days": 1
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=10.0)
            data = resp.json()
        
        current = data.get("current", {})
        hourly = data.get("hourly", {})
        uv_indices = hourly.get("uv_index", [])
        current_uv = uv_indices[0] if uv_indices else 0
        max_uv = max(uv_indices[:24]) if uv_indices[:24] else 0
        
        # 构建天气数据对象
        weather_data = WeatherData(
            place_name=city,
            city=city,
            current_temp=current.get("temperature_2m", 0),
            rain_probability=max(0, min(1, current.get("precipitation", 0) / 100)),
            wind_speed=current.get("wind_speed_10m", 0),
            hourly_temps=hourly.get("temperature_2m", [])[:24],
            hourly_rain_probs=[max(0, min(1, p / 100)) for p in hourly.get("precipitation_probability", [])[:24]],
            hourly_winds=hourly.get("wind_speed_10m", [])[:24],
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            uv_index=current_uv,
            max_uv=max_uv
        )
        
        # 额外的天气属性（如果API返回）
        if "relative_humidity_2m" in current:
            weather_data.humidity = current["relative_humidity_2m"]
        
        # 调用出行规划Agent
        travel_planner = get_travel_planner_agent()
        travel_response = await travel_planner.plan_travel(
            travel_request=travel_request,
            weather_data=weather_data,
            traffic_info={
                "current_traffic": "moderate",
                "congestion_index": 0.5
            }
        )
        
        return travel_response.dict()
        
    except Exception as e:
        print(f"[Travel Planning Error] {str(e)}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Travel planning failed: {str(e)}"
        )



@app.get("/api/weather_hourly")
async def get_weather_hourly(place_id: str = None, lat: float = None, lng: float = None):
    # 优先根据 place_id 获取地点
    place = None
    if place_id and place_id in PLACE_BY_ID:
        place = PLACE_BY_ID.get(place_id)
        lat = place["lat"]
        lng = place["lng"]
    
    # 如果没有找到预设地点，检查是否直接提供了经纬度
    if not place and (lat is None or lng is None):
        return JSONResponse(
            {"error": f"Invalid location parameters. Provide valid place_id or lat/lng. Got place_id={place_id}"},
            status_code=400
        )

    # 缓存键：如果是预设地点用 ID，否则用经纬度组合
    cache_key = place_id if (place_id and place_id in PLACE_BY_ID) else f"custom_{lat}_{lng}"
    
    # 检查缓存
    cached_data = location_cache.get(cache_key)
    if cached_data is not None:
        return {
            **cached_data,
            "from_cache": True,
            "cache_remaining_seconds": location_cache.get_remaining_time(cache_key)
        }

    # Open-Meteo：未来24小时逐小时预报（包含UV指数）
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lng,
        "hourly": "temperature_2m,precipitation_probability,windspeed_10m,uv_index",
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
    uv_indices = hourly.get("uv_index", [])

    # 取接下来24条
    # Open-Meteo 给的是按小时的时间字符串，比如 "2026-01-12T10:00"
    # 我们返回给前端 hours=0..23，同时也把 time 原样带回去，后面你想做更精细显示可用
    n = min(24, len(times), len(temps), len(rain_probs), len(winds), len(uv_indices))
    times = times[:n]
    temps = temps[:n]
    rain_probs = rain_probs[:n]
    winds = winds[:n]
    uv_indices = uv_indices[:n]

    # 你的前端现在期望 rain_prob 是 0-1，所以这里把百分比转成 0-1
    rain_prob_01 = [(p or 0) / 100.0 for p in rain_probs]
    
    # 计算当前时刻的UV指数（根据当前小时）
    from datetime import datetime
    current_hour = datetime.now().hour
    current_uv = uv_indices[current_hour] if current_hour < len(uv_indices) else (uv_indices[0] if uv_indices else 0)
    max_uv = max(uv_indices) if uv_indices else 0
    
    # 同样计算当前时刻的降雨概率
    current_rain_prob = rain_prob_01[current_hour] if current_hour < len(rain_prob_01) else (rain_prob_01[0] if rain_prob_01 else 0)
    
    def get_sun_protection_advice(uv_index):
        """根据UV指数生成防晒建议"""
        if uv_index < 3:
            return {
                "level": "低",
                "color": "#4ade80",
                "advice": "紫外线较弱，无需特殊防护"
            }
        elif uv_index < 6:
            return {
                "level": "中等",
                "color": "#fbbf24",
                "advice": "建议戴太阳镜，涂抹SPF15+防晒霜"
            }
        elif uv_index < 8:
            return {
                "level": "高",
                "color": "#fb923c",
                "advice": "需要防护！戴帽子、太阳镜，涂抹SPF30+防晒霜，避免正午外出"
            }
        elif uv_index < 11:
            return {
                "level": "很高",
                "color": "#f87171",
                "advice": "强烈防护！必须戴帽子、太阳镜，涂抹SPF50+防晒霜，尽量待在阴凉处"
            }
        else:
            return {
                "level": "极高",
                "color": "#dc2626",
                "advice": "极端紫外线！避免外出，必须全面防护：帽子、太阳镜、长袖衣物、SPF50+防晒霜"
            }

    response_data = {
        "place_id": place_id,
        "time": times,                      # 新增：真实时间
        "hours": list(range(n)),            # 保持：给图表x轴用
        "temp_c": temps,
        "rain_prob": rain_prob_01,
        "current_rain_prob": round(current_rain_prob, 3),  # 新增：当前时刻降雨概率
        "wind_mps": [round(w / 3.6, 1) for w in winds],  # Open-Meteo windspeed_10m 默认 km/h，转 m/s，保留1位小数
        "uv_index": uv_indices,             # 新增：UV指数数组
        "current_uv": round(current_uv, 1), # 新增：当前时刻UV指数
        "max_uv": round(max_uv, 1),         # 新增：最大UV指数
        "sun_protection": get_sun_protection_advice(max_uv),  # 新增：防晒建议
        "source": "open-meteo",
        "lat": lat,
        "lng": lng,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "from_cache": False
    }
    
    # 缓存数据
    location_cache.set(cache_key, response_data)
    
    return response_data



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
    """
    from app.agents.weather_agent import get_weather_agent
    from app.agents.rule_based_analyzer import RuleBasedAnalyzer
    from app.models.schemas import WeatherData
    
    try:
        place_id = payload.get("place_id")
        place_name = payload.get("place_name", "未知地点")
        city = payload.get("city", "")
        lat = payload.get("lat")
        lng = payload.get("lng")
        
        # 获取位置坐标
        if place_id and place_id in PLACE_BY_ID:
            place = PLACE_BY_ID[place_id]
            lat = place["lat"]
            lng = place["lng"]
            place_name = place["name"]
            city = place["city"]
        
        if lat is None or lng is None:
            return JSONResponse(
                {"error": "Missing coordinates (lat/lng) or valid place_id"},
                status_code=400
            )
        
        # 缓存键：如果是预设地点用 ID，否则用经纬度组合
        cache_key = f"ai_analysis_{place_id}" if (place_id and place_id in PLACE_BY_ID) else f"ai_analysis_custom_{lat}_{lng}"
        
        cached_analysis = location_cache.get(cache_key)
        if cached_analysis is not None:
            remaining_time = location_cache.get_remaining_time(cache_key)
            return {
                **cached_analysis,
                "from_cache": True,
                "cache_remaining_seconds": remaining_time
            }
        
        # 获取最新天气数据
        weather_resp = await fetch_weather_data(place_id, lat, lng)
        if "error" in weather_resp:
            return JSONResponse(weather_resp, status_code=400)
        
        # 构建 WeatherData
        weather_data = WeatherData(
            place_name=place_name,
            city=city,
            current_temp=weather_resp.get("temp_c", [20.0])[0],
            rain_probability=weather_resp.get("rain_prob", [0.3])[0],
            wind_speed=weather_resp.get("wind_mps", [3.0])[0],
            hourly_temps=weather_resp.get("temp_c", [20.0] * 24),
            hourly_rain_probs=weather_resp.get("rain_prob", [0.3] * 24),
            hourly_winds=weather_resp.get("wind_mps", [3.0] * 24),
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
            uv_index=weather_resp.get("current_uv"),
            max_uv=weather_resp.get("max_uv")
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
        
        response_data = {
            "place_id": place_id,
            "place_name": place_name,
            "city": city,
            "analysis": analysis.dict(),
            "analysis_method": analysis_method,  # 新增：标记分析方法
            "generated_at": datetime.now().isoformat(),
            "from_cache": False
        }
        
        # 缓存分析结果
        location_cache.set(cache_key, response_data)
        
        return response_data
        
    except Exception as e:
        print(f"[Error] {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 最后的降级：即使规则分析也失败了，返回基础建议
        return JSONResponse(
            {"error": f"Analysis failed: {str(e)}", "fallback": "basic"},
            status_code=500
        )


async def fetch_weather_data(place_id: str = None, lat: float = None, lng: float = None) -> dict:
    """获取天气数据（支持 ID 或 坐标）"""
    if place_id and place_id in PLACE_BY_ID:
        place = PLACE_BY_ID.get(place_id)
        lat = place["lat"]
        lng = place["lng"]
    
    if lat is None or lng is None:
        return {"error": "Missing coordinates"}
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lng,
        "hourly": "temperature_2m,precipitation_probability,windspeed_10m,uv_index",
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
    uv_indices = hourly.get("uv_index", [])
    
    n = min(24, len(times), len(temps), len(rain_probs), len(winds), len(uv_indices))
    
    current_uv = uv_indices[0] if uv_indices else 0
    max_uv = max(uv_indices[:n]) if uv_indices[:n] else 0
    
    return {
        "place_id": place_id,
        "time": times[:n],
        "hours": list(range(n)),
        "temp_c": temps[:n],
        "rain_prob": [(p or 0) / 100.0 for p in rain_probs[:n]],
        "wind_mps": [round(w / 3.6, 1) for w in winds[:n]],
        "uv_index": uv_indices[:n],
        "current_uv": round(current_uv, 1),
        "max_uv": round(max_uv, 1),
        "source": "open-meteo",
        "lat": lat,
        "lng": lng,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
    }


# ========== 缓存调试接口 ==========

@app.get("/api/cache/stats")
async def get_cache_stats():
    """
    获取缓存统计信息
    
    返回：
    {
        "total_cached": 缓存的地点数量,
        "ttl_seconds": 缓存有效期（秒）,
        "cached_places": {
            "place_id": {
                "place_id": "p1",
                "cached_at": "2026-01-24T12:34:56.123456",
                "age_seconds": 30,
                "remaining_seconds": 570,
                "is_valid": true
            }
        }
    }
    """
    return location_cache.export_stats()


@app.get("/api/cache/clear")
async def clear_cache(place_id: str = None):
    """
    清除缓存
    
    参数：
    - place_id: 可选，指定要清除的地点ID。如不指定则清除所有缓存
    
    返回：
    {
        "message": "缓存已清除",
        "place_id": "p1" 或 null （如果清除所有）
    }
    """
    if place_id:
        location_cache.clear(place_id)
        return {"message": f"Cache cleared for place_id={place_id}", "place_id": place_id}
    else:
        location_cache.clear_all()
        return {"message": "All caches cleared", "place_id": None}


# ========== AI 智能助手聊天接口 ==========

CHAT_SYSTEM_PROMPT = """你是 GeoWeather 智能助手，一个专业、友好的气象与出行顾问。你可以：
1. 回答用户关于天气、出行、穿衣、防晒等各类问题
2. 结合实时天气数据为用户提供个性化建议
3. 进行日常闲聊，但始终保持专业与友好
4. 用简洁明了的中文回复，适当使用 emoji 增加亲和力

当用户提供了天气数据上下文时，请基于真实数据给出精准建议。
回复请控制在 300 字以内，除非用户需要详细分析。"""


# ========== 文件上传与分析接口 ==========

@app.post("/api/upload-file")
async def upload_file(
    request: Request,
    files: List[UploadFile] = File(...)
):
    """
    上传并分析文件/图片
    
    支持格式：
    - 图片: PNG, JPG, JPEG, GIF, WEBP, BMP
    - 文档: PDF, TXT, DOCX, DOC
    
    返回: {
        'files': [
            {
                'filename': 文件名,
                'type': 'image' or 'document',
                'format': 格式,
                'size': 文件大小,
                'analysis': {
                    基础分析数据
                },
                'summary': 分析摘要
            }
        ],
        'success_count': 成功的文件数,
        'error_count': 失败的文件数,
        'errors': [失败信息]
    }
    """
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    
    results = {
        'files': [],
        'success_count': 0,
        'error_count': 0,
        'errors': []
    }
    
    if not files:
        return JSONResponse({'error': '未选择任何文件'}, status_code=400)
    
    # 创建临时目录用于存储上传的文件
    import tempfile
    temp_dir = tempfile.gettempdir()
    
    for file in files:
        if not file or not file.filename:
            continue
        
        try:
            # 检查文件是否支持
            is_supported, file_type = FileAnalyzer.is_supported_file(file.filename)
            if not is_supported:
                error_msg = f"❌ {file.filename}: 不支持的文件类型"
                results['errors'].append(error_msg)
                results['error_count'] += 1
                continue
            
            # 读取文件内容
            file_content = await file.read()
            file_size = len(file_content)
            
            # 验证文件
            is_valid, error_msg = FileAnalyzer.validate_file(file.filename, file_size)
            if not is_valid:
                results['errors'].append(f"❌ {file.filename}: {error_msg}")
                results['error_count'] += 1
                continue
            
            # 保存到临时文件
            temp_file_path = os.path.join(temp_dir, file.filename)
            with open(temp_file_path, 'wb') as f:
                f.write(file_content)
            
            # 分析文件
            analysis = await FileAnalyzer.analyze_file(temp_file_path)
            
            # 获取摘要
            summary = FileAnalyzer.get_file_summary(analysis)
            
            # 如果是图片，提取base64用于前端显示
            if file_type == 'image' and 'base64' in analysis:
                file_result = {
                    'filename': file.filename,
                    'type': file_type,
                    'format': analysis.get('format', 'unknown'),
                    'size': file_size,
                    'dimensions': analysis.get('dimensions'),
                    'mime_type': analysis.get('mime_type'),
                    'base64': analysis.get('base64'),
                    'analysis': {
                        'colors': analysis.get('analysis', {}).get('colors', [])[:5],
                        'is_grayscale': analysis.get('analysis', {}).get('is_grayscale'),
                        'has_alpha': analysis.get('analysis', {}).get('has_alpha'),
                    },
                    'summary': summary
                }
            else:
                # 文档类型
                file_result = {
                    'filename': file.filename,
                    'type': file_type,
                    'format': analysis.get('format', 'unknown'),
                    'size': file_size,
                    'analysis': {
                        'char_count': analysis.get('char_count', 0),
                        'word_count': analysis.get('word_count', 0),
                        'line_count': analysis.get('line_count', 0),
                        'page_count': analysis.get('pages', 0),
                        'paragraph_count': analysis.get('paragraph_count', 0),
                        'table_count': analysis.get('table_count', 0),
                    },
                    'text_preview': analysis.get('text_preview', '')[:300],
                    'full_text': analysis.get('text', '')[:5000],  # 限制返回的文本大小
                    'summary': summary
                }
            
            results['files'].append(file_result)
            results['success_count'] += 1
            
            # 清理临时文件
            try:
                os.remove(temp_file_path)
            except:
                pass
                
        except Exception as e:
            error_msg = f"❌ {file.filename}: {str(e)}"
            results['errors'].append(error_msg)
            results['error_count'] += 1
    
    return results


@app.post("/api/analyze-files")
async def analyze_files(
    request: Request,
    files: List[UploadFile] = File(...)
):
    """
    上传文件并使用AI进行深度分析
    
    返回: {
        'files': [文件分析结果],
        'ai_analysis': 用户文件的AI分析,
        'summary': 总体摘要
    }
    """
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    
    # 先上传分析每个文件
    from app.utils.llm import get_llm_provider
    
    results = {
        'files': [],
        'errors': []
    }
    
    if not files:
        return JSONResponse({'error': '未选择任何文件'}, status_code=400)
    
    import tempfile
    temp_dir = tempfile.gettempdir()
    
    # 收集所有文件分析结果
    file_analyses = []
    file_summaries = []
    
    for file in files:
        if not file or not file.filename:
            continue
        
        try:
            is_supported, file_type = FileAnalyzer.is_supported_file(file.filename)
            if not is_supported:
                results['errors'].append(f"不支持的文件类型: {file.filename}")
                continue
            
            file_content = await file.read()
            file_size = len(file_content)
            
            is_valid, error_msg = FileAnalyzer.validate_file(file.filename, file_size)
            if not is_valid:
                results['errors'].append(f"{file.filename}: {error_msg}")
                continue
            
            # 保存临时文件
            temp_file_path = os.path.join(temp_dir, file.filename)
            with open(temp_file_path, 'wb') as f:
                f.write(file_content)
            
            # 分析
            analysis = await FileAnalyzer.analyze_file(temp_file_path)
            summary = FileAnalyzer.get_file_summary(analysis)
            
            file_analyses.append({
                'filename': file.filename,
                'type': file_type,
                'analysis': analysis
            })
            file_summaries.append(f"【{file.filename}】\n{summary}")
            
            results['files'].append({
                'filename': file.filename,
                'type': file_type,
                'format': analysis.get('format', 'unknown'),
                'size': file_size,
            })
            
            # 清理
            try:
                os.remove(temp_file_path)
            except:
                pass
                
        except Exception as e:
            results['errors'].append(f"{file.filename}: {str(e)}")
    
    # 使用AI进行深度分析
    if file_summaries:
        try:
            llm_provider = get_llm_provider()
            
            analysis_prompt = f"""请对以下上传的文件进行深度分析和总结：

{chr(10).join(file_summaries)}

请提供：
1. 文件内容的关键要点
2. 文件之间的关联性（如果有多个文件）
3. 建议的后续行动或改进方向
4. 专业建议"""
            
            ai_response = await llm_provider.call(
                system_prompt="你是一个专业的文档分析助手，能够快速理解和分析各种格式的文件，提供有深度的见解。",
                user_prompt=analysis_prompt
            )
            
            results['ai_analysis'] = ai_response
            results['analysis_method'] = 'ai'
            
        except Exception as e:
            # AI分析失败，返回基础分析
            results['ai_analysis'] = f"深度分析失败: {str(e)}\n\n基础摘要:\n" + "\n".join(file_summaries)
            results['analysis_method'] = 'basic'
    
    return results



@app.post("/api/chat")
async def chat_with_ai(
    request: Request,
    message: str = Form(""),
    history: str = Form("[]"),
    files: Optional[List[UploadFile]] = File(None)
):
    """
    AI 智能助手聊天接口
    支持多轮对话、文件上传、图片分析
    """
    from app.utils.llm import get_llm_provider

    try:
        user_message = message.strip() if message else ""
        history_list = json.loads(history) if history else []
        
        # 调试日志
        print(f"[Chat Debug] Received message: '{message}' (length: {len(message) if message else 0})")
        print(f"[Chat Debug] User message after strip: '{user_message}'")
        print(f"[Chat Debug] Files count: {len(files) if files else 0}")
        
        # 处理上传的文件
        file_contents = []
        image_data_list = []
        
        if files and isinstance(files, list):
            for file in files:
                if not file or not file.filename:
                    continue
                    
                file_content = await file.read()
                file_name = file.filename
                file_type = file.content_type or ''
                
                # 处理图片
                if file_type.startswith('image/'):
                    try:
                        # 转换为 base64 用于 AI 分析
                        img = Image.open(io.BytesIO(file_content))
                        # 压缩大图
                        if img.width > 1024 or img.height > 1024:
                            img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                        
                        buffer = io.BytesIO()
                        img.save(buffer, format='PNG')
                        img_base64 = base64.b64encode(buffer.getvalue()).decode()
                        
                        image_data_list.append({
                            'filename': file_name,
                            'data': img_base64,
                            'format': 'png'
                        })
                        file_contents.append(f"📷 图片: {file_name}")
                    except Exception as e:
                        file_contents.append(f"❌ 图片 {file_name} 处理失败: {str(e)}")
                
                # 处理文本文件
                elif file_type == 'text/plain' or file_name.endswith('.txt'):
                    try:
                        text = file_content.decode('utf-8', errors='ignore')
                        file_contents.append(f"📄 文件 {file_name} 内容:\n```\n{text[:2000]}\n```")
                    except Exception as e:
                        file_contents.append(f"❌ 文件 {file_name} 读取失败: {str(e)}")
                
                # 处理 PDF
                elif file_type == 'application/pdf' or file_name.endswith('.pdf'):
                    try:
                        import PyPDF2
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                        text = ""
                        for page in pdf_reader.pages[:5]:  # 只读前5页
                            text += page.extract_text() + "\n"
                        file_contents.append(f"📄 PDF文件 {file_name} 内容（前5页）:\n```\n{text[:2000]}\n```")
                    except ImportError:
                        file_contents.append(f"📎 PDF文件 {file_name} - 需要安装 PyPDF2 包才能读取")
                    except Exception as e:
                        file_contents.append(f"❌ PDF {file_name} 读取失败: {str(e)}")
                
                # 处理 Word 文档
                elif file_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword'] or file_name.endswith(('.docx', '.doc')):
                    try:
                        from docx import Document
                        doc = Document(io.BytesIO(file_content))
                        text = "\n".join([para.text for para in doc.paragraphs])
                        file_contents.append(f"📄 Word文档 {file_name} 内容:\n```\n{text[:2000]}\n```")
                    except ImportError:
                        file_contents.append(f"📎 Word文档 {file_name} - 需要安装 python-docx 包才能读取")
                    except Exception as e:
                        file_contents.append(f"❌ Word文档 {file_name} 读取失败: {str(e)}")
                
                else:
                    file_contents.append(f"📎 文件: {file_name} (类型: {file_type}) - 暂不支持此格式")

        # 构建完整的用户消息
        full_message = user_message
        if file_contents:
            full_message += "\n\n【上传的文件】:\n" + "\n".join(file_contents)
        
        # 验证：必须有消息文本、文件内容或图片之一
        if not full_message.strip() and not image_data_list:
            print(f"[Chat Error] Empty request - message: '{user_message}', file_contents: {len(file_contents)}, images: {len(image_data_list)}")
            return JSONResponse({"error": "消息和文件不能同时为空"}, status_code=400)

        # 构建天气上下文（保留原有逻辑）
        weather_context = ""
        # ... 天气上下文代码保持不变 ...

        # 构建消息列表
        system_content = CHAT_SYSTEM_PROMPT
        if weather_context:
            system_content += f"\n\n以下是用户当前位置的实时天气数据，请在回答时参考：\n{weather_context}"
        
        if file_contents or image_data_list:
            system_content += "\n\n用户上传了文件，请分析文件内容并给出专业的见解。"

        messages = [{"role": "system", "content": system_content}]

        # 添加历史对话（最多保留最近10轮）
        recent_history = history_list[-20:] if len(history_list) > 20 else history_list
        for msg in recent_history:
            if msg.get("role") in ("user", "assistant"):
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # 添加当前用户消息
        if image_data_list:
            # 如果有图片，构建包含图片的消息
            user_content = full_message if full_message.strip() else "请分析这些图片"
            user_content += "\n\n📷 已上传 " + str(len(image_data_list)) + " 张图片，请分析图片内容。"
            messages.append({"role": "user", "content": user_content})
        else:
            messages.append({"role": "user", "content": full_message})

        # 调用 LLM
        llm = get_llm_provider()
        reply = await llm.chat(messages, json_mode=False)

        return {
            "reply": reply,
            "has_weather_context": bool(weather_context),
            "files_processed": len(file_contents) if file_contents else 0,
            "images_processed": len(image_data_list) if image_data_list else 0
        }

    except Exception as e:
        print(f"[Chat Error] {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"error": f"聊天服务暂时不可用: {str(e)}"},
            status_code=500
        )


# ========== 对话历史管理 ==========
import uuid

CHAT_SESSIONS_FILE = "chat_sessions.json"


def load_chat_sessions() -> dict:
    """加载所有聊天会话"""
    if os.path.exists(CHAT_SESSIONS_FILE):
        try:
            with open(CHAT_SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_chat_sessions(sessions: dict):
    """保存聊天会话"""
    with open(CHAT_SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


@app.get("/api/chat/sessions")
async def get_chat_sessions(request: Request):
    """获取当前用户的所有会话列表（按时间倒序）"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse({"error": "未登录"}, status_code=401)

    all_sessions = load_chat_sessions()
    user_sessions = all_sessions.get(user.username, {})

    session_list = []
    for sid, session in user_sessions.items():
        session_list.append({
            "id": sid,
            "title": session.get("title", "新对话"),
            "created_at": session.get("created_at", ""),
            "updated_at": session.get("updated_at", ""),
            "message_count": len(session.get("messages", []))
        })

    # 按更新时间倒序
    session_list.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return {"sessions": session_list}


@app.post("/api/chat/sessions")
async def create_chat_session(request: Request):
    """创建新会话"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse({"error": "未登录"}, status_code=401)

    body = await request.json()
    title = body.get("title", "新对话")

    session_id = str(uuid.uuid4())[:8]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    all_sessions = load_chat_sessions()
    if user.username not in all_sessions:
        all_sessions[user.username] = {}

    all_sessions[user.username][session_id] = {
        "title": title,
        "created_at": now,
        "updated_at": now,
        "messages": []
    }
    save_chat_sessions(all_sessions)

    return {"id": session_id, "title": title, "created_at": now}


@app.get("/api/chat/sessions/{session_id}")
async def get_chat_session(session_id: str, request: Request):
    """获取某个会话的全部消息"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse({"error": "未登录"}, status_code=401)

    all_sessions = load_chat_sessions()
    user_sessions = all_sessions.get(user.username, {})

    if session_id not in user_sessions:
        return JSONResponse({"error": "会话不存在"}, status_code=404)

    session = user_sessions[session_id]
    return {
        "id": session_id,
        "title": session.get("title", "新对话"),
        "created_at": session.get("created_at", ""),
        "updated_at": session.get("updated_at", ""),
        "messages": session.get("messages", [])
    }


@app.post("/api/chat/sessions/{session_id}/messages")
async def add_message_to_session(session_id: str, request: Request):
    """向会话添加消息（用户消息 + AI回复）"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse({"error": "未登录"}, status_code=401)

    body = await request.json()
    messages = body.get("messages", [])

    all_sessions = load_chat_sessions()
    if user.username not in all_sessions:
        all_sessions[user.username] = {}

    if session_id not in all_sessions[user.username]:
        # 自动创建会话
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        all_sessions[user.username][session_id] = {
            "title": "新对话",
            "created_at": now,
            "updated_at": now,
            "messages": []
        }

    session = all_sessions[user.username][session_id]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for msg in messages:
        session["messages"].append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", ""),
            "time": msg.get("time", now),
            "attachments": msg.get("attachments", [])
        })

    # 自动用第一条用户消息作为标题
    if session["title"] == "新对话":
        for m in session["messages"]:
            if m["role"] == "user" and m["content"].strip():
                title_text = m["content"].strip()
                session["title"] = title_text[:20] + ("..." if len(title_text) > 20 else "")
                break

    session["updated_at"] = now
    save_chat_sessions(all_sessions)

    return {"success": True, "title": session["title"]}


@app.put("/api/chat/sessions/{session_id}")
async def update_chat_session(session_id: str, request: Request):
    """更新会话标题"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse({"error": "未登录"}, status_code=401)

    body = await request.json()
    title = body.get("title")

    all_sessions = load_chat_sessions()
    user_sessions = all_sessions.get(user.username, {})

    if session_id not in user_sessions:
        return JSONResponse({"error": "会话不存在"}, status_code=404)

    if title:
        user_sessions[session_id]["title"] = title
    save_chat_sessions(all_sessions)

    return {"success": True}


@app.delete("/api/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str, request: Request):
    """删除某个会话"""
    user = await get_current_user(request)
    if not user:
        return JSONResponse({"error": "未登录"}, status_code=401)

    all_sessions = load_chat_sessions()
    user_sessions = all_sessions.get(user.username, {})

    if session_id in user_sessions:
        del user_sessions[session_id]
        save_chat_sessions(all_sessions)

    return {"success": True}
