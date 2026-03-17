from typing import Dict, Any, List
import logging
import json
from datetime import datetime, timedelta
from ..config.config_manager import config_manager
from ..storage.storage_manager import StorageManager
# 导入机器学习模型
from ..ml.models.activity_recognition import ActivityRecognitionModel
from ..ml.models.emotion_recognition import EmotionRecognitionModel
from ..ml.models.intervention_generator import InterventionGenerator

class DigitalTwin:
    """数字孪生体核心模块"""
    
    def __init__(self, user_id: str):
        """初始化数字孪生体"""
        self.user_id = user_id
        self.logger = logging.getLogger(f"DigitalTwin_{user_id}")
        self.storage_manager = StorageManager()
        
        # 初始化机器学习模型
        self.activity_model = ActivityRecognitionModel()
        self.emotion_model = EmotionRecognitionModel()
        self.intervention_generator = InterventionGenerator()
        
        # 初始化各层数据
        self.base_info = {}
        self.dynamic_state = {}
        self.personalized_baseline = {}
        
        # 加载基础信息
        self._load_base_info()
        # 加载动态状态
        self._load_dynamic_state()
        # 加载个性化基线
        self._load_personalized_baseline()
        
        # 加载模型
        self._load_models()
    
    def _load_base_info(self) -> None:
        """加载基础信息层（静态数据）"""
        try:
            user_info = self.storage_manager.get_user_info(self.user_id)
            if user_info:
                self.base_info = user_info
                self.logger.info("基础信息加载成功")
            else:
                self.logger.warning("未找到用户基础信息")
        except Exception as e:
            self.logger.error(f"加载基础信息失败: {e}")
    
    def _load_dynamic_state(self) -> None:
        """加载动态状态层（实时数据）"""
        try:
            # 从Redis获取最新的实时数据
            real_time_data = self.storage_manager.get_real_time_data(user_id=self.user_id, count=50)
            
            # 解析并聚合实时数据
            self.dynamic_state = {
                "health_status": {},
                "behavior_status": {},
                "emotion_status": {},
                "last_updated": datetime.now().isoformat()
            }
            
            # 处理健康相关数据
            for data in real_time_data:
                if data.get("data_type") == "wearable":
                    self.dynamic_state["health_status"].update({
                        "heart_rate": data.get("heart_rate"),
                        "blood_pressure": data.get("blood_pressure"),
                        "steps": data.get("steps"),
                        "sleep": data.get("sleep"),
                        "activity": data.get("activity")
                    })
                elif data.get("data_type") == "environment":
                    self.dynamic_state["behavior_status"].update({
                        "temperature": data.get("temperature"),
                        "humidity": data.get("humidity"),
                        "light": data.get("light"),
                        "noise": data.get("noise")
                    })
                elif data.get("data_type") == "audio":
                    self.dynamic_state["emotion_status"].update({
                        "audio_activity": data.get("audio_activity"),
                        "speech_detection": data.get("speech_detection"),
                        "emotion": data.get("emotion")
                    })
            
            self.logger.info("动态状态加载成功")
        except Exception as e:
            self.logger.error(f"加载动态状态失败: {e}")
    
    def _load_personalized_baseline(self) -> None:
        """加载个性化基线层（定期更新）"""
        try:
            # 从Redis或其他存储中获取基线数据
            # 这里简化处理，实际应该从存储中读取
            self.personalized_baseline = {
                "sleep": {
                    "normal_range": ["23:00", "06:00"],
                    "duration": 7,
                    "last_updated": datetime.now().isoformat()
                },
                "heart_rate": {
                    "resting_range": [60, 80],
                    "active_range": [80, 120],
                    "last_updated": datetime.now().isoformat()
                },
                "blood_pressure": {
                    "normal_range": [120, 80],
                    "last_updated": datetime.now().isoformat()
                },
                "activity": {
                    "daily_steps": 5000,
                    "last_updated": datetime.now().isoformat()
                }
            }
            self.logger.info("个性化基线加载成功")
        except Exception as e:
            self.logger.error(f"加载个性化基线失败: {e}")
    
    def _load_models(self) -> None:
        """加载机器学习模型"""
        try:
            # 构建模型（实际应用中应该加载训练好的模型）
            self.activity_model.build_model()
            self.emotion_model.build_model()
            self.logger.info("机器学习模型加载成功")
        except Exception as e:
            self.logger.error(f"加载机器学习模型失败: {e}")
    
    def update_dynamic_state(self, data: Dict[str, Any]) -> bool:
        """更新动态状态层"""
        try:
            # 更新对应的状态数据
            if data.get("data_type") == "wearable":
                # 提取加速度和陀螺仪数据进行行为识别
                accel_data = data.get("accelerometer")
                gyro_data = data.get("gyroscope")
                
                if accel_data and gyro_data:
                    # 合并加速度和陀螺仪数据
                    sensor_data = []
                    for a, g in zip(accel_data, gyro_data):
                        sensor_data.extend([a[0], a[1], a[2], g[0], g[1], g[2]])
                    
                    # 行为识别
                    activity_result = self.activity_model.predict([sensor_data])
                    if activity_result:
                        self.dynamic_state["behavior_status"]["activity"] = activity_result[0]["label"]
                        self.dynamic_state["behavior_status"]["activity_confidence"] = activity_result[0]["confidence"]
                
                self.dynamic_state["health_status"].update({
                    "heart_rate": data.get("heart_rate"),
                    "blood_pressure": data.get("blood_pressure"),
                    "steps": data.get("steps"),
                    "sleep": data.get("sleep"),
                    "activity": data.get("activity")
                })
            elif data.get("data_type") == "environment":
                self.dynamic_state["behavior_status"].update({
                    "temperature": data.get("temperature"),
                    "humidity": data.get("humidity"),
                    "light": data.get("light"),
                    "noise": data.get("noise"),
                    "weather": data.get("weather")
                })
            elif data.get("data_type") == "audio":
                # 提取音频数据进行情感识别
                audio_data = data.get("audio_data")
                if audio_data:
                    # 情感识别
                    emotion_result = self.emotion_model.predict([audio_data])
                    if emotion_result:
                        self.dynamic_state["emotion_status"]["emotion"] = emotion_result[0]["label"]
                        self.dynamic_state["emotion_status"]["emotion_confidence"] = emotion_result[0]["confidence"]
                
                self.dynamic_state["emotion_status"].update({
                    "audio_activity": data.get("audio_activity"),
                    "speech_detection": data.get("speech_detection")
                })
            
            # 更新时间戳
            self.dynamic_state["last_updated"] = datetime.now().isoformat()
            
            # 存储到Redis
            self.storage_manager.store_data({
                "data_type": "digital_twin_state",
                "user_id": self.user_id,
                "state": self.dynamic_state,
                "timestamp": datetime.now().isoformat()
            })
            
            self.logger.info("动态状态更新成功")
            return True
        except Exception as e:
            self.logger.error(f"更新动态状态失败: {e}")
            return False
    
    def update_personalized_baseline(self) -> bool:
        """更新个性化基线层（定期执行）"""
        try:
            # 获取历史数据（7-14天）
            end_time = datetime.now()
            start_time = end_time - timedelta(days=14)
            
            # 构建查询获取历史健康数据
            query = f"""
                SELECT time, heart_rate, blood_pressure, sleep, steps 
                FROM wearable_data 
                WHERE user_id = '{self.user_id}' 
                AND time >= '{start_time.isoformat()}' 
                AND time <= '{end_time.isoformat()}'
            """
            
            historical_data = self.storage_manager.get_historical_data(query)
            
            # 这里应该使用时间序列模型（如Prophet/LSTM）训练基线
            # 简化处理，使用统计方法计算基线
            if historical_data:
                # 计算心率基线
                heart_rates = [d.get("heart_rate") for d in historical_data if d.get("heart_rate")]
                if heart_rates:
                    avg_heart_rate = sum(heart_rates) / len(heart_rates)
                    self.personalized_baseline["heart_rate"] = {
                        "resting_range": [int(avg_heart_rate - 10), int(avg_heart_rate + 10)],
                        "active_range": [int(avg_heart_rate + 10), int(avg_heart_rate + 40)],
                        "last_updated": datetime.now().isoformat()
                    }
                
                # 计算睡眠基线
                sleep_data = [d.get("sleep") for d in historical_data if d.get("sleep")]
                if sleep_data:
                    # 简化处理，实际应该分析睡眠模式
                    self.personalized_baseline["sleep"] = {
                        "normal_range": ["23:00", "06:00"],
                        "duration": 7,
                        "last_updated": datetime.now().isoformat()
                    }
            
            # 存储基线数据
            self.storage_manager.store_data({
                "data_type": "digital_twin_baseline",
                "user_id": self.user_id,
                "baseline": self.personalized_baseline,
                "timestamp": datetime.now().isoformat()
            })
            
            self.logger.info("个性化基线更新成功")
            return True
        except Exception as e:
            self.logger.error(f"更新个性化基线失败: {e}")
            return False
    
    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """检测异常情况"""
        try:
            anomalies = []
            
            # 检测心率异常
            current_heart_rate = self.dynamic_state.get("health_status", {}).get("heart_rate")
            if current_heart_rate:
                resting_range = self.personalized_baseline.get("heart_rate", {}).get("resting_range", [60, 80])
                if current_heart_rate < resting_range[0] or current_heart_rate > resting_range[1]:
                    anomalies.append({
                        "type": "heart_rate_anomaly",
                        "message": f"心率异常: {current_heart_rate}，正常范围: {resting_range}",
                        "severity": "medium",
                        "timestamp": datetime.now().isoformat()
                    })
            
            # 检测睡眠异常
            current_time = datetime.now().strftime("%H:%M")
            sleep_range = self.personalized_baseline.get("sleep", {}).get("normal_range", ["23:00", "06:00"])
            if current_time >= "00:00" and current_time < sleep_range[1]:
                # 夜间检测
                if self.dynamic_state.get("behavior_status", {}).get("light") > 50 or \
                   self.dynamic_state.get("emotion_status", {}).get("audio_activity"):
                    anomalies.append({
                        "type": "sleep_anomaly",
                        "message": "夜间活动异常，可能影响睡眠",
                        "severity": "low",
                        "timestamp": datetime.now().isoformat()
                    })
            
            # 检测活动异常
            current_steps = self.dynamic_state.get("health_status", {}).get("steps", 0)
            daily_steps_baseline = self.personalized_baseline.get("activity", {}).get("daily_steps", 5000)
            if current_steps < daily_steps_baseline * 0.3:
                anomalies.append({
                    "type": "activity_anomaly",
                    "message": f"活动量过低: {current_steps}步，建议: {daily_steps_baseline}步",
                    "severity": "low",
                    "timestamp": datetime.now().isoformat()
                })
            
            return anomalies
        except Exception as e:
            self.logger.error(f"异常检测失败: {e}")
            return []
    
    def generate_intervention(self) -> Dict[str, Any]:
        """生成智能干预建议"""
        try:
            # 生成干预建议
            intervention = self.intervention_generator.generate_intervention(self.dynamic_state)
            self.logger.info(f"生成干预建议: {intervention}")
            return intervention
        except Exception as e:
            self.logger.error(f"生成干预建议失败: {e}")
            return {
                "action": "监测状态",
                "explanation": "生成干预建议时发生错误，继续监测",
                "confidence": "low",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_full_twin(self) -> Dict[str, Any]:
        """获取完整的数字孪生体数据"""
        # 生成干预建议
        intervention = self.generate_intervention()
        
        return {
            "user_id": self.user_id,
            "base_info": self.base_info,
            "dynamic_state": self.dynamic_state,
            "personalized_baseline": self.personalized_baseline,
            "intervention": intervention,
            "last_updated": datetime.now().isoformat()
        }
    
    def close(self) -> None:
        """关闭数字孪生体"""
        if self.storage_manager:
            self.storage_manager.close()
        self.logger.info("数字孪生体已关闭")