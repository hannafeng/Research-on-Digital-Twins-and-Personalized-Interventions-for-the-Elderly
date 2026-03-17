import flask
from flask import request, jsonify
import logging
import numpy as np
import json
import asyncio
from datetime import datetime
from pathlib import Path
from flask_socketio import SocketIO, emit
from ..models.activity_recognition import ActivityRecognitionModel
from ..models.emotion_recognition import EmotionRecognitionModel
from ..models.intervention_generator import InterventionGenerator
from ..models.fall_detection import ModelManager, StateManager, LLMService, process_activity_logic, handle_user_reply

app = flask.Flask(__name__)
app.config["DEBUG"] = True
app.config["SECRET_KEY"] = "secret_key"
socketio = SocketIO(app, cors_allowed_origins="*")

# 初始化模型
activity_model = ActivityRecognitionModel()
emotion_model = EmotionRecognitionModel()
intervention_generator = InterventionGenerator()

# 构建模型
activity_model.build_model()
emotion_model.build_model()

# 初始化摔倒检测相关组件
BASE_DIR = Path(__file__).parent.parent.parent.parent
MODEL_DIR = BASE_DIR / "models"
fall_model_manager = ModelManager(
    model_path=MODEL_DIR / "har_model.json",
    encoder_path=MODEL_DIR / "label_encoder.pkl",
    features_path=MODEL_DIR / "feature_names.pkl"
)
fall_model_manager.load()

# 初始化状态管理器和LLM服务
state_manager = StateManager()
# 从环境变量或配置文件中获取LLM API密钥
import os
from dotenv import load_dotenv
load_dotenv()

llm_service = LLMService(
    api_key=os.getenv("QWEN_API_KEY", ""),
    api_url=os.getenv("QWEN_API_URL", "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"),
    model=os.getenv("QWEN_MODEL", "qwen-plus")
)

logger = logging.getLogger("ModelService")

# 模拟数据存储
intervention_status = {}
notification_rules = {}
device_status = {}
system_logs = []

