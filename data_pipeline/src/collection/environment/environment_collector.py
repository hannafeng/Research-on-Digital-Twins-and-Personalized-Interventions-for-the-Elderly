from typing import Dict, Any, Callable
import logging
from .mqtt_collector import MqttCollector
from .http_collector import HttpCollector
from ...config.config_manager import config_manager

class EnvironmentCollector:
    """环境传感器数据采集管理器"""
    
    def __init__(self, data_callback: Callable[[Dict[str, Any]], None]):
        """初始化环境传感器采集管理器"""
        self.config = config_manager.get_section("data_sources")["environment"]
        self.data_callback = data_callback
        self.collectors = []
        self.logger = logging.getLogger("EnvironmentCollector")
        
        # 初始化采集器
        self._init_collectors()
    
    def _init_collectors(self) -> None:
        """初始化采集器"""
        # 如果启用了MQTT协议，初始化MQTT采集器
        if "mqtt" in self.config["protocols"]:
            mqtt_collector = MqttCollector(self.data_callback)
            self.collectors.append(mqtt_collector)
            self.logger.info("已初始化环境传感器MQTT采集器")
        
        # 如果启用了HTTP协议，初始化HTTP采集器
        if "http" in self.config["protocols"]:
            http_collector = HttpCollector(self.data_callback)
            self.collectors.append(http_collector)
            self.logger.info("已初始化环境传感器HTTP采集器")
    
    def start(self) -> None:
        """启动所有采集器"""
        self.logger.info("启动环境传感器数据采集")
        for collector in self.collectors:
            collector.start()
    
    def stop(self) -> None:
        """停止所有采集器"""
        self.logger.info("停止环境传感器数据采集")
        for collector in self.collectors:
            collector.stop()
    
    def get_collector_count(self) -> int:
        """获取采集器数量"""
        return len(self.collectors)
