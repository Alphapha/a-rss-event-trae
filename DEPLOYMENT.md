# Docker 部署问题解决方法

## 问题：Docker 守护进程未运行

错误信息：
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
```

## 解决方法

### macOS 系统

1. **启动 Docker Desktop**
   - 打开应用程序
   - 找到 Docker Desktop
   - 启动并等待状态变为绿色（运行中）

2. **验证 Docker 是否运行**
   ```bash
   docker --version
   docker ps
   ```

3. **启动服务**
   ```bash
   ./start.sh
   ```

### 如果端口被占用

错误信息：
```
Bind for 0.0.0.0:8000 failed: port is already allocated
```

**解决方法 1：停止占用端口的进程**
```bash
# 查找占用 8000 端口的进程
lsof -ti:8000

# 停止进程
lsof -ti:8000 | xargs kill -9

# 重新启动
./start.sh
```

**解决方法 2：修改端口**
```bash
# 编辑 docker-compose.yml
# 将 ports 从 "8000:8000" 改为 "8080:8000"

# 或者在 .env 文件中添加
PORT=8080
```

## 完整部署流程

1. **确保 Docker Desktop 正在运行**
   - macOS: 打开 Docker Desktop 应用
   - 状态栏图标应为绿色

2. **清理旧容器（如有必要）**
   ```bash
   docker-compose down
   ```

3. **重新构建镜像**
   ```bash
   docker-compose build --no-cache
   ```

4. **启动服务**
   ```bash
   ./start.sh
   ```

5. **验证服务**
   ```bash
   # 查看日志
   docker-compose logs -f
   
   # 运行测试
   python test_api.py
   
   # 访问 API 文档
   open http://localhost:8000/docs
   ```

## 常见问题

### Q1: Docker Desktop 启动失败

**解决方法**:
1. 重启计算机
2. 重新安装 Docker Desktop
3. 检查系统要求（macOS 10.15 或更高版本）

### Q2: 权限错误

**解决方法**:
```bash
# 确保脚本有执行权限
chmod +x start.sh stop.sh

# 或者使用 sudo
sudo ./start.sh
```

### Q3: 网络错误

**解决方法**:
```bash
# 删除网络重新创建
docker-compose down
docker network prune
./start.sh
```

## 替代方案：本地运行

如果 Docker 无法使用，可以本地运行：

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 测试服务
python test_api.py
```

## 联系支持

如遇到其他问题，请查看：
- 完整文档：README.md
- 快速开始：QUICK_START.md
- GitHub Issues: https://github.com/Alphapha/a-rss-event-trae/issues
