import redis
import json
import logging
from typing import Dict, Any, List
from ..config.config_manager import config_manager

class RedisStorage:
    """Redis实时数据存储模块"""
    
    def __init__(self):
        """初始化Redis存储模块"""
        self.config = config_manager.get_section("storage")["redis"]
        self.expire_time = self.config["expire_time"]
        
        self.logger = logging.getLogger("RedisStorage")
        
        # 连接到Redis
        try:
            self.client = redis.Redis(
                host=self.config["host"],
                port=self.config["port"],
                db=self.config["db"],
                password=self.config["password"] or None
            )
            # 测试连接
            self.client.ping()
            self.logger.info(f"成功连接到Redis服务器: {self.config['host']}:{self.config['port']}")
        except Exception as e:
            self.logger.error(f"Redis连接失败: {e}")
            self.client = None
    
    def store_data(self, data: Dict[str, Any]) -> bool:
        """存储单条数据到Redis"""
        if not self.client:
            return False
        
        try:
            # 生成Redis键
            data_type = data.get("data_type", "unknown")
            user_id = data.get("user_id", "anonymous")
            timestamp = data.get("timestamp", "")
            
            # 构建键名: data_type:user_id:timestamp
            key = f"{data_type}:{user_id}:{timestamp}"
            
            # 序列化数据
            serialized_data = json.dumps(data)
            
            # 存储数据并设置过期时间
            self.client.setex(key, self.expire_time, serialized_data)
            
            # 同时将键添加到集合中，方便按类型查询
            self.client.sadd(f"{data_type}:keys", key)
            self.client.sadd(f"user:{user_id}:keys", key)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Redis数据存储失败: {e}")
            return False
    
    def store_batch_data(self, data_list: List[Dict[str, Any]]) -> bool:
        """批量存储数据到Redis"""
        if not self.client or not data_list:
            return False
        
        try:
            for data in data_list:
                self.store_data(data)
            return True
        except Exception as e:
            self.logger.error(f"Redis批量数据存储失败: {e}")
            return False
    
    def get_data(self, key: str) -> Dict[str, Any] or None:
        """根据键获取数据"""
        if not self.client:
            return None
        
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            self.logger.error(f"Redis数据获取失败: {e}")
            return None
    
    def get_data_by_type(self, data_type: str, count: int = 100) -> List[Dict[str, Any]]:
        """根据数据类型获取最新数据"""
        if not self.client:
            return []
        
        try:
            # 获取该类型的所有键
            keys = self.client.smembers(f"{data_type}:keys")
            if not keys:
                return []
            
            # 转换为字符串列表
            keys = [key.decode("utf-8") for key in keys]
            
            # 按时间戳排序，获取最新的count条数据
            keys.sort(reverse=True)  # 假设键名中的timestamp是可排序的
            keys = keys[:count]
            
            # 获取数据
            data_list = []
            for key in keys:
                data = self.get_data(key)
                if data:
                    data_list.append(data)
            
            return data_list
            
        except Exception as e:
            self.logger.error(f"Redis按类型获取数据失败: {e}")
            return []
    
    def get_data_by_user(self, user_id: str, count: int = 100) -> List[Dict[str, Any]]:
        """根据用户ID获取最新数据"""
        if not self.client:
            return []
        
        try:
            # 获取该用户的所有键
            keys = self.client.smembers(f"user:{user_id}:keys")
            if not keys:
                return []
            
            # 转换为字符串列表
            keys = [key.decode("utf-8") for key in keys]
            
            # 按时间戳排序，获取最新的count条数据
            keys.sort(reverse=True)  # 假设键名中的timestamp是可排序的
            keys = keys[:count]
            
            # 获取数据
            data_list = []
            for key in keys:
                data = self.get_data(key)
                if data:
                    data_list.append(data)
            
            return data_list
            
        except Exception as e:
            self.logger.error(f"Redis按用户获取数据失败: {e}")
            return []
    
    def delete_data(self, key: str) -> bool:
        """删除指定键的数据"""
        if not self.client:
            return False
        
        try:
            # 删除数据
            self.client.delete(key)
            
            # 从集合中移除键
            # 这里需要解析键名来确定数据类型和用户ID
            parts = key.split(":")
            if len(parts) >= 2:
                data_type = parts[0]
                user_id = parts[1]
                self.client.srem(f"{data_type}:keys", key)
                self.client.srem(f"user:{user_id}:keys", key)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Redis数据删除失败: {e}")
            return False
    
    def close(self) -> None:
        """关闭Redis连接"""
        if self.client:
            self.client.close()
            self.logger.info("Redis连接已关闭")
