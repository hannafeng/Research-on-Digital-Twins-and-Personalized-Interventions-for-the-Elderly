from typing import Dict, Any, Callable, List
import logging
from .mqtt_collector import MqttCollector
from ...config.config_manager import config_manager

# 尝试导入BLE采集器，若失败则跳过
BLE_AVAILABLE = False
try:
    from .ble_collector import BleCollector
    BLE_AVAILABLE = True
except ImportError:
    logging.getLogger("WearableCollector").warning("BLE模块不可用，跳过BLE采集功能")

class WearableCollector:
    """可穿戴设备数据采集管理器"""
    
    def __init__(self, data_callback: Callable[[Dict[str, Any]], None]):
        """初始化可穿戴设备采集管理器"""
        self.config = config_manager.get_section("data_sources")["wearable"]
        self.data_callback = data_callback
        self.collectors = []
        self.logger = logging.getLogger("WearableCollector")
        
        # 初始化采集器
        self._init_collectors()
    
    def _init_collectors(self) -> None:
        """初始化采集器"""
        # 如果启用了MQTT协议，初始化MQTT采集器
        if "mqtt" in self.config["protocols"]:
            mqtt_collector = MqttCollector(self.data_callback)
            self.collectors.append(mqtt_collector)
            self.logger.info("已初始化MQTT采集器")
        
        # 如果启用了BLE协议且BLE模块可用，初始化BLE采集器
        if "ble" in self.config["protocols"] and BLE_AVAILABLE:
            ble_collector = BleCollector(self.data_callback)
            self.collectors.append(ble_collector)
            self.logger.info("已初始化BLE采集器")
        elif "ble" in self.config["protocols"] and not BLE_AVAILABLE:
            self.logger.warning("BLE协议已启用，但BLE模块不可用，无法初始化BLE采集器")
    
    def start(self) -> None:
        """启动所有采集器"""
        self.logger.info("启动可穿戴设备数据采集")
        for collector in self.collectors:
            collector.start()
    
    def stop(self) -> None:
        """停止所有采集器"""
        self.logger.info("停止可穿戴设备数据采集")
        for collector in self.collectors:
            collector.stop()
    
    def get_collector_count(self) -> int:
        """获取采集器数量"""
        return len(self.collectors)
