# 数字孪生与个性化干预系统部署文档

## 1. 环境准备

### 1.1 安装Docker
- **Windows**：下载并安装Docker Desktop for Windows
- **macOS**：下载并安装Docker Desktop for Mac
- **Linux**：使用包管理器安装Docker

### 1.2 安装Minikube（用于本地Kubernetes集群）
- 下载并安装Minikube：https://minikube.sigs.k8s.io/docs/start/
- 安装kubectl：https://kubernetes.io/docs/tasks/tools/

### 1.3 配置Docker Hub账号
- 注册Docker Hub账号：https://hub.docker.com/
- 创建访问令牌：用于GitHub Actions推送镜像

### 1.4 配置GitHub仓库
- 创建GitHub仓库
- 在仓库设置中添加以下Secrets：
  - `DOCKER_HUB_USERNAME`：Docker Hub用户名
  - `DOCKER_HUB_ACCESS_TOKEN`：Docker Hub访问令牌
  - `KUBE_CONFIG`：Kubernetes集群配置文件内容

## 2. Docker容器化部署

### 2.1 构建镜像

1. **前端服务**：
   ```bash
   cd frontend
   docker build -t frontend:latest .
   ```

2. **后端服务**：
   ```bash
   docker build -t backend:latest -f Dockerfile.collector .
   ```

3. **Spark处理器**：
   ```bash
   docker build -t spark-processor:latest -f Dockerfile.spark .
   ```

### 2.2 使用Docker Compose启动所有服务

```bash
docker-compose up -d
```

### 2.3 验证服务

- 前端服务：http://localhost
- 后端服务：http://localhost:8000
- Spark UI：http://localhost:8080
- Prometheus：http://localhost:9090
- Grafana：http://localhost:3000

## 3. Kubernetes部署（使用Minikube）

### 3.1 启动Minikube集群

```bash
minikube start
```

### 3.2 创建命名空间

```bash
kubectl apply -f k8s/namespace.yaml
```

### 3.3 创建持久卷声明

```bash
kubectl apply -f k8s/pvc.yaml
```

### 3.4 部署存储服务和消息队列

```bash
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/influxdb-deployment.yaml
kubectl apply -f k8s/influxdb-service.yaml
kubectl apply -f k8s/zookeeper-deployment.yaml
kubectl apply -f k8s/zookeeper-service.yaml
kubectl apply -f k8s/kafka-deployment.yaml
kubectl apply -f k8s/kafka-service.yaml
```

### 3.5 部署应用服务

```bash
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/spark-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml
```

### 3.6 配置Ingress

1. 启用Minikube的Ingress插件：
   ```bash
   minikube addons enable ingress
   ```

2. 应用Ingress配置：
   ```bash
   kubectl apply -f k8s/ingress.yaml
   ```

3. 配置本地域名解析：
   - 在`/etc/hosts`文件中添加以下条目：
     ```
     127.0.0.1 dashboard.local
     127.0.0.1 api.local
     ```

### 3.7 验证Kubernetes部署

- 查看所有服务：
  ```bash
  kubectl get all -n elderly-care
  ```

- 查看Ingress：
  ```bash
  kubectl get ingress -n elderly-care
  ```

- 访问服务：
  - 前端服务：http://dashboard.local
  - 后端服务：http://api.local

## 4. CI/CD流水线配置

### 4.1 配置GitHub Actions

1. 确保`.github/workflows/deploy.yml`文件已正确配置
2. 在GitHub仓库设置中添加必要的Secrets

### 4.2 测试CI/CD流水线

1. 提交代码到main分支
2. 查看GitHub Actions运行状态
3. 验证镜像是否已推送到Docker Hub
4. 验证Kubernetes部署是否已更新

## 5. 服务验证

### 5.1 前端验证

1. 访问http://dashboard.local
2. 登录系统
3. 验证仪表盘数据是否正确显示
4. 验证各功能模块是否正常工作

### 5.2 后端验证

1. 访问http://api.local/health
2. 验证健康检查是否返回正常
3. 测试API接口是否正常响应

### 5.3 数据处理验证

1. 查看Spark UI：http://localhost:8080
2. 验证Spark Streaming任务是否正常运行
3. 检查数据处理日志

### 5.4 存储服务验证

1. 验证Redis连接：
   ```bash
   redis-cli -h localhost -p 6379 ping
   ```

2. 验证PostgreSQL连接：
   ```bash
   psql -h localhost -p 5432 -U admin -d elderly_care
   ```

3. 验证InfluxDB连接：
   ```bash
   influx -t my-super-secret-token -o elderly-care
   ```

### 5.5 消息队列验证

1. 验证Kafka连接：
   ```bash
   kafka-topics.sh --list --bootstrap-server localhost:9092
   ```

## 6. 常见问题及解决方案

### 6.1 Docker相关问题

- **问题**：Docker容器启动失败
  **解决方案**：检查Docker日志，确保端口未被占用，检查环境变量配置

- **问题**：镜像构建失败
  **解决方案**：检查Dockerfile语法，确保依赖安装正确

### 6.2 Kubernetes相关问题

- **问题**：Pod启动失败
  **解决方案**：查看Pod日志，检查资源限制，确保存储卷正确挂载

- **问题**：Ingress无法访问
  **解决方案**：检查Ingress配置，确保Minikube的Ingress插件已启用，检查本地域名解析

### 6.3 CI/CD相关问题

- **问题**：GitHub Actions运行失败
  **解决方案**：检查Secrets配置，确保Docker Hub账号和Kubernetes配置正确

- **问题**：镜像推送失败
  **解决方案**：检查Docker Hub访问令牌权限，确保网络连接正常

## 7. 部署架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                             访问层                                      │
│  ┌─────────────────────┐  ┌─────────────────────┐                      │
│  │  前端服务           │  │  后端API服务        │                      │
│  │  (dashboard.local)  │  │  (api.local)        │                      │
│  └─────────────────────┘  └─────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────┘
                                ↑         ↑
┌─────────────────────────────────────────────────────────────────────────┐
│                             Kubernetes集群                            │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐ │
│  │  前端部署           │  │  后端部署           │  │  Spark处理部署  │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────┘ │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐ │
│  │  Redis             │  │  PostgreSQL         │  │  InfluxDB       │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────┘ │
│  ┌─────────────────────┐  ┌─────────────────────┐                      │
│  │  Kafka             │  │  Zookeeper          │                      │
│  └─────────────────────┘  └─────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────┘
                                ↑         ↑
┌─────────────────────────────────────────────────────────────────────────┐
│                             CI/CD流水线                                │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐ │
│  │  代码提交           │  │  镜像构建与推送     │  │  K8s部署更新    │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

## 8. 总结

本部署文档详细介绍了数字孪生与个性化干预系统的容器化部署和Kubernetes部署流程，包括：

1. **Docker容器化**：为所有组件编写了Dockerfile，使用docker-compose实现本地一键启动
2. **Kubernetes部署**：使用Minikube模拟K8s集群，配置了所有服务的部署文件和Ingress
3. **CI/CD流水线**：使用GitHub Actions实现代码提交→自动构建→推送镜像→更新K8s部署的流程
4. **服务验证**：提供了详细的验证步骤，确保所有服务正常运行

通过本部署方案，系统实现了"组件容器化、部署自动化"的目标，证明了项目的"可落地性"，避免了"本地跑通但无法部署"的问题。