# 🚗 智能出行规划 Agent - 快速开始

## 功能简介

新增的 **智能出行规划 Agent** 是一个基于 AI 的出行决策系统，它能够：

✅ **根据实时天气智能推荐出行方式**
- 地铁、公交、自驾、步行、骑车的可行性评估
- 规避不合理的出行方式选择

✅ **规划最优出行路线**
- 多条路线推荐
- 路线详情（时长、距离、路况等级）

✅ **预测出行时间和路况**
- 建议出发时间
- 预计出行时长
- 实时路况预测和拥堵时段

✅ **分析天气影响**
- 具体天气风险识别
- 出行应对措施建议
- 天气对各种出行方式的影响评估

✅ **个性化出行建议**
- 根据天气条件的携带物品建议
- 穿着和时间规划建议
- 安全注意事项

## 如何使用

### 方式一：网页界面（推荐）

1. **访问出行规划页面**
   - 登录后访问 `http://localhost:8000/travel-planning`
   - 或在导航栏点击 "🚗 出行规划"

2. **填写出行信息**
   ```
   出发地点: 天津和平广场
   目的地: 天津滨河公园
   所在城市: 天津
   ```

3. **（可选）设置更多参数**
   ```
   距离: 10 公里
   预期时长: 30 分钟
   偏好出发时间: 09:00
   ```

4. **选择出行方式偏好**
   - 可以选择多个方式，系统会为每个方式评级

5. **点击"规划出行方案"**
   - 系统自动获取实时天气
   - AI 进行智能分析
   - 显示详细的规划结果

### 方式二：API 调用

```bash
curl -X POST 'http://localhost:8000/api/travel-planning?lat=39.0851&lng=117.1994&city=天津' \
  -H 'Content-Type: application/json' \
  -d '{
    "origin": "天津和平广场",
    "destination": "天津滨河公园",
    "preferred_time": "09:00",
    "preferred_modes": ["subway", "bus"],
    "expected_duration": 30,
    "distance": 10
  }'
```

**Python 示例：**
```python
import httpx
import json

response = httpx.post(
    'http://localhost:8000/api/travel-planning?lat=39.0851&lng=117.1994&city=天津',
    json={
        'origin': '天津和平广场',
        'destination': '天津滨河公园',
        'preferred_time': '09:00',
        'preferred_modes': ['subway', 'bus'],
        'expected_duration': 30,
        'distance': 10
    }
)

result = response.json()
print(json.dumps(result, indent=2, ensure_ascii=False))
```

## 规划结果示例

### 晴天出行
```
首选方式: 🚇 地铁
出行方式评级:
  ✓ 地铁: GO (推荐)
  ✓ 公交: GO (推荐)
  ✓ 自驾: GO (推荐)
  ✓ 步行: GO (推荐)
  ✓ 骑车: GO (推荐)

推荐路线:
  1. 地铁1号线 + 步行 (25分钟, 8.5公里)
  2. 公交快速公交线 (28分钟, 8.5公里)
  
建议出发时间: 08:45
预计出行时长: 25 分钟

路况预测:
  当前路况: 畅通
  拥堵高峰: 08:00-09:00, 17:30-19:00

天气影响: 轻微

出行建议:
  - 天气良好，适合各种出行方式
  - 建议乘坐地铁，最稳定准时
  - 避开 08:00-09:00 高峰时段
```

### 下雨天出行
```
首选方式: 🚇 地铁
出行方式评级:
  ✓ 地铁: GO (推荐)
  ⚠ 公交: CAUTION (谨慎)
  ⚠ 自驾: CAUTION (谨慎)
  ✗ 步行: AVOID (避免)
  ✗ 骑车: AVOID (避免)

天气影响: 显著

具体风险:
  - 高降雨概率 (75%) 影响户外出行
  - 中等风速 (4.5 m/s) 可能导致不适

应对措施:
  - 携带雨具
  - 穿着防水外套
  - 避免步行和骑车
  - 地铁是最优选择

出行建议:
  - 强烈建议乘坐地铁
  - 地铁不受雨水影响，准时可靠
  - 到达地铁站可能需要提前出发
  - 带上手机充电宝，以防延误时间长
```

