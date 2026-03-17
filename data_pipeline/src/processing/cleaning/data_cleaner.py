from typing import Dict, Any, List
import logging
from datetime import datetime
from ...config.config_manager import config_manager

class DataCleaner:
    """数据清洗模块"""
    
    def __init__(self):
        """初始化数据清洗模块"""
        self.config = config_manager.get_section("processing")["cleaning"]
        self.logger = logging.getLogger("DataCleaner")
    
    def clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗数据"""
        try:
            # 根据数据类型选择不同的清洗策略
            data_type = data.get("data_type", "")
            
            if data_type == "wearable":
                cleaned_data = self._clean_wearable_data(data)
            elif data_type == "environment":
                cleaned_data = self._clean_environment_data(data)
            elif data_type == "audio":
                cleaned_data = self._clean_audio_data(data)
            else:
                cleaned_data = self._clean_generic_data(data)
            
            # 添加清洗标记
            cleaned_data["cleaned"] = True
            cleaned_data["cleaned_at"] = datetime.now().isoformat()
            
            return cleaned_data
            
        except Exception as e:
            self.logger.error(f"数据清洗失败: {e}")
            # 添加清洗失败标记
            data["cleaned"] = False
            data["cleaning_error"] = str(e)
            return data
    
    def _clean_wearable_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗可穿戴设备数据"""
        # 可穿戴设备数据的关键指标
        wearable_metrics = ["heart_rate", "steps", "blood_pressure", "temperature", "acceleration"]
        
        # 清洗每个指标
        for metric in wearable_metrics:
            if metric in data:
                # 处理异常值
                if self.config["outlier_detection"]:
                    data[metric] = self._detect_and_handle_outliers(data[metric], metric)
                
                # 处理缺失值
                if self.config["missing_value_imputation"] and data[metric] is None:
                    data[metric] = self._impute_missing_value(data[metric], metric)
        
        # 标准化心率数据 (60-100 bpm为正常范围)
        if "heart_rate" in data and data["heart_rate"] is not None:
            if data["heart_rate"] < 40:
                data["heart_rate"] = 40
            elif data["heart_rate"] > 200:
                data["heart_rate"] = 200
        
        # 标准化体温数据 (35-42°C为正常范围)
        if "temperature" in data and data["temperature"] is not None:
            if data["temperature"] < 35:
                data["temperature"] = 35
            elif data["temperature"] > 42:
                data["temperature"] = 42
        
        return data
    
    def _clean_environment_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗环境传感器数据"""
        # 环境传感器数据的关键指标
        environment_metrics = ["temperature", "humidity", "light_intensity", "co2_level", "smoke_level"]
        
        # 清洗每个指标
        for metric in environment_metrics:
            if metric in data:
                # 处理异常值
                if self.config["outlier_detection"]:
                    data[metric] = self._detect_and_handle_outliers(data[metric], metric)
                
                # 处理缺失值
                if self.config["missing_value_imputation"] and data[metric] is None:
                    data[metric] = self._impute_missing_value(data[metric], metric)
        
        # 标准化温度数据 (-20-50°C为正常范围)
        if "temperature" in data and data["temperature"] is not None:
            if data["temperature"] < -20:
                data["temperature"] = -20
            elif data["temperature"] > 50:
                data["temperature"] = 50
        
        # 标准化湿度数据 (0-100%为正常范围)
        if "humidity" in data and data["humidity"] is not None:
            if data["humidity"] < 0:
                data["humidity"] = 0
            elif data["humidity"] > 100:
                data["humidity"] = 100
        
        return data
    
    def _clean_audio_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗音频数据"""
        # 音频数据主要检查完整性和格式
        if "audio_data" not in data or not data["audio_data"]:
            data["audio_data"] = None
            data["audio_error"] = "缺失音频数据"
        
        # 检查采样率
        if "sampling_rate" in data and data["sampling_rate"] != config_manager.get_value("data_sources.audio.sampling_rate"):
            data["sampling_rate"] = config_manager.get_value("data_sources.audio.sampling_rate")
            data["resampled"] = True
        
        return data
    
    def _clean_generic_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗通用数据"""
        # 处理所有数值字段
        for key, value in data.items():
            if isinstance(value, (int, float)):
                # 处理异常值
                if self.config["outlier_detection"]:
                    data[key] = self._detect_and_handle_outliers(value, key)
                
                # 处理缺失值
                if self.config["missing_value_imputation"] and value is None:
                    data[key] = self._impute_missing_value(value, key)
        
        return data
    
    def _detect_and_handle_outliers(self, value: Any, metric: str) -> Any:
        """检测并处理异常值"""
        # 简单的基于标准差的异常值检测
        if value is None:
            return value
        
        # 这里使用预设的正常范围，实际应用中应该基于历史数据计算
        normal_ranges = {
            "heart_rate": (40, 200),
            "steps": (0, 20000),
            "blood_pressure": (60, 180),
            "temperature": (35, 42),
            "acceleration": (-20, 20),
            "temperature_env": (-20, 50),
            "humidity": (0, 100),
            "light_intensity": (0, 10000),
            "co2_level": (0, 5000),
            "smoke_level": (0, 1000)
        }
        
        if metric in normal_ranges:
            min_val, max_val = normal_ranges[metric]
            if value < min_val or value > max_val:
                self.logger.debug(f"检测到异常值: {metric} = {value}, 正常范围: [{min_val}, {max_val}]")
                # 截断到正常范围内
                return max(min_val, min(max_val, value))
        
        return value
    
    def _impute_missing_value(self, value: Any, metric: str) -> Any:
        """填充缺失值"""
        if value is not None:
            return value
        
        # 基于指标类型选择填充策略
        imputation_values = {
            "heart_rate": 75,  # 平均心率
            "steps": 0,
            "blood_pressure": 120,  # 平均收缩压
            "temperature": 37.0,  # 正常体温
            "temperature_env": 25.0,  # 室温
            "humidity": 50,  # 平均湿度
            "light_intensity": 500,  # 中等光照
            "co2_level": 400,  # 正常CO2水平
            "smoke_level": 0
        }
        
        return imputation_values.get(metric, 0)
    
    def batch_clean_data(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量清洗数据"""
        cleaned_data_list = []
        for data in data_list:
            cleaned_data = self.clean_data(data)
            cleaned_data_list.append(cleaned_data)
        
        return cleaned_data_list
