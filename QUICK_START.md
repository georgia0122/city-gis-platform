# 🚀 快速开始指南

## 系统状态检查

### ✅ 已实现的功能

1. **双层分析系统**
   - ✅ AI 分析（DeepSeek）- 优先级最高
   - ✅ 规则分析器 - 自动降级
   - ✅ 错误恢复机制

2. **改进的 UI 布局**
   - ✅ 出行建议顶部显示（最重要的信息）
   - ✅ 最佳时间段突出显示
   - ✅ 分析方法和置信度标注
   - ✅ 结构化的建议和风险显示

3. **天气数据获取**
   - ✅ Open-Meteo API 集成
   - ✅ 24 小时逐小时预报
   - ✅ 自动单位转换（km/h → m/s）

4. **规则分析器**
   - ✅ 温度风险评估
   - ✅ 降雨风险评估  
   - ✅ 风速风险评估
   - ✅ 最佳时间计算
   - ✅ 个性化建议生成

5. **出行页面**
   - ✅ 城市搜索（10 个预设 + 全球 Nominatim）
   - ✅ 预警中心
   - ✅ 个人中心
   - ✅ 地图交互

## 运行方式

### 启动应用
```bash
cd c:\Users\yoyo\Desktop\city-gis-platform
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 访问应用
- 主页: http://127.0.0.1:8000
- 预警中心: http://127.0.0.1:8000/alerts
- 个人中心: http://127.0.0.1:8000/profile

## 使用流程

1. **打开应用** → 访问 http://127.0.0.1:8000
2. **选择地点** → 点击地图或使用搜索
3. **查看天气** → 实时数据显示在地图下方
4. **生成建议** → 点击"生成出行建议"按钮
5. **查看分析** → AI 分析或规则分析结果显示

## 输出示例

### 当点击"生成出行建议"时：

```
✅ 出行建议: GO (AI 已降级)
⏰ 最佳时间段: 10:00-16:00
✅ 分析方法: 📊 规则分析 | 置信度: 75%

📝 评价: 适合外出。天津市今日天气相对良好，降雨概率30%，风速3.5m/s，气温18°C。

💡 行动建议:
   1. 建议在上午10点到下午4点外出
   2. 携带轻薄衣物适应温度变化

⚠️ 风险评估:
   🟢 降雨 (LOW)
      └─ 降雨概率仅 30%
   🟢 风速 (LOW)
      └─ 风速温和 3.5 m/s
```

## 常见问题

### Q: 为什么显示"AI 已降级"？
**A**: DeepSeek API 余额不足或网络问题，系统自动使用规则分析器。这是正常现象，仍能提供准确的出行建议。

### Q: 置信度为什么是 75%？
**A**: 规则分析器的置信度固定为 0.75（75%），而 AI 分析可能更高。这反映了不同分析方法的可信程度。

### Q: 怎么添加自己的 AI Key？
**A**: 编辑 `.env` 文件，添加你的 API Key：
```env
DEEPSEEK_API_KEY=你的key
LLM_PROVIDER=deepseek
```

### Q: 支持其他 LLM 吗？
**A**: 当前支持：
- DeepSeek (推荐)
- OpenAI (GPT-3.5 等)
- Mock (本地模拟)

可以在 `app/utils/llm.py` 中添加更多提供商。

## 技术栈

- **后端**: FastAPI + Python 3.12
- **前端**: HTML5 + CSS3 + JavaScript
- **地图**: Leaflet.js
- **图表**: ECharts
- **天气 API**: Open-Meteo (免费)
- **LLM**: DeepSeek API
- **任务调度**: APScheduler

## 文件结构

```
app/
├── main.py                          # 主 FastAPI 应用
├── templates/
│   ├── index.html                   # 地图主页
│   ├── alerts.html                  # 预警中心
│   └── profile.html                 # 个人中心
├── static/
│   ├── css/style.css                # 样式
│   └── js/app.js                    # 前端逻辑
├── agents/
│   ├── weather_agent.py             # AI Agent 分析器
│   └── rule_based_analyzer.py       # 规则分析器
├── models/
│   └── schemas.py                   # Pydantic 数据模型
└── utils/
    └── llm.py                       # LLM 提供商封装
```

## 配置文件

### .env
```env
# LLM 配置
DEEPSEEK_API_KEY=sk-xxxx...
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat

# 应用配置
DEBUG=True
```

## API 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/` | 主页 |
| GET | `/alerts` | 预警中心 |
| GET | `/profile` | 个人中心 |
| GET | `/api/places` | 获取所有预设地点 |
| GET | `/api/weather_hourly` | 获取小时级天气 |
| POST | `/api/ai_analysis` | 获取 AI 分析建议 |

## 监控和日志

### 查看实时日志
```
[AI Analysis Failed] ... → AI 分析失败
[Fallback] Using rule-based analyzer instead → 已降级到规则分析
INFO: ... 200 OK → API 成功
```

### 常见错误
- `402 Insufficient Balance` → DeepSeek 余额不足
- `400 Bad Request` → 请求参数错误
- `500 Internal Server Error` → 服务器错误

## 性能指标

- **地图加载**: 200-500ms
- **天气 API**: 1-2s
- **AI 分析**: 2-5s（DeepSeek）
- **规则分析**: <100ms

## 下一步行动

1. [ ] 添加更多 LLM 提供商支持
2. [ ] 实现用户偏好设置
3. [ ] 添加天气预警推送
4. [ ] 支持历史记录查询
5. [ ] 优化移动端适配
