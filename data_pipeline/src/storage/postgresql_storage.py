import psycopg2
import logging
from typing import Dict, Any, List
from datetime import datetime
from ..config.config_manager import config_manager

class PostgreSQLStorage:
    """PostgreSQL结构化数据存储模块"""
    
    def __init__(self):
        """初始化PostgreSQL存储模块"""
        self.config = config_manager.get_section("storage")["postgresql"]
        
        self.logger = logging.getLogger("PostgreSQLStorage")
        
        # 连接到PostgreSQL
        try:
            self.connection = psycopg2.connect(
                host=self.config["host"],
                port=self.config["port"],
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"]
            )
            self.cursor = self.connection.cursor()
            self.logger.info(f"成功连接到PostgreSQL服务器: {self.config['host']}:{self.config['port']}/{self.config['database']}")
            
            # 初始化数据库表（如果不存在）
            self._init_tables()
            
        except Exception as e:
            self.logger.error(f"PostgreSQL连接失败: {e}")
            self.connection = None
            self.cursor = None
    
    def _init_tables(self) -> None:
        """初始化数据库表"""
        if not self.connection or not self.cursor:
            return
        
        try:
            # 创建用户表（基础信息层）
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(100),
                    age INTEGER,
                    gender VARCHAR(10),
                    # 基础信息层字段
                    chronic_diseases JSONB,  -- 慢性病信息，如{"hypertension": true, "diabetes": false}
                    allergies JSONB,  -- 过敏史，如{"medication": ["penicillin"], "food": ["peanuts"]}
                    preferences JSONB,  -- 偏好信息，如{"music": ["classical", "jazz"], "activities": ["reading"]}
                    emergency_contact JSONB,  -- 紧急联系人信息
                    medical_history JSONB,  -- 医疗历史
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建设备表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id SERIAL PRIMARY KEY,
                    device_id VARCHAR(50) UNIQUE NOT NULL,
                    device_type VARCHAR(50) NOT NULL,
                    user_id VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # 创建事件表
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    event_id VARCHAR(50) UNIQUE NOT NULL,
                    user_id VARCHAR(50),
                    event_type VARCHAR(50) NOT NULL,
                    event_data JSONB,
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            self.connection.commit()
            self.logger.info("PostgreSQL表初始化完成")
            
        except Exception as e:
            self.logger.error(f"PostgreSQL表初始化失败: {e}")
            self.connection.rollback()
    
    def store_data(self, data: Dict[str, Any]) -> bool:
        """存储单条数据到PostgreSQL"""
        if not self.connection or not self.cursor:
            return False
        
        try:
            # 根据数据类型选择存储表
            if data.get("data_type") == "event":
                return self._store_event(data)
            elif data.get("data_type") == "user":
                return self._store_user(data)
            elif data.get("data_type") == "device":
                return self._store_device(data)
            else:
                # 默认存储为事件
                return self._store_event(data)
                
        except Exception as e:
            self.logger.error(f"PostgreSQL数据存储失败: {e}")
            self.connection.rollback()
            return False
    
    def _store_event(self, data: Dict[str, Any]) -> bool:
        """存储事件数据"""
        try:
            event_id = data.get("event_id", "")
            user_id = data.get("user_id", "")
            event_type = data.get("event_type", "unknown")
            event_data = data
            timestamp = data.get("timestamp", datetime.now())
            
            # 转换timestamp为datetime对象
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            # 插入事件数据
            self.cursor.execute("""
                INSERT INTO events (event_id, user_id, event_type, event_data, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (event_id) DO UPDATE
                SET event_type = EXCLUDED.event_type,
                    event_data = EXCLUDED.event_data,
                    timestamp = EXCLUDED.timestamp
            """, (event_id, user_id, event_type, event_data, timestamp))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"事件数据存储失败: {e}")
            self.connection.rollback()
            return False
    
    def _store_user(self, data: Dict[str, Any]) -> bool:
        """存储用户数据"""
        try:
            user_id = data.get("user_id", "")
            name = data.get("name", "")
            age = data.get("age", 0)
            gender = data.get("gender", "")
            chronic_diseases = data.get("chronic_diseases", {})
            allergies = data.get("allergies", {})
            preferences = data.get("preferences", {})
            emergency_contact = data.get("emergency_contact", {})
            medical_history = data.get("medical_history", {})
            
            # 插入或更新用户数据
            self.cursor.execute("""
                INSERT INTO users (user_id, name, age, gender, chronic_diseases, allergies, preferences, emergency_contact, medical_history, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE
                SET name = EXCLUDED.name,
                    age = EXCLUDED.age,
                    gender = EXCLUDED.gender,
                    chronic_diseases = EXCLUDED.chronic_diseases,
                    allergies = EXCLUDED.allergies,
                    preferences = EXCLUDED.preferences,
                    emergency_contact = EXCLUDED.emergency_contact,
                    medical_history = EXCLUDED.medical_history,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, name, age, gender, chronic_diseases, allergies, preferences, emergency_contact, medical_history))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"用户数据存储失败: {e}")
            self.connection.rollback()
            return False
    
    def _store_device(self, data: Dict[str, Any]) -> bool:
        """存储设备数据"""
        try:
            device_id = data.get("device_id", "")
            device_type = data.get("device_type", "")
            user_id = data.get("user_id", "")
            status = data.get("status", "active")
            
            # 插入或更新设备数据
            self.cursor.execute("""
                INSERT INTO devices (device_id, device_type, user_id, status, updated_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (device_id) DO UPDATE
                SET device_type = EXCLUDED.device_type,
                    user_id = EXCLUDED.user_id,
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
            """, (device_id, device_type, user_id, status))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"设备数据存储失败: {e}")
            self.connection.rollback()
            return False
    
    def store_batch_data(self, data_list: List[Dict[str, Any]]) -> bool:
        """批量存储数据到PostgreSQL"""
        if not self.connection or not self.cursor:
            return False
        
        try:
            for data in data_list:
                self.store_data(data)
            return True
        except Exception as e:
            self.logger.error(f"PostgreSQL批量数据存储失败: {e}")
            self.connection.rollback()
            return False
    
    def get_user(self, user_id: str) -> Dict[str, Any] or None:
        """根据用户ID获取用户信息"""
        if not self.connection or not self.cursor:
            return None
        
        try:
            self.cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            user = self.cursor.fetchone()
            
            if user:
                return {
                    "id": user[0],
                    "user_id": user[1],
                    "name": user[2],
                    "age": user[3],
                    "gender": user[4],
                    "chronic_diseases": user[5],
                    "allergies": user[6],
                    "preferences": user[7],
                    "emergency_contact": user[8],
                    "medical_history": user[9],
                    "created_at": user[10].isoformat() if user[10] else None,
                    "updated_at": user[11].isoformat() if user[11] else None
                }
            return None
            
        except Exception as e:
            self.logger.error(f"获取用户信息失败: {e}")
            return None
    
    def close(self) -> None:
        """关闭PostgreSQL连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            self.logger.info("PostgreSQL连接已关闭")
