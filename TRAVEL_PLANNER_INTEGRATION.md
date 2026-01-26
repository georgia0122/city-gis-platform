# 🚗 智能出行规划 Agent 集成说明

## 概述

本文档说明如何在 City GIS Weather Decision Platform 中集成和使用新增的智能出行规划 Agent。

## 新增文件

### 1. 核心 Agent
```
app/agents/travel_planner_agent.py
- TravelPlannerAgent 类：主要的出行规划逻辑
- get_travel_planner_agent() 函数：全局实例获取
```

**功能：**
- 准备规划 prompt
- 调用 LLM 进行智能分析
- 解析和返回规划结果

### 2. 数据模型（已扩展）
```
app/models/schemas.py
- WeatherData（已扩展，新增 humidity 字段）
- TravelPlanningRequest：规划请求参数
- TravelPlanningResponse：规划响应结果
- TransportMode：出行方式评级
- Route：推荐路线
- TrafficPrediction：路况预测
- WeatherImpact：天气影响分析
```

### 3. 前端界面
```
app/templates/travel_planning.html
- 完整的出行规划页面
- 表单输入、结果展示、交互功能
```

### 4. API 路由（已扩展）
```
app/main.py
- GET /travel-planning - 页面路由
- POST /api/travel-planning - API 端点
```

### 5. 测试工具
```
test_travel_planner.py
- 4 个真实场景的测试
- 响应结构验证
```

### 6. 文档
```
TRAVEL_PLANNER_GUIDE.md - 详细使用指南
TRAVEL_PLANNER_QUICKSTART.md - 快速开始指南
TRAVEL_PLANNER_INTEGRATION.md - 集成说明（本文档）
```

## 文件改动汇总

### 修改的文件

#### 1. `app/main.py`
**改动 1：导入新模型**
```python
# 第 22-26 行
from app.models.schemas import (
    User, 
    UserCreate,
    TravelPlanningRequest,
    TravelPlanningResponse,
    WeatherData
)
```

**改动 2：新增页面路由**
```python
# 第 363-371 行
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
```

**改动 3：新增 API 端点**
```python
# 第 511-600 行
@app.post("/api/travel-planning")
async def plan_travel(
    lat: float,
    lng: float,
    city: str,
    travel_request: TravelPlanningRequest
):
    """智能出行规划 API"""
    # 实现代码...
```

#### 2. `app/models/schemas.py`
**改动 1：扩展 WeatherData**
```python
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
    humidity: Optional[float] = None  # 新增
```

**改动 2：新增数据模型类**
```python
# 新增 9 个相关的 Pydantic 模型类
- TransportMode
- Route
- TrafficPrediction
- WeatherImpact
- TravelPlanningRequest
- TravelPlanningResponse
```

## 工作流程

```
用户访问 /travel-planning
         ↓
    填写表单
         ↓
    选择出行方式（可选）
         ↓
    点击"规划出行方案"
         ↓
    前端向 /api/travel-planning 发送 POST 请求
         ↓
API 获取实时天气数据 (Open-Meteo)
         ↓
    创建 WeatherData 对象
         ↓
调用 TravelPlannerAgent.plan_travel()
         ↓
Agent 准备 Prompt 并调用 LLM
         ↓
LLM 返回 JSON 格式的规划方案
         ↓
Agent 解析并返回 TravelPlanningResponse
         ↓
API 返回 JSON 响应给前端
         ↓
前端展示结果
```

## 集成步骤

### 1. 代码复制
```bash
# 复制以下文件到相应目录
cp app/agents/travel_planner_agent.py 你的项目/app/agents/
cp TRAVEL_PLANNER_GUIDE.md 你的项目/
cp TRAVEL_PLANNER_QUICKSTART.md 你的项目/
cp test_travel_planner.py 你的项目/
```

### 2. 更新现有文件

**更新 app/main.py：**
- 更新导入语句（第 22-26 行）
- 新增页面路由（第 363-371 行）
- 新增 API 端点（第 511-600 行）

**更新 app/models/schemas.py：**
- 更新 WeatherData 类
- 新增 7 个数据模型类

**新增 app/templates/travel_planning.html：**
- 复制整个文件

### 3. 验证依赖
```bash
# 确保已安装所需包
pip install fastapi httpx pydantic python-dotenv openai
```

### 4. 配置环境变量
```env
# .env 文件
LLM_PROVIDER=deepseek  # 或 openai, mock
LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=your_key_here
```

### 5. 运行测试
```bash
# 运行集成测试
python test_travel_planner.py

# 输出应该显示：
# ✅ 测试场景 1：晴天出行
# ✅ 测试场景 2：下雨天出行
# ✅ 测试场景 3：高温天气
# ✅ 测试场景 4：强风天气
# ✅ 所有测试完成!
```

### 6. 启动应用
```bash
python -m uvicorn app.main:app --reload
```

