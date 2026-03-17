import asyncio
import websockets
import logging
import base64
from typing import Dict, Any, Callable
from datetime import datetime
from ...config.config_manager import config_manager

class WebSocketCollector:
    """WebSocket协议音频数据采集器"""
    
    def __init__(self, data_callback: Callable[[Dict[str, Any]], None]):
        """初始化WebSocket采集器"""
        self.config = config_manager.get_section("collection")["audio"]
        self.ws_config = {
            "url": self.config["websocket_url"],
            "buffer_size": self.config["buffer_size"]
        }
        
        self.data_callback = data_callback
        self.running = False
        self.logger = logging.getLogger("AudioWebSocketCollector")
        
    async def _connect_and_collect(self) -> None:
        """连接到WebSocket服务器并采集数据"""
        while self.running:
            try:
                self.logger.info(f"尝试连接到WebSocket服务器: {self.ws_config['url']}")
                
                async with websockets.connect(self.ws_config['url']) as websocket:
                    self.logger.info(f"成功连接到WebSocket服务器: {self.ws_config['url']}")
                    
                    while self.running:
                        # 接收音频数据
                        audio_data = await websocket.recv()
                        
                        # 处理音频数据
                        self._process_audio_data(audio_data)
                        
            except websockets.exceptions.ConnectionClosedError as e:
                self.logger.error(f"WebSocket连接关闭: {e}")
                # 等待一段时间后重试连接
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"WebSocket采集器错误: {e}")
                # 等待一段时间后重试连接
                await asyncio.sleep(5)
    
    def _process_audio_data(self, audio_data: Any) -> None:
        """处理音频数据"""
        try:
            # 构建数据对象
            data = {
                "data_type": "audio",
                "protocol": "websocket",
                "timestamp": datetime.now().isoformat(),
                "audio_format": "raw",
                "sampling_rate": config_manager.get_value("data_sources.audio.sampling_rate"),
                "channels": config_manager.get_value("data_sources.audio.channels"),
                "sample_width": config_manager.get_value("data_sources.audio.sample_width")
            }
            
            # 如果是二进制数据，转换为base64编码的字符串
            if isinstance(audio_data, bytes):
                data["audio_data"] = base64.b64encode(audio_data).decode("utf-8")
                data["encoding"] = "base64"
            else:
                # 假设是已经编码的字符串
                data["audio_data"] = audio_data
                data["encoding"] = "utf-8"
            
            # 调用回调函数处理数据
            self.data_callback(data)
            
        except Exception as e:
            self.logger.error(f"处理音频数据失败: {e}")
    
    def start(self) -> None:
        """启动WebSocket采集器"""
        self.logger.info("启动音频数据采集")
        self.running = True
        asyncio.create_task(self._connect_and_collect())
    
    def stop(self) -> None:
        """停止WebSocket采集器"""
        self.logger.info("停止音频数据采集")
        self.running = False
