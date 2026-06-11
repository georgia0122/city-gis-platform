# City GIS Platform Release Notes

## Release: 2026-06-11

本次发布整理了城市出行 GIS 平台的当前能力、部署方式和发布检查项，方便在 GitHub 上作为版本说明使用。

## 发布摘要

City GIS Platform 是一个面向城市出行与天气决策的 Web 平台，提供地图交互、城市天气监测、AI 智能分析、预警信息、出行规划、用户登录注册、文件上传分析和 AI 助手对话等功能。

本版本重点覆盖：

- 城市地图与天气数据联动展示
- AI 智能助手与对话历史能力
- 文件、图片和文档上传后的智能分析
- 出行规划与天气风险建议
- 预警中心和监测城市管理
- 用户认证、个人资料维护与基础权限流程
- Docker 与本地开发两种运行方式

## 主要功能

### 城市 GIS 与天气决策

- 支持城市搜索与地图定位
- 展示当前城市天气、温度、降雨、紫外线等信息
- 根据天气条件输出出行建议
- 支持预警中心查看当前监测城市和天气风险

### AI 智能分析

- 集成 LLM 分析能力，可结合天气与出行场景生成建议
- 提供规则分析器作为稳定兜底逻辑
- 支持 AI 简报的展开与收起
- 支持 AI 助手对话历史记录

### 文件上传与分析

- 支持上传文件、图片等内容
- 支持对上传内容进行智能识别和摘要分析
- 支持常见文档类型的解析能力

### 用户与个人中心

- 支持注册、登录和退出
- 支持用户资料页面
- 使用本地 JSON 文件保存基础用户信息

### 出行规划

- 支持根据城市、天气和用户输入生成出行建议
- 提供风险等级、注意事项和推荐行动
- 包含独立的出行规划页面和说明文档

## 技术栈

- 后端：FastAPI
- 模板：Jinja2
- 前端：HTML、CSS、JavaScript
- 数据校验：Pydantic
- 定时任务：APScheduler
- HTTP 客户端：httpx
- 图片处理：Pillow
- 文档解析：PyPDF2、python-docx
- 部署：Docker、docker-compose

## 运行方式

### 本地开发

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

访问地址：

```text
http://127.0.0.1:8000
```

### Docker 运行

```bash
docker build -t city-gis-platform .
docker run -p 8000:8000 city-gis-platform
```

或使用：

```bash
docker compose up --build
```

## 环境配置

项目根目录可使用 `.env` 配置外部服务密钥和运行参数。涉及 AI 能力时，请根据实际使用的模型服务配置 API Key。

建议发布前确认：

- `.env` 未提交真实密钥
- 本地测试账号和历史对话数据不包含敏感信息
- 数据库缓存文件不作为正式发布资产上传

## 发布前检查

建议在发布前完成以下检查：

- 应用可以通过 `uvicorn app.main:app --reload` 正常启动
- 首页、登录、注册、个人中心、AI 助手、预警中心和出行规划页面可访问
- 城市搜索和天气展示流程正常
- AI 分析失败时规则分析器可以正常兜底
- 文件上传分析流程可用
- Docker 镜像可以成功构建并运行
- GitHub 仓库不包含真实密钥、隐私数据或临时缓存文件

## 重要文档

- `README.md`：项目文档入口
- `QUICK_START.md`：快速启动指南
- `DOCKER_GUIDE.md`：Docker 部署说明
- `AI_ANALYSIS_GUIDE.md`：AI 分析功能说明
- `FILE_UPLOAD_GUIDE.md`：文件上传分析说明
- `TRAVEL_PLANNER_GUIDE.md`：出行规划说明
- `TEST_REPORT.md`：测试与验收说明

## 已知注意事项

- 当前用户数据主要使用本地文件保存，生产环境建议迁移到正式数据库
- 本地对话历史和缓存文件应根据部署策略单独管理
- 外部天气服务和 AI 服务依赖网络与 API Key，发布环境需提前配置
- 如果部署到公网环境，请补充 HTTPS、日志、备份和访问控制策略

## 推荐 GitHub Release 标题

```text
City GIS Platform Release - 2026-06-11
```

## 推荐 GitHub Release 描述

```text
本版本发布城市出行 GIS 平台当前稳定能力，包括地图天气展示、AI 智能分析、文件上传分析、AI 助手对话历史、预警中心、出行规划和用户认证等功能。支持本地开发运行和 Docker 部署。
```