@app.route('/api/activity', methods=['POST'])
def predict_activity():
    """行为识别API"""
    try:
        # 获取请求数据
        data = request.get_json()
        sensor_data = data.get('sensor_data')
        
        if not sensor_data:
            return jsonify({"error": "缺少传感器数据"}), 400
        
        # 预测行为
        result = activity_model.predict([sensor_data])
        
        if result:
            return jsonify(result[0])
        else:
            return jsonify({"error": "预测失败"}), 500
    except Exception as e:
        logger.error(f"行为识别API错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/emotion', methods=['POST'])
def predict_emotion():
    """情感计算API"""
    try:
        # 获取请求数据
        data = request.get_json()
        audio_data = data.get('audio_data')
        
        if not audio_data:
            return jsonify({"error": "缺少音频数据"}), 400
        
        # 预测情感
        result = emotion_model.predict([audio_data])
        
        if result:
            return jsonify(result[0])
        else:
            return jsonify({"error": "预测失败"}), 500
    except Exception as e:
        logger.error(f"情感计算API错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/intervention', methods=['POST'])
def generate_intervention():
    """智能干预生成API"""
    try:
        # 获取请求数据
        data = request.get_json()
        twin_state = data.get('twin_state')
        
        if not twin_state:
            return jsonify({"error": "缺少孪生体状态数据"}), 400
        
        # 生成干预建议
        result = intervention_generator.generate_intervention(twin_state)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"干预生成API错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查API"""
    return jsonify({"status": "healthy"})

# 摔倒检测相关API

@app.route('/api/fall_detection/predict', methods=['POST'])
def receive_prediction():
    """接收行为预测结果并处理摔倒检测逻辑"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        activity_label = data.get('activity_label')
        timestamp_str = data.get('timestamp')
        
        if not user_id or not activity_label:
            return jsonify({"error": "缺少用户ID或活动标签"}), 400
        
        # 解析时间戳
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str)
        else:
            timestamp = datetime.now()
        
        # 处理活动逻辑
        current_state = asyncio.run(process_activity_logic(user_id, activity_label, timestamp, state_manager, llm_service))
        
        return jsonify({
            "status": "ok",
            "user_state": str(current_state),
            "received": str(activity_label)
        })
    except Exception as e:
        logger.error(f"摔倒检测预测API错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fall_detection/sensor_predict', methods=['POST'])
def sensor_predict():
    """接收传感器数据并预测活动，然后处理摔倒检测逻辑"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        features = data.get('features')
        timestamp_str = data.get('timestamp')
        
        if not user_id or not features:
            return jsonify({"error": "缺少用户ID或特征数据"}), 400
        
        if len(features) != 561:
            return jsonify({"error": "特征维度必须为561"}), 400
        
        # 解析时间戳
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str)
        else:
            timestamp = datetime.now()
        
        # 预测活动
        if not fall_model_manager.is_loaded:
            return jsonify({"error": "模型未加载"}), 503
        
        activity = fall_model_manager.predict(features)
        
        # 处理活动逻辑
        current_state = asyncio.run(process_activity_logic(user_id, activity, timestamp, state_manager, llm_service))
        
        return jsonify({
            "status": "ok",
            "predicted_activity": str(activity),
            "user_state": str(current_state)
        })
    except Exception as e:
        logger.error(f"传感器预测API错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fall_detection/user_reply', methods=['POST'])
def handle_fall_user_reply():
    """处理用户对摔倒检测的回复"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        reply_text = data.get('reply_text')
        timestamp_str = data.get('timestamp')
        
        if not user_id or not reply_text:
            return jsonify({"error": "缺少用户ID或回复内容"}), 400
        
        # 解析时间戳
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str)
        else:
            timestamp = datetime.now()
        
        # 处理用户回复
        result = asyncio.run(handle_user_reply(user_id, reply_text, timestamp, state_manager, llm_service))
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"用户回复处理API错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/fall_detection/status/<user_id>', methods=['GET'])
def get_fall_status(user_id):
    """获取用户摔倒检测状态"""
    try:
        status_data = asyncio.run(state_manager.get_status(user_id))
        if not status_data:
            return jsonify({"message": "用户不存在", "default_state": "normal"})
        return jsonify(status_data)
    except Exception as e:
        logger.error(f"获取摔倒检测状态API错误: {e}")
        return jsonify({"error": str(e)}), 500

# 社区护理人员模块API

@app.route('/api/caregiver/alert', methods=['GET'])
def get_health_alerts():
    """获取健康风险预警"""
    try:
        # 模拟健康风险预警数据
        alerts = [
            {
                "alert_id": "alert_001",
                "user_id": "user_001",
                "risk_level": "high",
                "abnormal指标": "心率异常",
                "message": "老人心率异常，请及时处理",
                "timestamp": datetime.now().isoformat()
            },
            {
                "alert_id": "alert_002",
                "user_id": "user_002",
                "risk_level": "medium",
                "abnormal指标": "活动量过低",
                "message": "老人活动量过低，建议提醒活动",
                "timestamp": datetime.now().isoformat()
            }
        ]
        return jsonify(alerts)
    except Exception as e:
        logger.error(f"获取健康风险预警错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/caregiver/intervention/confirm', methods=['POST'])
def confirm_intervention():
    """确认干预建议"""
    try:
        data = request.get_json()
        intervention_id = data.get('intervention_id')
        user_id = data.get('user_id')
        
        if not intervention_id or not user_id:
            return jsonify({"error": "缺少干预ID或用户ID"}), 400
        
        # 记录干预执行状态
        intervention_status[intervention_id] = {
            "status": "in_progress",
            "confirmed_at": datetime.now().isoformat(),
            "user_id": user_id
        }
        
        return jsonify({"success": True, "message": "干预建议已确认"})
    except Exception as e:
        logger.error(f"确认干预建议错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/caregiver/intervention/status', methods=['GET'])
def get_intervention_status():
    """获取干预执行状态"""
    try:
        return jsonify(intervention_status)
    except Exception as e:
        logger.error(f"获取干预执行状态错误: {e}")
        return jsonify({"error": str(e)}), 500

# 老人家属模块API

@app.route('/api/family/dashboard', methods=['GET'])
def get_family_dashboard():
    """获取老人状态仪表盘数据"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "缺少用户ID"}), 400
        
        # 模拟仪表盘数据
        dashboard_data = {
            "user_id": user_id,
            "health_metrics": {
                "heart_rate": 75,
                "blood_pressure": "120/80",
                "steps": 3500,
                "sleep_quality": "good"
            },
            "daily_activities": {
                "medication_completion": 100,
                "activity_time": 120,
                "social_interaction": "medium"
            },
            "last_updated": datetime.now().isoformat()
        }
        
        return jsonify(dashboard_data)
    except Exception as e:
        logger.error(f"获取老人状态仪表盘数据错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/family/notification/rule', methods=['POST'])
def set_notification_rule():
    """设置通知规则"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        rules = data.get('rules')
        
        if not user_id or not rules:
            return jsonify({"error": "缺少用户ID或规则"}), 400
        
        # 保存通知规则
        notification_rules[user_id] = rules
        
        return jsonify({"success": True, "message": "通知规则已设置"})
    except Exception as e:
        logger.error(f"设置通知规则错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/family/notification/rule', methods=['GET'])
def get_notification_rule():
    """获取通知规则"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "缺少用户ID"}), 400
        
        rule = notification_rules.get(user_id, {})
        return jsonify(rule)
    except Exception as e:
        logger.error(f"获取通知规则错误: {e}")
        return jsonify({"error": str(e)}), 500

# 老年人模块API

@app.route('/api/elderly/command', methods=['GET'])
def get_elderly_commands():
    """获取老年人日常指令"""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "缺少用户ID"}), 400
        
        # 模拟日常指令
        commands = [
            {
                "command_id": "cmd_001",
                "type": "medication",
                "content": "该吃药了",
                "timestamp": "08:00"
            },
            {
                "command_id": "cmd_002",
                "type": "activity",
                "content": "该活动一下了",
                "timestamp": "10:30"
            },
            {
                "command_id": "cmd_003",
                "type": "entertainment",
                "content": "播放怀旧音乐",
                "timestamp": "15:00"
            }
        ]
        
        return jsonify(commands)
    except Exception as e:
        logger.error(f"获取老年人日常指令错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/elderly/call', methods=['POST'])
def emergency_call():
    """老年人一键呼叫"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        call_type = data.get('call_type', 'emergency')  # emergency or daily
        
        if not user_id:
            return jsonify({"error": "缺少用户ID"}), 400
        
        # 模拟呼叫处理
        call_result = {
            "call_id": f"call_{datetime.now().timestamp()}",
            "user_id": user_id,
            "call_type": call_type,
            "status": "connected",
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(call_result)
    except Exception as e:
        logger.error(f"老年人一键呼叫错误: {e}")
        return jsonify({"error": str(e)}), 500

# 系统管理员模块API

@app.route('/api/admin/devices', methods=['GET'])
def get_device_status():
    """获取设备状态"""
    try:
        # 模拟设备状态数据
        devices = [
            {
                "device_id": "device_001",
                "type": "wearable",
                "status": "online",
                "battery": 85,
                "last_updated": datetime.now().isoformat()
            },
            {
                "device_id": "device_002",
                "type": "environment",
                "status": "online",
                "battery": 70,
                "last_updated": datetime.now().isoformat()
            },
            {
                "device_id": "device_003",
                "type": "audio",
                "status": "offline",
                "battery": 0,
                "last_updated": datetime.now().isoformat()
            }
        ]
        
        return jsonify(devices)
    except Exception as e:
        logger.error(f"获取设备状态错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/device/config', methods=['POST'])
def configure_device():
    """远程配置设备"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        config = data.get('config')
        
        if not device_id or not config:
            return jsonify({"error": "缺少设备ID或配置"}), 400
        
        # 模拟设备配置
        return jsonify({"success": True, "message": f"设备 {device_id} 配置成功"})
    except Exception as e:
        logger.error(f"远程配置设备错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/logs', methods=['GET'])
def get_system_logs():
    """获取系统日志"""
    try:
        # 模拟系统日志数据
        logs = [
            {
                "log_id": "log_001",
                "level": "error",
                "message": "设备 device_003 离线",
                "timestamp": datetime.now().isoformat(),
                "is_anomaly": True
            },
            {
                "log_id": "log_002",
                "level": "info",
                "message": "系统启动成功",
                "timestamp": datetime.now().isoformat(),
                "is_anomaly": False
            },
            {
                "log_id": "log_003",
                "level": "warning",
                "message": "心率数据异常",
                "timestamp": datetime.now().isoformat(),
                "is_anomaly": True
            }
        ]
        
        return jsonify(logs)
    except Exception as e:
        logger.error(f"获取系统日志错误: {e}")
        return jsonify({"error": str(e)}), 500

# WebSocket事件处理
@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    emit('response', {'message': 'Connected to WebSocket server'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('subscribe')
def handle_subscribe(data):
    topic = data.get('topic')
    logger.info(f'Client subscribed to topic: {topic}')
    emit('response', {'message': f'Subscribed to {topic}'})

@socketio.on('fall_detection:predict')
def handle_fall_detection_predict(data):
    try:
        user_id = data.get('user_id')
        activity_label = data.get('activity_label')
        timestamp = datetime.now()
        
        if not user_id or not activity_label:
            emit('error', {'message': '缺少用户ID或活动标签'})
            return
        
        # 处理活动逻辑
        current_state = asyncio.run(process_activity_logic(user_id, activity_label, timestamp, state_manager, llm_service))
        
        emit('fall_detection:response', {
            'status': 'ok',
            'user_state': str(current_state),
            'received': str(activity_label)
        })
    except Exception as e:
        logger.error(f'WebSocket fall detection predict error: {e}')
        emit('error', {'message': str(e)})

@socketio.on('fall_detection:user_reply')
def handle_fall_detection_user_reply(data):
    try:
        user_id = data.get('user_id')
        reply_text = data.get('reply_text')
        timestamp = datetime.now()
        
        if not user_id or not reply_text:
            emit('error', {'message': '缺少用户ID或回复内容'})
            return
        
        # 处理用户回复
        result = asyncio.run(handle_user_reply(user_id, reply_text, timestamp, state_manager, llm_service))
        
        emit('fall_detection:response', result)
    except Exception as e:
        logger.error(f'WebSocket fall detection user reply error: {e}')
        emit('error', {'message': str(e)})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)