### 7. 访问功能
- 登录后访问：`http://localhost:8000/travel-planning`
- 或在导航栏点击"🚗 出行规划"

## 核心概念

### 出行方式评级标准

#### GO（推荐）
- 该出行方式在当前天气条件下是安全、高效的
- 系统强烈推荐使用

#### CAUTION（谨慎）
- 该出行方式在当前天气条件下可用但有限制
- 用户需要采取额外的预防措施
- 可能增加出行时间或不适感

#### AVOID（避免）
- 该出行方式在当前天气条件下不推荐
- 存在安全隐患或显著的不适感
- 建议选择其他出行方式

### 天气影响等级

| 等级 | 说明 | 影响范围 |
|------|------|---------|
| Minimal | 天气对出行几乎无影响 | 可正常使用所有方式 |
| Moderate | 天气对某些方式有影响 | 部分方式受限 |
| Significant | 天气对大多数户外方式有影响 | 地铁/公交优先 |
| Severe | 天气对所有方式都有严重影响 | 考虑延迟出行 |

## 自定义扩展

### 1. 添加新的出行方式

修改 `travel_planner_agent.py` 中的 SYSTEM_PROMPT：
```python
# 在出行方式列表中添加新方式
# 例如：电瓶车、摩托车等
```

### 2. 添加新的天气因素

修改 `main.py` 中的 API 请求参数：
```python
params = {
    "latitude": lat,
    "longitude": lng,
    "current": "temperature_2m,precipitation,wind_speed_10m,relative_humidity_2m,uv_index",  # 添加 uv_index
    # ...
}
```

### 3. 整合真实路况数据

修改 `plan_travel()` 函数中的 `traffic_info` 获取逻辑：
```python
# 从高德/百度地图 API 获取实时路况
# 替换 mock 数据
```

### 4. 实现用户历史记录

添加数据库表存储用户的规划历史：
```sql
CREATE TABLE travel_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    origin VARCHAR(255),
    destination VARCHAR(255),
    plan_result JSON,
    actual_duration INT,
    created_at TIMESTAMP
);
```

## 故障排除

### 问题 1：API 返回 404
**原因：** 路由未正确添加
**解决方案：** 
- 检查 main.py 中的路由定义
- 确认文件已保存
- 重启应用

### 问题 2：LLM 调用失败
**原因：** API Key 配置错误或网络问题
**解决方案：**
- 检查 .env 文件中的 API Key
- 验证网络连接
- 切换到 MockLLMProvider 进行测试

### 问题 3：天气数据为空
**原因：** Open-Meteo API 请求失败
**解决方案：**
- 检查网络连接
- 验证坐标是否正确
- 查看日志中的错误信息

### 问题 4：前端页面加载缓慢
**原因：** 规划请求处理时间长
**解决方案：**
- 设置 LLM 调用超时时间
- 使用缓存机制存储规划结果
- 优化 Prompt 内容

## 性能优化建议

### 1. 缓存规划结果
```python
# 对于相同位置和时间的请求，返回缓存结果
cache_key = f"{origin}_{destination}_{current_hour}"
```

### 2. 异步处理
```python
# 已使用 async/await，确保并发处理
```

### 3. Prompt 优化
```python
# 简化 Prompt，减少 token 使用
# 只包含必要的信息
```

### 4. 批量请求
```python
# 支持一次规划多条路线
# 减少 API 调用次数
```

## 安全考虑

### 1. 输入验证
```python
# 已验证：
# - origin 和 destination 不为空
# - 坐标范围有效
# - 时间格式正确
```

### 2. API 密钥安全
```python
# 使用环境变量存储敏感信息
# 不要在代码中硬编码密钥
```

### 3. 速率限制
```python
# 建议为 API 端点添加速率限制
# 防止滥用
```

## 监控和日志

添加日志记录规划过程：
```python
import logging

logger = logging.getLogger(__name__)

# 在关键步骤记录
logger.info(f"Planning for {origin} to {destination}")
logger.error(f"LLM call failed: {error}")
```

## 性能指标

目标性能指标：
- API 响应时间：< 5 秒
- 规划准确度：> 80%
- 系统可用性：> 99.5%

## 兼容性

- Python 版本：3.8+
- FastAPI 版本：0.104.0+
- 浏览器：现代浏览器（Chrome, Firefox, Safari 等）

## 维护计划

### 每周
- 检查 API 调用日志
- 监控错误率

### 每月
- 更新天气数据源
- 优化 Prompt 策略
- 收集用户反馈

### 每季度
- 性能优化
- 功能迭代
- 文档更新

## 支持和反馈

对于问题、建议或贡献，请：
1. 提交 Issue
2. 创建 Pull Request
3. 联系开发团队

---

**版本：** 1.0.0
**最后更新：** 2026-01-26
**维护者：** City GIS 开发团队
