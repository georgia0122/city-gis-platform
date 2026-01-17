# 🐳 Docker 部署指南

## 文件说明

本项目已 Docker 化，包含以下文件：

- **Dockerfile** - Docker 镜像构建文件
- **docker-compose.yml** - Docker Compose 编排配置
- **.dockerignore** - Docker 构建时忽略的文件列表
- **requirements.txt** - Python 依赖列表

## 快速开始

### 方式一：使用 Docker Compose（推荐）

#### 1. 启动应用
```bash
docker-compose up -d
```

#### 2. 查看应用日志
```bash
docker-compose logs -f web
```

#### 3. 访问应用
- 主页: http://localhost:8000
- 预警中心: http://localhost:8000/alerts
- 个人中心: http://localhost:8000/profile

#### 4. 停止应用
```bash
docker-compose down
```

---

### 方式二：使用 Docker 命令

#### 1. 构建镜像
```bash
docker build -t city-gis-platform:latest .
```

#### 2. 运行容器
```bash
docker run -d \
  --name city-gis-platform \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/users.json:/app/users.json \
  city-gis-platform:latest
```

#### 3. 查看容器日志
```bash
docker logs -f city-gis-platform
```

#### 4. 停止容器
```bash
docker stop city-gis-platform
docker rm city-gis-platform
```

---

## 常用命令

### 查看运行中的容器
```bash
docker-compose ps
```

### 进入容器内部
```bash
docker-compose exec web bash
```

### 重启应用
```bash
docker-compose restart web
```

### 删除所有容器和镜像
```bash
docker-compose down --rmi all
```

### 查看镜像
```bash
docker images | grep city-gis
```

---

## 环境配置

### 自动加载的环境变量
应用会自动从以下位置读取环境变量（优先级从高到低）：
1. `.env` 文件（项目根目录）
2. Docker Compose 配置中的 `env_file`
3. 容器运行时的 `-e` 参数

### 必需的环境变量
```env
DEEPSEEK_API_KEY=your-api-key-here
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
```

### 可选的环境变量
```env
DEBUG=False
PYTHONUNBUFFERED=1
```

---

## 数据持久化

### 用户数据
用户数据存储在 `users.json` 文件中，已通过 Docker Volume 挂载到容器中：
```yaml
volumes:
  - ./users.json:/app/users.json
```

这确保用户数据在容器重启后不会丢失。

---

## 故障排查

### 容器启动失败
```bash
# 查看详细错误日志
docker-compose logs web
```

### 无法连接到应用
- 检查端口是否被占用：`netstat -an | findstr 8000`（Windows）或 `lsof -i :8000`（Mac/Linux）
- 确认容器正在运行：`docker-compose ps`

### API 密钥错误
- 验证 `.env` 文件中的 `DEEPSEEK_API_KEY` 是否正确
- 检查环境变量是否正确传递给容器

### 权限问题
- 确保项目目录及其文件对 Docker 可读/可写
- 如需修改权限：`chmod -R 755 .`

---

## 生产环境部署建议

### 1. 安全性
- 使用 `.env.production` 文件存储生产密钥
- 不要在 Dockerfile 中硬编码敏感信息
- 使用私有镜像仓库存储镜像

### 2. 性能优化
```dockerfile
# 在 Dockerfile 中使用多阶段构建
FROM python:3.11-slim as builder
# ... 构建步骤 ...

FROM python:3.11-slim
# ... 最终步骤 ...
```

### 3. 监控和日志
```yaml
# 在 docker-compose.yml 中配置日志
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 4. 自动重启
应用已配置 `restart: unless-stopped`，容器异常退出时会自动重启。

---

## 更新应用

### 重新构建镜像
```bash
# 如果修改了代码，需要重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 仅重启应用
```bash
# 如果只是重启，不需要重新构建
docker-compose restart web
```

---

## 相关文档
- [快速开始](QUICK_START.md)
- [项目完成清单](PROJECT_COMPLETION.md)
- [系统验证](SYSTEM_VERIFICATION.md)