## 关键特性详解

### 1️⃣ 多出行方式评估

系统评估以下出行方式在当前天气下的可行性：

| 出行方式 | 晴天 | 下雨 | 高温 | 强风 | 严寒 |
|---------|------|------|------|------|------|
| 🚇 地铁 | ✓ GO | ✓ GO | ✓ GO | ✓ GO | ✓ GO |
| 🚌 公交 | ✓ GO | ⚠ CAUTION | ✓ GO | ⚠ CAUTION | ✓ GO |
| 🚗 自驾 | ✓ GO | ⚠ CAUTION | ✓ GO | ⚠ CAUTION | ⚠ CAUTION |
| 🚶 步行 | ✓ GO | ✗ AVOID | ⚠ CAUTION | ⚠ CAUTION | ✗ AVOID |
| 🚲 骑车 | ✓ GO | ✗ AVOID | ⚠ CAUTION | ✗ AVOID | ✗ AVOID |

### 2️⃣ 天气影响分析

系统考虑以下天气因素：
- 🌡️ **温度** - 极端温度影响户外活动
- 🌧️ **降雨** - 高降雨概率限制露天出行
- 💨 **风速** - 强风影响自驾安全和舒适度
- 💧 **湿度** - 辅助出行舒适度评估

### 3️⃣ 路况预测

系统提供以下路况信息：
- 🟢 **Smooth** (畅通) - 无明显拥堵
- 🟡 **Moderate** (适中) - 轻微拥堵
- 🟠 **Congested** (拥堵) - 明显拥堵
- 🔴 **Severe** (严重拥堵) - 严重拥堵

### 4️⃣ 置信度评分

系统为每个规划结果提供 0-100% 的置信度：
- **80-100%** - 高度可信，强烈推荐遵循
- **60-80%** - 较为可信，建议参考
- **40-60%** - 中等可信性，可考虑多个方案
- **<40%** - 低可信性，建议咨询多个信息源

## 测试系统

### 运行测试套件

```bash
cd /path/to/city-gis-platform
python test_travel_planner.py
```

测试包含 4 个场景：
1. 晴天出行
2. 下雨天出行
3. 高温天气
4. 强风天气

## 系统架构

```
Frontend (travel_planning.html)
         ↓
API Route (/api/travel-planning)
         ↓
TravelPlannerAgent
         ↓
WeatherData + TravelPlanningRequest
         ↓
LLM Provider (OpenAI/DeepSeek/Mock)
         ↓
JSON Response → TravelPlanningResponse
         ↓
Return to Frontend
```

## 核心文件

| 文件 | 功能 |
|------|------|
| `app/agents/travel_planner_agent.py` | 出行规划 AI Agent 实现 |
| `app/models/schemas.py` | 数据模型定义 |
| `app/templates/travel_planning.html` | 前端用户界面 |
| `app/main.py` | API 路由和页面路由 |
| `TRAVEL_PLANNER_GUIDE.md` | 详细使用指南 |
| `test_travel_planner.py` | 功能测试套件 |

## 常见问题

**Q: 如何改变首选出行方式？**
A: 在前端表单中点击要选中的出行方式按钮即可。系统会考虑所有选中的方式并评级。

**Q: API 返回置信度很低怎么办？**
A: 这可能意味着：
- 天气数据不完整
- 出行信息不够详细
- 建议参考系统提供的多个路线选项

**Q: 可以离线使用吗？**
A: 不可以。系统需要实时天气数据和 LLM 支持，都需要网络连接。

**Q: 支持哪些城市？**
A: 当前支持：天津、北京、上海、广州、深圳、成都、杭州、南京
可以在 HTML 表单中的城市下拉列表中查看。

**Q: 路况预测有多准确？**
A: 当前基于历史数据和 AI 推理，精度会随着更多真实数据积累而提高。

## 下一步

1. 📖 阅读 [详细使用指南](TRAVEL_PLANNER_GUIDE.md)
2. 🧪 运行 `test_travel_planner.py` 进行测试
3. 🌐 访问 `/travel-planning` 页面尝试规划
4. 📊 查看规划结果中的各个方面的建议

---

**祝您出行愉快！** 🚗✨
