import asyncio
from bleak import BleakScanner, BleakClient
import logging
from typing import Dict, Any, Callable
from datetime import datetime
from ...config.config_manager import config_manager

class BleCollector:
    """BLE协议数据采集器"""
    
    def __init__(self, data_callback: Callable[[Dict[str, Any]], None]):
        """初始化BLE采集器"""
        self.config = config_manager.get_section("collection")["wearable"]
        self.scan_interval = self.config["ble_scan_interval"]
        
        self.data_callback = data_callback
        self.devices = {}
        self.logger = logging.getLogger("BleCollector")
        self.running = False
        
    async def scan_devices(self) -> None:
        """扫描BLE设备"""
        self.logger.info(f"开始扫描BLE设备，扫描间隔: {self.scan_interval}秒")
        
        while self.running:
            try:
                # 扫描设备
                devices = await BleakScanner.discover()
                
                for device in devices:
                    # 只处理可穿戴设备（这里可以根据设备名称或UUID进行过滤）
                    if "wearable" in device.name.lower() or "watch" in device.name.lower() or "band" in device.name.lower():
                        if device.address not in self.devices:
                            self.devices[device.address] = device
                            self.logger.info(f"发现新的可穿戴设备: {device.name} ({device.address})")
                            # 连接到设备
                            asyncio.create_task(self.connect_device(device))
                
            except Exception as e:
                self.logger.error(f"BLE设备扫描失败: {e}")
            
            # 等待指定间隔后再次扫描
            await asyncio.sleep(self.scan_interval)
    
    async def connect_device(self, device: Any) -> None:
        """连接到BLE设备"""
        async with BleakClient(device.address) as client:
            self.logger.info(f"已连接到设备: {device.name} ({device.address})")
            
            try:
                # 获取设备服务和特征
                services = client.services
                
                for service in services:
                    self.logger.debug(f"服务: {service.uuid}")
                    
                    for characteristic in service.characteristics:
                        self.logger.debug(f"  特征: {characteristic.uuid} - 可读: {characteristic.properties.read} - 可写: {characteristic.properties.write} - 通知: {characteristic.properties.notify}")
                        
                        # 如果特征支持通知，订阅通知
                        if characteristic.properties.notify:
                            await client.start_notify(characteristic.uuid, self.notification_handler)
                            self.logger.info(f"已订阅特征通知: {characteristic.uuid} (设备: {device.name})")
                        
                        # 如果特征可读，读取一次数据
                        if characteristic.properties.read:
                            value = await client.read_gatt_char(characteristic.uuid)
                            self.process_ble_data(device, characteristic.uuid, value)
                
                # 保持连接，接收通知
                while self.running and client.is_connected:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"与设备通信失败 {device.name} ({device.address}): {e}")
            finally:
                self.logger.info(f"断开与设备的连接: {device.name} ({device.address})")
    
    def notification_handler(self, sender: Any, data: Any) -> None:
        """BLE通知处理函数"""
        # 这里需要根据具体设备的协议解析数据
        self.logger.debug(f"收到BLE通知，发送者: {sender}, 数据: {data.hex()}")
    
    def process_ble_data(self, device: Any, characteristic_uuid: str, value: bytes) -> None:
        """处理BLE数据"""
        try:
            # 这里需要根据具体设备的协议解析数据
            # 示例：假设数据是JSON格式的字符串
            data_str = value.decode("utf-8")
            import json
            data = json.loads(data_str)
            
            # 添加设备信息和时间戳
            data["device_name"] = device.name
            data["device_address"] = device.address
            data["timestamp"] = datetime.now().isoformat()
            data["data_type"] = "wearable"
            data["protocol"] = "ble"
            
            # 调用回调函数处理数据
            self.data_callback(data)
            
        except Exception as e:
            self.logger.error(f"处理BLE数据失败: {e}")
    
    def start(self) -> None:
        """启动BLE采集器"""
        self.running = True
        self.logger.info("BLE采集器已启动")
        asyncio.create_task(self.scan_devices())
    
    def stop(self) -> None:
        """停止BLE采集器"""
        self.running = False
        self.logger.info("BLE采集器已停止")
