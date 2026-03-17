from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import logging
from typing import Dict, Any, List
from datetime import datetime
from ..config.config_manager import config_manager

class InfluxDBStorage:
    """InfluxDB时序数据存储模块"""
    
    def __init__(self):
        """初始化InfluxDB存储模块"""
        self.config = config_manager.get_section("storage")["influxdb"]
        self.logger = logging.getLogger("InfluxDBStorage")
        
        # 连接到InfluxDB
        try:
            self.client = InfluxDBClient(
                url=self.config["url"],
                token=self.config["token"],
                org=self.config["org"]
            )
            
            # 测试连接
            health = self.client.health()
            if health.status == "pass":
                self.logger.info(f"成功连接到InfluxDB服务器: {self.config['url']}")
            else:
                self.logger.error(f"InfluxDB连接失败: {health}")
                self.client = None
                return
            
            # 获取写入API
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.bucket = self.config["bucket"]
            
        except Exception as e:
            self.logger.error(f"InfluxDB连接失败: {e}")
            self.client = None
            self.write_api = None
    
    def store_data(self, data: Dict[str, Any]) -> bool:
        """存储单条时序数据到InfluxDB"""
        if not self.client or not self.write_api:
            return False
        
        try:
            # 转换数据为InfluxDB Point
            point = self._data_to_point(data)
            
            # 写入数据
            self.write_api.write(bucket=self.bucket, org=self.config["org"], record=point)
            return True
            
        except Exception as e:
            self.logger.error(f"InfluxDB数据存储失败: {e}")
            return False
    
    def _data_to_point(self, data: Dict[str, Any]) -> Point:
        """将数据转换为InfluxDB Point"""
        # 确定测量名称（measurement）
        measurement = data.get("data_type", "unknown")
        
        # 创建Point对象
        point = Point(measurement)
        
        # 添加标签（tags）
        point.tag("protocol", data.get("protocol", "unknown"))
        
        # 添加用户ID作为标签（如果有）
        if "user_id" in data:
            point.tag("user_id", data["user_id"])
        
        # 添加设备ID作为标签（如果有）
        if "device_id" in data:
            point.tag("device_id", data["device_id"])
        
        # 添加时间戳（如果有）
        timestamp = data.get("timestamp")
        if timestamp:
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            point.time(timestamp)
        
        # 添加字段（fields）
        # 遍历数据，将数值类型的数据添加为字段
        for key, value in data.items():
            # 跳过已经处理过的字段
            if key in ["data_type", "protocol", "user_id", "device_id", "timestamp", "cleaned", "cleaned_at", "cleaning_error"]:
                continue
            
            # 只添加数值类型的数据作为字段
            if isinstance(value, (int, float)):
                point.field(key, value)
            # 对于复杂类型，转换为字符串
            elif isinstance(value, (dict, list)):
                import json
                point.field(key, json.dumps(value))
            # 对于其他类型，直接添加为字符串
            else:
                point.field(key, str(value))
        
        return point
    
    def store_batch_data(self, data_list: List[Dict[str, Any]]) -> bool:
        """批量存储时序数据到InfluxDB"""
        if not self.client or not self.write_api:
            return False
        
        try:
            # 转换数据为InfluxDB Point列表
            points = [self._data_to_point(data) for data in data_list]
            
            # 批量写入数据
            self.write_api.write(bucket=self.bucket, org=self.config["org"], record=points)
            return True
            
        except Exception as e:
            self.logger.error(f"InfluxDB批量数据存储失败: {e}")
            return False
    
    def query_data(self, query: str) -> List[Dict[str, Any]]:
        """查询InfluxDB数据"""
        if not self.client:
            return []
        
        try:
            # 使用查询API
            query_api = self.client.query_api()
            
            # 执行查询
            result = query_api.query(org=self.config["org"], query=query)
            
            # 处理查询结果
            data_list = []
            for table in result:
                for record in table.records:
                    data = {
                        "measurement": record.get_measurement(),
                        "time": record.get_time().isoformat() if record.get_time() else None,
                        **record.values
                    }
                    data_list.append(data)
            
            return data_list
            
        except Exception as e:
            self.logger.error(f"InfluxDB查询失败: {e}")
            return []
    
    def close(self) -> None:
        """关闭InfluxDB连接"""
        if self.write_api:
            self.write_api.close()
        if self.client:
            self.client.close()
            self.logger.info("InfluxDB连接已关闭")
