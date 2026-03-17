# 使用官方TensorFlow Serving镜像作为基础
FROM tensorflow/serving:latest

# 安装必要的依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

# 复制模型文件和代码
COPY src/ /app/src/
COPY models/ /app/models/

# 设置环境变量
ENV MODEL_BASE_PATH=/app/models
ENV MODEL_NAME=activity_model

# 暴露端口
EXPOSE 8501

# 启动TensorFlow Serving
CMD ["/usr/bin/tensorflow_model_server", "--rest_api_port=8501", "--model_name=activity_model", "--model_base_path=/app/models/activity_model"]