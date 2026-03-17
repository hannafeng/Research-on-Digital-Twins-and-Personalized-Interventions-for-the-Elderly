import aiohttp
import asyncio
import json
import logging
from typing import Dict, Any, Callable
from datetime import datetime
from ...config.config_manager import config_manager

class HttpCollector:
    """HTTP协议环境传感器数据采集器"""
    
    def __init__(self, data_callback: Callable[[Dict[str, Any]], None]):
        """初始化HTTP采集器"""
        self.config = config_manager.get_section("collection")["environment"]
        self.http_config = {
            "endpoint": self.config["http_endpoint"],
            "interval": 60,  # 秒，默认60秒采集一次
            "timeout": 10     # 秒，请求超时时间
        }
        
        self.data_callback = data_callback
        self.running = False
        self.logger = logging.getLogger("EnvironmentHttpCollector")
        
    async def _fetch_data(self) -> None:
        """从HTTP端点获取数据"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.http_config["endpoint"], timeout=self.http_config["timeout"]) as response:
                    if response.status == 200:
                        # 解析响应数据
                        data = await response.json()
                        
                        # 如果返回的是列表，逐个处理
                        if isinstance(data, list):
                            for item in data:
                                # 添加数据类型和协议信息
                                item["data_type"] = "environment"
                                item["protocol"] = "http"
                                item["timestamp"] = datetime.now().isoformat()
                                
                                # 调用回调函数处理数据
                                self.data_callback(item)
                        else:
                            # 单个数据项
                            data["data_type"] = "environment"
                            data["protocol"] = "http"
                            data["timestamp"] = datetime.now().isoformat()
                            
                            # 调用回调函数处理数据
                            self.data_callback(data)
                        
                        self.logger.debug(f"从HTTP端点获取数据成功: {self.http_config['endpoint']}")
                    else:
                        self.logger.error(f"HTTP请求失败，状态码: {response.status}, 端点: {self.http_config['endpoint']}")
        
        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP客户端错误: {e}, 端点: {self.http_config['endpoint']}")
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误: {e}, 端点: {self.http_config['endpoint']}")
        except Exception as e:
            self.logger.error(f"处理HTTP请求时出错: {e}, 端点: {self.http_config['endpoint']}")
    
    async def _collect_data_loop(self) -> None:
        """数据采集循环"""
        while self.running:
            await self._fetch_data()
            await asyncio.sleep(self.http_config["interval"])
    
    def start(self) -> None:
        """启动HTTP采集器"""
        self.running = True
        self.logger.info(f"启动环境传感器HTTP采集器，采集间隔: {self.http_config['interval']}秒")
        asyncio.create_task(self._collect_data_loop())
    
    def stop(self) -> None:
        """停止HTTP采集器"""
        self.running = False
        self.logger.info("停止环境传感器HTTP采集器")
