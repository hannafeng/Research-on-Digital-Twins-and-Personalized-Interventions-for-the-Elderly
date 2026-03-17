from typing import Dict, Any, List, Optional
import logging
from ..config.config_manager import config_manager

class StorageManager:
    """存储管理器，统一管理多种存储方式"""
    
    def __init__(self):
        """初始化存储管理器"""
        self.logger = logging.getLogger("StorageManager")
        
        # 初始化各种存储模块，支持优雅降级
        self.redis_storage = None
        self.postgresql_storage = None
        self.influxdb_storage = None
        
        # 尝试导入并初始化Redis存储
        try:
            from .redis_storage import RedisStorage
            self.redis_storage = RedisStorage()
            self.logger.info("Redis存储模块初始化成功")
        except ImportError as e:
            self.logger.warning(f"Redis存储模块不可用: {e}")
        except Exception as e:
            self.logger.error(f"Redis存储模块初始化失败: {e}")
        
        # 尝试导入并初始化PostgreSQL存储
        try:
            from .postgresql_storage import PostgreSQLStorage
            self.postgresql_storage = PostgreSQLStorage()
            self.logger.info("PostgreSQL存储模块初始化成功")
        except ImportError as e:
            self.logger.warning(f"PostgreSQL存储模块不可用: {e}")
        except Exception as e:
            self.logger.error(f"PostgreSQL存储模块初始化失败: {e}")
        
        # 尝试导入并初始化InfluxDB存储
        try:
            from .influxdb_storage import InfluxDBStorage
            self.influxdb_storage = InfluxDBStorage()
            self.logger.info("InfluxDB存储模块初始化成功")
        except ImportError as e:
            self.logger.warning(f"InfluxDB存储模块不可用: {e}")
        except Exception as e:
            self.logger.error(f"InfluxDB存储模块初始化失败: {e}")
        
        self.logger.info("存储管理器初始化完成")
    
    def store_data(self, data: Dict[str, Any]) -> bool:
        """存储数据到所有适用的存储系统"""
        try:
            # 1. 存储到Redis（实时数据，用于数字孪生体更新）
            redis_result = True
            if self.redis_storage:
                redis_result = self.redis_storage.store_data(data)
            else:
                self.logger.debug("Redis存储模块不可用，跳过Redis存储")
            
            # 2. 存储到InfluxDB（时序数据，用于历史分析和AI模型）
            influx_result = True
            if self.influxdb_storage:
                influx_result = self.influxdb_storage.store_data(data)
            else:
                self.logger.debug("InfluxDB存储模块不可用，跳过InfluxDB存储")
            
            # 3. 根据数据类型决定是否存储到PostgreSQL
            pg_result = True
            if data.get("data_type") in ["user", "device", "event"]:
                if self.postgresql_storage:
                    pg_result = self.postgresql_storage.store_data(data)
                else:
                    self.logger.debug("PostgreSQL存储模块不可用，跳过PostgreSQL存储")
            else:
                pg_result = True  # 非结构化数据不需要存储到PostgreSQL
            
            # 返回综合结果
            return redis_result and influx_result and pg_result
            
        except Exception as e:
            self.logger.error(f"数据存储失败: {e}")
            return False
    
    def store_batch_data(self, data_list: List[Dict[str, Any]]) -> bool:
        """批量存储数据"""
        try:
            # 1. 批量存储到Redis
            redis_result = True
            if self.redis_storage:
                redis_result = self.redis_storage.store_batch_data(data_list)
            else:
                self.logger.debug("Redis存储模块不可用，跳过Redis批量存储")
            
            # 2. 批量存储到InfluxDB
            influx_result = True
            if self.influxdb_storage:
                influx_result = self.influxdb_storage.store_batch_data(data_list)
            else:
                self.logger.debug("InfluxDB存储模块不可用，跳过InfluxDB批量存储")
            
            # 3. 分离不同类型的数据，批量存储到PostgreSQL
            user_data = [data for data in data_list if data.get("data_type") == "user"]
            device_data = [data for data in data_list if data.get("data_type") == "device"]
            event_data = [data for data in data_list if data.get("data_type") == "event"]
            
            pg_result = True
            if self.postgresql_storage:
                if user_data:
                    pg_result = pg_result and self.postgresql_storage.store_batch_data(user_data)
                if device_data:
                    pg_result = pg_result and self.postgresql_storage.store_batch_data(device_data)
                if event_data:
                    pg_result = pg_result and self.postgresql_storage.store_batch_data(event_data)
            else:
                self.logger.debug("PostgreSQL存储模块不可用，跳过PostgreSQL批量存储")
            
            # 返回综合结果
            return redis_result and influx_result and pg_result
            
        except Exception as e:
            self.logger.error(f"批量数据存储失败: {e}")
            return False
    
    def get_real_time_data(self, data_type: str = None, user_id: str = None, count: int = 100) -> List[Dict[str, Any]]:
        """获取实时数据（从Redis）"""
        try:
            if not self.redis_storage:
                self.logger.warning("Redis存储模块不可用，无法获取实时数据")
                return []
            
            if user_id:
                return self.redis_storage.get_data_by_user(user_id, count)
            elif data_type:
                return self.redis_storage.get_data_by_type(data_type, count)
            else:
                # 获取所有类型的最新数据
                all_data = []
                for data_type in ["wearable", "environment", "audio", "event"]:
                    data = self.redis_storage.get_data_by_type(data_type, count)
                    all_data.extend(data)
                # 按时间戳排序
                all_data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                return all_data[:count]
                
        except Exception as e:
            self.logger.error(f"获取实时数据失败: {e}")
            return []
    
    def get_historical_data(self, query: str) -> List[Dict[str, Any]]:
        """获取历史数据（从InfluxDB）"""
        try:
            if not self.influxdb_storage:
                self.logger.warning("InfluxDB存储模块不可用，无法获取历史数据")
                return []
            return self.influxdb_storage.query_data(query)
        except Exception as e:
            self.logger.error(f"获取历史数据失败: {e}")
            return []
    
    def get_user_info(self, user_id: str) -> Dict[str, Any] or None:
        """获取用户信息（从PostgreSQL）"""
        try:
            if not self.postgresql_storage:
                self.logger.warning("PostgreSQL存储模块不可用，无法获取用户信息")
                return None
            return self.postgresql_storage.get_user(user_id)
        except Exception as e:
            self.logger.error(f"获取用户信息失败: {e}")
            return None
    
    def close(self) -> None:
        """关闭所有存储连接"""
        if self.redis_storage:
            try:
                self.redis_storage.close()
                self.logger.info("Redis连接已关闭")
            except Exception as e:
                self.logger.error(f"关闭Redis连接失败: {e}")
        
        if self.postgresql_storage:
            try:
                self.postgresql_storage.close()
                self.logger.info("PostgreSQL连接已关闭")
            except Exception as e:
                self.logger.error(f"关闭PostgreSQL连接失败: {e}")
        
        if self.influxdb_storage:
            try:
                self.influxdb_storage.close()
                self.logger.info("InfluxDB连接已关闭")
            except Exception as e:
                self.logger.error(f"关闭InfluxDB连接失败: {e}")
        
        self.logger.info("所有存储连接已关闭")
