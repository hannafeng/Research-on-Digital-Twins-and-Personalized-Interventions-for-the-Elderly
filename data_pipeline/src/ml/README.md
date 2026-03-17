# 机器学习模型开发文档

## 项目概述

本项目实现了一套完整的机器学习模型系统，用于社区养老数字孪生平台。主要包括三个核心模型：

1. **行为识别模型**：基于CNN-LSTM混合架构，识别用户的关键行为状态
2. **情感计算模型**：基于MFCC特征和CNN/SVM，识别用户的情感状态
3. **智能干预生成模型**：融合规则引擎与强化学习，生成个性化干预建议

## 目录结构

```
src/ml/
├── models/           # 模型定义和实现
├── services/         # 模型服务和API
├── utils/            # 工具函数
├── config/           # 配置文件
├── data/             # 数据集和预处理
└── __init__.py
```

## 模型详情

### 1. 行为识别模型

**技术方案**：CNN-LSTM混合深度学习架构

**输入数据**：加速度传感器与陀螺仪采集的运动序列数据

**输出格式**：行为标签及相应的置信度评分（如"跌倒：92%"）

**性能指标**：
- 准确率 ≥ 85%
- 跌倒识别召回率 ≥ 90%

**模型文件**：`models/activity_recognition.py`

### 2. 情感计算模型

**技术方案**：提取语音数据的MFCC特征，采用SVM分类器或轻量级CNN网络架构

**输入数据**：音频数据

**输出格式**：情感标签及相应的置信度评分

**性能指标**：
- 情感分类准确率 ≥ 80%

**模型文件**：`models/emotion_recognition.py`

### 3. 智能干预生成模型

**技术方案**：融合规则引擎与强化学习（Q-Learning）的混合决策系统

**输入数据**：用户当前的孪生状态数据

**输出格式**：可解释、个性化的干预建议，包含详细解释理由

**性能指标**：
- 干预建议的采纳率 ≥ 70%
- 用户满意度 ≥ 80%

**模型文件**：`models/intervention_generator.py`

## 模型部署

### 容器化部署

使用Docker容器封装所有模型组件，确保环境一致性与部署便捷性。

**配置文件**：
- `Dockerfile`：构建模型服务镜像
- `docker-compose.yml`：编排多个模型服务
- `prometheus.yml`：监控配置

### 服务架构

通过Flask构建高性能模型服务，提供标准化HTTP接口：

- **行为识别API**：`/api/activity`
- **情感计算API**：`/api/emotion`
- **干预生成API**：`/api/intervention`
- **健康检查API**：`/api/health`

**性能指标**：
- 接口响应时间 ≤ 500ms
- 支持每秒至少100次并发请求

## 集成使用

### 与数字孪生体集成

数字孪生体模块已集成机器学习模型，可通过以下方法使用：

```python
# 初始化数字孪生体
twin = DigitalTwin(user_id="user_001")

# 更新动态状态（自动调用行为识别和情感计算）
twin.update_dynamic_state(data)

# 生成干预建议
intervention = twin.generate_intervention()

# 获取完整孪生体数据（包含干预建议）
full_twin = twin.get_full_twin()
```

### 独立使用模型服务

启动模型服务后，可通过HTTP请求调用：

```bash
# 行为识别
curl -X POST http://localhost:5000/api/activity \
  -H "Content-Type: application/json" \
  -d '{"sensor_data": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, ...]}'

# 情感计算
curl -X POST http://localhost:5000/api/emotion \
  -H "Content-Type: application/json" \
  -d '{"audio_data": [[0.1, 0.2, ...], [0.3, 0.4, ...], ...]}'

# 干预生成
curl -X POST http://localhost:5000/api/intervention \
  -H "Content-Type: application/json" \
  -d '{"twin_state": {"health_status": {...}, "behavior_status": {...}, "emotion_status": {...}}}'
```

## 训练与优化

### 数据准备

- **行为识别**：使用UCI Human Activity Recognition数据集
- **情感计算**：使用AISHELL-4语音数据集

### 模型训练

1. 数据预处理：特征标准化、窗口分割、数据增强
2. 模型训练：参数优化、交叉验证
3. 模型压缩：使用TensorFlow Lite技术，确保在边缘设备上的高效运行

### 模型评估

- **行为识别**：准确率、召回率、F1-score
- **情感计算**：准确率、混淆矩阵
- **干预生成**：采纳率、用户满意度

## 监控与维护

### 性能监控

使用Prometheus和Grafana监控模型服务的性能：

- 响应时间
- 并发请求数
- 模型预测准确率

### 数据漂移检测

定期检测输入数据的分布变化，确保模型性能稳定。

### 自动报警机制

当模型性能下降或服务异常时，触发自动报警。

## 未来优化方向

1. **模型精度提升**：使用更先进的深度学习架构，如Transformer
2. **实时性优化**：进一步优化模型推理速度，支持更实时的应用场景
3. **多模态融合**：融合视觉、语音、生理信号等多模态数据，提高识别准确率
4. **个性化定制**：基于用户历史数据，进一步个性化模型参数
5. **联邦学习**：在保护隐私的前提下，使用联邦学习技术提升模型性能

## 依赖项

```
tensorflow==2.15.0
tensorflow-serving-api==2.15.0
scikit-learn==1.4.0
librosa==0.10.1
flask==2.0.1
numpy==1.24.3
pandas==2.0.3
```

## 启动方法

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **启动模型服务**：
   ```bash
   python src/ml/services/model_service.py
   ```

3. **使用Docker部署**：
   ```bash
   docker-compose up -d
   ```

## 测试

运行测试脚本验证模型功能：

```bash
python tests/test_ml_models.py
```