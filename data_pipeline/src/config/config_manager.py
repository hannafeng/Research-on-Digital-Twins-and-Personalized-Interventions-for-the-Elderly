import yaml
import os
from dotenv import load_dotenv
from typing import Dict, Any

class ConfigManager:
    """配置管理类，用于加载和管理配置文件"""
    
    def __init__(self, config_file: str = None):
        """初始化配置管理器"""
        # 获取当前脚本的绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建配置文件的绝对路径
        self.config_file = config_file or os.path.join(script_dir, "../../config/config.yaml")
        self.config: Dict[str, Any] = {}
        self._load_config()
        self._load_env_vars()
    
    def _load_config(self) -> None:
        """加载YAML配置文件"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"配置文件 {self.config_file} 未找到")
        except yaml.YAMLError as e:
            print(f"配置文件解析错误: {e}")
    
    def _load_env_vars(self) -> None:
        """加载环境变量"""
        load_dotenv()
        
        # 覆盖配置文件中的Redis配置
        if os.getenv("REDIS_HOST"):
            self.config["storage"]["redis"]["host"] = os.getenv("REDIS_HOST")
        if os.getenv("REDIS_PORT"):
            self.config["storage"]["redis"]["port"] = int(os.getenv("REDIS_PORT"))
        if os.getenv("REDIS_DB"):
            self.config["storage"]["redis"]["db"] = int(os.getenv("REDIS_DB"))
        if os.getenv("REDIS_PASSWORD"):
            self.config["storage"]["redis"]["password"] = os.getenv("REDIS_PASSWORD")
        if os.getenv("REDIS_EXPIRE_TIME"):
            self.config["storage"]["redis"]["expire_time"] = int(os.getenv("REDIS_EXPIRE_TIME"))
        
        # 覆盖配置文件中的PostgreSQL配置
        if os.getenv("POSTGRES_HOST"):
            self.config["storage"]["postgresql"]["host"] = os.getenv("POSTGRES_HOST")
        if os.getenv("POSTGRES_PORT"):
            self.config["storage"]["postgresql"]["port"] = int(os.getenv("POSTGRES_PORT"))
        if os.getenv("POSTGRES_DATABASE"):
            self.config["storage"]["postgresql"]["database"] = os.getenv("POSTGRES_DATABASE")
        if os.getenv("POSTGRES_USER"):
            self.config["storage"]["postgresql"]["user"] = os.getenv("POSTGRES_USER")
        if os.getenv("POSTGRES_PASSWORD"):
            self.config["storage"]["postgresql"]["password"] = os.getenv("POSTGRES_PASSWORD")
        
        # 覆盖配置文件中的InfluxDB配置
        if os.getenv("INFLUXDB_URL"):
            self.config["storage"]["influxdb"]["url"] = os.getenv("INFLUXDB_URL")
        if os.getenv("INFLUXDB_TOKEN"):
            self.config["storage"]["influxdb"]["token"] = os.getenv("INFLUXDB_TOKEN")
        if os.getenv("INFLUXDB_ORG"):
            self.config["storage"]["influxdb"]["org"] = os.getenv("INFLUXDB_ORG")
        if os.getenv("INFLUXDB_BUCKET"):
            self.config["storage"]["influxdb"]["bucket"] = os.getenv("INFLUXDB_BUCKET")
        
        # 覆盖配置文件中的Kafka配置
        if os.getenv("KAFKA_BOOTSTRAP_SERVERS"):
            self.config["message_queue"]["kafka"]["bootstrap_servers"] = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
        
        # 覆盖配置文件中的日志配置
        if os.getenv("LOG_LEVEL"):
            self.config["logging"]["level"] = os.getenv("LOG_LEVEL")
        if os.getenv("LOG_FILE"):
            self.config["logging"]["file"] = os.getenv("LOG_FILE")
        
        # 覆盖配置文件中的调度配置
        if os.getenv("SCHEDULE_INTERVAL"):
            self.config["scheduling"]["schedule_interval"] = int(os.getenv("SCHEDULE_INTERVAL"))
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self.config
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取指定配置节"""
        return self.config.get(section, {})
    
    def get_value(self, path: str, default: Any = None) -> Any:
        """获取指定路径的配置值，例如：get_value("storage.redis.host")"""
        keys = path.split(".")
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value

# 创建全局配置实例
config_manager = ConfigManager()
