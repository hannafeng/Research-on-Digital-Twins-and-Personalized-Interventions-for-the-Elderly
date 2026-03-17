import paho.mqtt.client as mqtt
import json
import logging
from typing import Dict, Any, Callable
from ...config.config_manager import config_manager

class MqttCollector:
    """MQTT协议环境传感器数据采集器"""
    
    def __init__(self, data_callback: Callable[[Dict[str, Any]], None]):
        """初始化MQTT采集器"""
        self.config = config_manager.get_section("collection")["environment"]
        self.mqtt_config = {
            "broker_host": "localhost",
            "broker_port": 1883,
            "client_id": "environment_mqtt_collector",
            "topic": self.config["mqtt_topic"]
        }
        
        self.data_callback = data_callback
        self.client = None
        self.logger = logging.getLogger("EnvironmentMqttCollector")
        
    def on_connect(self, client: mqtt.Client, userdata: Any, flags: Dict[str, Any], rc: int) -> None:
        """MQTT连接回调函数"""
        if rc == 0:
            self.logger.info(f"成功连接到MQTT broker: {self.mqtt_config['broker_host']}:{self.mqtt_config['broker_port']}")
            client.subscribe(self.mqtt_config["topic"])
            self.logger.info(f"订阅主题: {self.mqtt_config['topic']}")
        else:
            self.logger.error(f"MQTT连接失败，错误代码: {rc}")
    
    def on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        """MQTT消息回调函数"""
        try:
            # 解析消息
            payload = msg.payload.decode("utf-8")
            data = json.loads(payload)
            
            # 添加数据类型和协议信息
            data["data_type"] = "environment"
            data["protocol"] = "mqtt"
            
            # 调用回调函数处理数据
            self.data_callback(data)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误: {e}")
        except Exception as e:
            self.logger.error(f"处理MQTT消息时出错: {e}")
    
    def start(self) -> None:
        """启动MQTT采集器"""
        try:
            # 创建MQTT客户端
            self.client = mqtt.Client(client_id=self.mqtt_config["client_id"])
            
            # 设置回调函数
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            
            # 连接到MQTT broker
            self.client.connect(
                self.mqtt_config["broker_host"],
                self.mqtt_config["broker_port"]
            )
            
            # 启动MQTT客户端循环
            self.client.loop_start()
            self.logger.info("环境传感器MQTT采集器已启动")
            
        except Exception as e:
            self.logger.error(f"启动环境传感器MQTT采集器失败: {e}")
    
    def stop(self) -> None:
        """停止MQTT采集器"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.logger.info("环境传感器MQTT采集器已停止")
