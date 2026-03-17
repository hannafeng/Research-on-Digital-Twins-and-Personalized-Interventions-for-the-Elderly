from typing import Dict, Any, List, Tuple, DefaultDict
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from statistics import mean, stdev, pstdev
from ...config.config_manager import config_manager

class DataFuser:
    """数据融合模块"""
    
    def __init__(self):
        """初始化数据融合模块"""
        self.config = config_manager.get_section("processing")["fusion"]
        self.logger = logging.getLogger("DataFuser")
        self.time_window = self.config["time_window"]  # 时间窗口大小（秒）
    
    def fuse_data(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """融合多源数据"""
        try:
            if not data_list:
                return []
            
            # 确保数据包含时间戳
            if not all("timestamp" in data for data in data_list):
                self.logger.error("部分数据缺少时间戳字段")
                return data_list
            
            # 转换时间戳为datetime类型
            for data in data_list:
                try:
                    data["timestamp"] = datetime.fromisoformat(data["timestamp"])
                except (ValueError, TypeError) as e:
                    self.logger.error(f"时间戳转换失败: {e}")
                    return data_list
            
            # 按照用户ID分组融合数据（如果有用户ID）
            has_user_id = all("user_id" in data for data in data_list)
            if has_user_id:
                # 按用户ID分组
                user_data_map: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
                for data in data_list:
                    user_data_map[data["user_id"]].append(data)
                
                fused_data = []
                for user_id, user_data in user_data_map.items():
                    user_fused = self._fuse_user_data(user_data)
                    fused_data.extend(user_fused)
                return fused_data
            else:
                # 没有用户ID时，整体融合
                return self._fuse_user_data(data_list)
                
        except Exception as e:
            self.logger.error(f"数据融合失败: {e}")
            return data_list
    
    def _fuse_user_data(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """融合单个用户的数据"""
        # 按时间戳排序
        sorted_data = sorted(data_list, key=lambda x: x["timestamp"])
        
        # 创建时间窗口
        start_time = sorted_data[0]["timestamp"]
        end_time = sorted_data[-1]["timestamp"]
        
        fused_data = []
        
        current_time = start_time
        while current_time < end_time:
            # 计算窗口的开始和结束时间
            window_start = current_time
            window_end = current_time + timedelta(seconds=self.time_window)
            
            # 筛选当前窗口内的数据
            window_data = [data for data in sorted_data if window_start <= data["timestamp"] < window_end]
            
            if window_data:
                # 融合当前窗口内的数据
                fused_item = self._fuse_window_data(window_data, window_start, window_end)
                if fused_item:
                    fused_data.append(fused_item)
            
            # 移动到下一个窗口
            current_time = window_end
        
        return fused_data
    
    def _fuse_window_data(self, data_list: List[Dict[str, Any]], window_start: datetime, window_end: datetime) -> Dict[str, Any]:
        """融合单个时间窗口内的数据"""
        fused_item = {
            "fused": True,
            "fusion_time_window": {
                "start": window_start.isoformat(),
                "end": window_end.isoformat(),
                "duration_seconds": self.time_window
            },
            "fused_at": datetime.now().isoformat()
        }
        
        # 保留用户ID（如果有）
        if data_list and "user_id" in data_list[0]:
            fused_item["user_id"] = data_list[0]["user_id"]
        
        # 按数据类型分组
        data_type_groups: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
        for data in data_list:
            data_type = data.get("data_type", "unknown")
            data_type_groups[data_type].append(data)
        
        # 融合不同类型的数据
        for data_type, type_data in data_type_groups.items():
            if data_type == "wearable":
                wearable_fused = self._fuse_wearable_data(type_data)
                fused_item.update(wearable_fused)
            elif data_type == "environment":
                env_fused = self._fuse_environment_data(type_data)
                fused_item.update(env_fused)
            elif data_type == "audio":
                audio_fused = self._fuse_audio_data(type_data)
                fused_item.update(audio_fused)
        
        # 提取融合特征
        if self.config["feature_extraction"]:
            features = self._extract_features(fused_item, data_list)
            fused_item.update(features)
        
        return fused_item
    
    def _fuse_wearable_data(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """融合可穿戴设备数据"""
        wearable_features = {
            "heart_rate": None,
            "steps": None,
            "blood_pressure": None,
            "temperature": None,
            "acceleration": None
        }
        
        # 辅助函数：从数据列表中提取指定字段的有效值
        def extract_valid_values(field: str) -> List[float]:
            return [float(data[field]) for data in data_list if field in data and data[field] is not None]
        
        # 对每个特征计算统计值
        heart_rate_values = extract_valid_values("heart_rate")
        if heart_rate_values:
            wearable_features["heart_rate"] = {
                "mean": mean(heart_rate_values),
                "min": min(heart_rate_values),
                "max": max(heart_rate_values),
                "std": stdev(heart_rate_values) if len(heart_rate_values) > 1 else 0
            }
        
        steps_values = extract_valid_values("steps")
        if steps_values:
            wearable_features["steps"] = {
                "total": sum(steps_values),
                "mean_per_minute": mean(steps_values) * 60 / self.time_window
            }
        
        blood_pressure_values = extract_valid_values("blood_pressure")
        if blood_pressure_values:
            wearable_features["blood_pressure"] = {
                "mean": mean(blood_pressure_values),
                "min": min(blood_pressure_values),
                "max": max(blood_pressure_values)
            }
        
        temperature_values = extract_valid_values("temperature")
        if temperature_values:
            wearable_features["temperature"] = {
                "mean": mean(temperature_values),
                "min": min(temperature_values),
                "max": max(temperature_values)
            }
        
        acceleration_values = extract_valid_values("acceleration")
        if acceleration_values:
            wearable_features["acceleration"] = {
                "mean": mean(acceleration_values),
                "min": min(acceleration_values),
                "max": max(acceleration_values),
                "std": stdev(acceleration_values) if len(acceleration_values) > 1 else 0
            }
        
        return {"wearable_data": wearable_features}
    
    def _fuse_environment_data(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """融合环境传感器数据"""
        env_features = {
            "temperature": None,
            "humidity": None,
            "light_intensity": None,
            "co2_level": None,
            "smoke_level": None
        }
        
        # 辅助函数：从数据列表中提取指定字段的有效值
        def extract_valid_values(field: str) -> List[float]:
            return [float(data[field]) for data in data_list if field in data and data[field] is not None]
        
        # 对每个特征计算统计值
        temperature_values = extract_valid_values("temperature")
        if temperature_values:
            env_features["temperature"] = {
                "mean": mean(temperature_values),
                "min": min(temperature_values),
                "max": max(temperature_values)
            }
        
        humidity_values = extract_valid_values("humidity")
        if humidity_values:
            env_features["humidity"] = {
                "mean": mean(humidity_values),
                "min": min(humidity_values),
                "max": max(humidity_values)
            }
        
        light_intensity_values = extract_valid_values("light_intensity")
        if light_intensity_values:
            env_features["light_intensity"] = {
                "mean": mean(light_intensity_values),
                "min": min(light_intensity_values),
                "max": max(light_intensity_values)
            }
        
        co2_level_values = extract_valid_values("co2_level")
        if co2_level_values:
            env_features["co2_level"] = {
                "mean": mean(co2_level_values),
                "min": min(co2_level_values),
                "max": max(co2_level_values)
            }
        
        smoke_level_values = extract_valid_values("smoke_level")
        if smoke_level_values:
            env_features["smoke_level"] = {
                "mean": mean(smoke_level_values),
                "min": min(smoke_level_values),
                "max": max(smoke_level_values)
            }
        
        return {"environment_data": env_features}
    
    def _fuse_audio_data(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """融合音频数据"""
        audio_features = {
            "audio_present": len(data_list) > 0,
            "audio_sample_count": len(data_list)
        }
        
        return {"audio_data": audio_features}
    
    def _extract_features(self, fused_item: Dict[str, Any], original_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """提取融合特征"""
        features = {"fusion_features": {}}
        
        # 示例：提取心率与环境温度的相关性
        if "wearable_data" in fused_item and "environment_data" in fused_item:
            if fused_item["wearable_data"]["heart_rate"] and fused_item["environment_data"]["temperature"]:
                heart_rate_mean = fused_item["wearable_data"]["heart_rate"]["mean"]
                temp_mean = fused_item["environment_data"]["temperature"]["mean"]
                
                # 简单的舒适度评分
                if temp_mean >= 22 and temp_mean <= 26:
                    features["fusion_features"]["comfort_score"] = 1.0
                else:
                    features["fusion_features"]["comfort_score"] = max(0.0, 1.0 - abs(temp_mean - 24) / 10)
        
        # 示例：活动水平评分
        if "wearable_data" in fused_item:
            if fused_item["wearable_data"]["steps"]:
                steps_total = fused_item["wearable_data"]["steps"]["total"]
                # 根据步数计算活动水平
                if steps_total < 100:
                    activity_level = "low"
                elif steps_total < 500:
                    activity_level = "medium"
                else:
                    activity_level = "high"
                
                features["fusion_features"]["activity_level"] = activity_level
        
        # 示例：健康风险评分
        if "wearable_data" in fused_item:
            risk_score = 0.0
            
            # 心率风险
            if fused_item["wearable_data"]["heart_rate"]:
                hr_mean = fused_item["wearable_data"]["heart_rate"]["mean"]
                if hr_mean < 50 or hr_mean > 100:
                    risk_score += 0.5
            
            # 体温风险
            if fused_item["wearable_data"]["temperature"]:
                temp_mean = fused_item["wearable_data"]["temperature"]["mean"]
                if temp_mean < 36.0 or temp_mean > 37.5:
                    risk_score += 0.5
            
            features["fusion_features"]["health_risk_score"] = min(1.0, risk_score)
        
        return features
