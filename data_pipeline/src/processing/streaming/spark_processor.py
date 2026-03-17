from pyspark.sql import SparkSession
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from ...config.config_manager import config_manager
from ..cleaning.data_cleaner import DataCleaner
from ..fusion.data_fuser import DataFuser
from ...storage.storage_manager import StorageManager

class SparkProcessor:
    """Spark Streaming数据处理模块"""
    
    def __init__(self):
        """初始化Spark Streaming处理器"""
        self.config = config_manager.get_section("processing")
        self.kafka_config = config_manager.get_section("message_queue")["kafka"]
        self.logger = logging.getLogger("SparkProcessor")
        self.data_cleaner = DataCleaner()
        self.data_fuser = DataFuser()
        self.storage_manager = StorageManager()
        self.spark = None
        self.ssc = None
    
    def initialize(self) -> None:
        """初始化Spark和StreamingContext"""
        try:
            # 创建SparkSession
            self.spark = SparkSession.builder \
                .appName("ElderlyCareDataPipeline") \
                .master("local[*]") \
                .config("spark.streaming.kafka.maxRatePerPartition", "100") \
                .config("spark.streaming.backpressure.enabled", "true") \
                .getOrCreate()
            
            # 设置日志级别
            self.spark.sparkContext.setLogLevel("WARN")
            
            # 创建StreamingContext，批处理间隔为5秒
            self.ssc = StreamingContext(self.spark.sparkContext, 5)
            
            self.logger.info("Spark Streaming初始化成功")
            
        except Exception as e:
            self.logger.error(f"Spark Streaming初始化失败: {e}")
            raise
    
    def create_kafka_stream(self) -> Any:
        """创建Kafka输入流"""
        try:
            # 从Kafka读取数据
            kafka_params = {
                "bootstrap.servers": self.kafka_config["bootstrap_servers"],
                "group.id": self.kafka_config["group_id"],
                "auto.offset.reset": "latest"
            }
            
            # 订阅原始数据主题
            topics = self.kafka_config["topics"]
            
            # 创建Kafka流
            kafka_stream = KafkaUtils.createDirectStream(
                self.ssc,
                topics,
                kafka_params
            )
            
            self.logger.info(f"已创建Kafka流，订阅主题: {topics}")
            return kafka_stream
            
        except Exception as e:
            self.logger.error(f"创建Kafka流失败: {e}")
            raise
    
    def process_stream(self, kafka_stream: Any) -> None:
        """处理数据流"""
        try:
            # 解析Kafka消息
            parsed_stream = kafka_stream.map(lambda x: self._parse_message(x[1]))
            
            # 过滤无效数据
            valid_stream = parsed_stream.filter(lambda x: x is not None)
            
            # 实时数据清洗
            cleaned_stream = valid_stream.map(lambda x: self.data_cleaner.clean_data(x))
            
            # 按用户ID分组（如果有）
            grouped_stream = cleaned_stream.transform(lambda rdd: self._group_by_user(rdd))
            
            # 时间窗口处理（60秒窗口，5秒滑动）
            windowed_stream = grouped_stream.window(60, 5)
            
            # 数据融合
            fused_stream = windowed_stream.map(lambda x: self._fuse_window_data(x))
            
            # 特征提取
            featured_stream = fused_stream.map(lambda x: self._extract_features(x))
            
            # 输出处理结果
            featured_stream.foreachRDD(lambda rdd: self._output_results(rdd))
            
        except Exception as e:
            self.logger.error(f"处理流数据失败: {e}")
            raise
    
    def _parse_message(self, message: str) -> Dict[str, Any]:
        """解析Kafka消息"""
        try:
            data = json.loads(message)
            # 确保数据包含必要字段
            if "timestamp" not in data:
                data["timestamp"] = datetime.now().isoformat()
            if "data_type" not in data:
                data["data_type"] = "unknown"
            return data
        except json.JSONDecodeError as e:
            self.logger.error(f"解析消息失败: {e}")
            return None
    
    def _group_by_user(self, rdd: Any) -> Any:
        """按用户ID分组"""
        def group_func(data):
            user_id = data.get("user_id", "default")
            return (user_id, data)
        
        return rdd.map(group_func)
    
    def _fuse_window_data(self, user_data: tuple) -> Dict[str, Any]:
        """融合窗口数据"""
        user_id, data_list = user_data
        
        if not data_list:
            return None
        
        try:
            # 使用现有的DataFuser进行融合
            fused_data = self.data_fuser.fuse_data(data_list)
            if fused_data:
                # 添加用户ID
                for item in fused_data:
                    item["user_id"] = user_id
                return fused_data[0]  # 返回第一个融合结果
            return None
        except Exception as e:
            self.logger.error(f"融合窗口数据失败: {e}")
            return None
    
    def _extract_features(self, fused_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取特征"""
        if not fused_data:
            return None
        
        try:
            # 这里可以添加额外的特征提取逻辑
            # 目前使用DataFuser中已有的特征提取
            return fused_data
        except Exception as e:
            self.logger.error(f"提取特征失败: {e}")
            return None
    
    def _output_results(self, rdd: Any) -> None:
        """输出处理结果"""
        results = rdd.collect()
        
        for result in results:
            if result:
                try:
                    # 输出到存储系统
                    store_result = self.storage_manager.store_data(result)
                    if store_result:
                        self.logger.info(f"处理结果已存储: {json.dumps(result, ensure_ascii=False)[:100]}...")
                    else:
                        self.logger.warning(f"处理结果存储失败: {json.dumps(result, ensure_ascii=False)[:100]}...")
                except Exception as e:
                    self.logger.error(f"输出结果失败: {e}")
    
    def start(self) -> None:
        """启动Spark Streaming"""
        try:
            if not self.ssc:
                self.initialize()
            
            # 创建Kafka流
            kafka_stream = self.create_kafka_stream()
            
            # 处理流
            self.process_stream(kafka_stream)
            
            # 启动流处理
            self.ssc.start()
            self.logger.info("Spark Streaming已启动")
            
        except Exception as e:
            self.logger.error(f"启动Spark Streaming失败: {e}")
            raise
    
    def stop(self) -> None:
        """停止Spark Streaming"""
        try:
            if self.ssc:
                self.ssc.stop(stopSparkContext=True, stopGracefully=True)
                self.logger.info("Spark Streaming已停止")
        except Exception as e:
            self.logger.error(f"停止Spark Streaming失败: {e}")
    
    def await_termination(self) -> None:
        """等待流处理终止"""
        try:
            if self.ssc:
                self.ssc.awaitTermination()
        except Exception as e:
            self.logger.error(f"等待终止失败: {e}")
