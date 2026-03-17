from typing import Dict, Any, Callable
import logging
from .websocket_collector import WebSocketCollector
from ...config.config_manager import config_manager

class AudioCollector:
    """音频数据采集管理器"""
    
    def __init__(self, data_callback: Callable[[Dict[str, Any]], None]):
        """初始化音频数据采集管理器"""
        self.config = config_manager.get_section("data_sources")["audio"]
        self.data_callback = data_callback
        self.collectors = []
        self.logger = logging.getLogger("AudioCollector")
        
        # 初始化采集器
        self._init_collectors()
    
    def _init_collectors(self) -> None:
        """初始化采集器"""
        # 音频数据目前只支持WebSocket协议
        if self.config["enabled"]:
            ws_collector = WebSocketCollector(self.data_callback)
            self.collectors.append(ws_collector)
            self.logger.info("已初始化音频WebSocket采集器")
    
    def start(self) -> None:
        """启动所有采集器"""
        self.logger.info("启动音频数据采集")
        for collector in self.collectors:
            collector.start()
    
    def stop(self) -> None:
        """停止所有采集器"""
        self.logger.info("停止音频数据采集")
        for collector in self.collectors:
            collector.stop()
    
    def get_collector_count(self) -> int:
        """获取采集器数量"""
        return len(self.collectors)
