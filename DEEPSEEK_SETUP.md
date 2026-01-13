# City GIS Weather Decision Platform - DeepSeek 集成指南

## 快速开始

### 1. 环境变量配置

已在 `.env` 文件中配置 DeepSeek API：

```env
DEEPSEEK_API_KEY=sk-eb9cc0102999476ca8da718a24eea1d6
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
```

### 2. 启动应用

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. 测试 API

访问 http://127.0.0.1:8000 并在地图上选择地点，点击"生成出行建议"按钮。

## LLM 提供商支持

### 可用提供商

1. **DeepSeek** (推荐)
   - 配置: `LLM_PROVIDER=deepseek`
   - API Key: `DEEPSEEK_API_KEY`
   - 模型: `deepseek-chat`

2. **OpenAI**
   - 配置: `LLM_PROVIDER=openai`
   - API Key: `OPENAI_API_KEY`
   - 模型: `gpt-3.5-turbo` (可配置)

3. **Mock** (开发用)
   - 配置: `LLM_PROVIDER=mock`
   - 返回模拟数据，用于开发和测试

## 切换 LLM 提供商

编辑 `.env` 文件中的 `LLM_PROVIDER` 和相应的 API Key：

```env
# 使用 OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxx...

# 使用 DeepSeek
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxxx...

# 使用 Mock（用于开发）
LLM_PROVIDER=mock
```

## API 端点

### 天气分析 API

```
POST /api/ai_analysis
Content-Type: application/json

{
  "place_id": "p1",
  "place_name": "天津市区",
  "city": "天津"
}
```

响应示例：
```json
{
  "place_id": "p1",
  "place_name": "天津市区",
  "city": "天津",
  "analysis": {
    "recommendation": "GO",
    "summary": "根据天气数据分析，今天适合外出活动。",
    "risks": [
      {
        "risk_type": "RAIN",
        "severity": "LOW",
        "confidence": 0.3,
        "evidence": "降雨概率较低"
      }
    ],
    "suggestions": [
      "建议在上午10点到下午4点外出，避开可能的降雨时段",
      "携带轻薄衣物适应温度变化"
    ],
    "optimal_time": "10:00-16:00",
    "confidence_score": 0.85,
    "reasoning": "综合温度、风速、降雨概率等多个因素，本时段天气适宜户外活动"
  },
  "generated_at": "2026-01-13T12:34:56.789123"
}
```

## 依赖包

- FastAPI - Web 框架
- Uvicorn - ASGI 服务器
- httpx - HTTP 客户端
- pydantic - 数据验证
- APScheduler - 任务调度
- OpenAI - LLM API 客户端
- python-dotenv - 环境变量管理

## 注意事项

1. **API Key 安全**: 不要在版本控制中提交真实的 API Key，使用 `.env` 文件
2. **速率限制**: DeepSeek API 可能有速率限制，请查阅官方文档
3. **响应格式**: API 强制要求 JSON 响应，确保 LLM 模型支持 JSON 模式
4. **超时设置**: 默认超时为 10 秒，可在代码中调整

## 故障排除

### 错误: "DEEPSEEK_API_KEY environment variable is not set"
- 检查 `.env` 文件是否存在且包含有效的 API Key
- 确保运行前已加载 `.env` 文件

### 错误: "Failed to fetch weather"
- 检查网络连接
- 验证 Open-Meteo API 是否可访问

### 错误: "AI analysis failed"
- 检查 DeepSeek API Key 是否有效
- 查看日志中的具体错误信息
- 确保请求的 JSON 格式正确
