import time
import threading
import schedule
import logging
from typing import List, Dict, Any, Callable
from datetime import datetime, timedelta
from ..collection.wearable.wearable_collector import WearableCollector
from ..collection.environment.environment_collector import EnvironmentCollector
from ..collection.audio.audio_collector import AudioCollector
from ..processing.cleaning.data_cleaner import DataCleaner
from ..processing.fusion.data_fuser import DataFuser
from ..storage.storage_manager import StorageManager
from ..config.config_manager import config_manager

class DataPipelineScheduler:
    """数据管道调度器"""
    
    def __init__(self):
        """初始化数据管道调度器"""
        self.logger = logging.getLogger("DataPipelineScheduler")
        
        # 初始化配置
        self.config = config_manager.get_section("scheduling")
        self.schedule_interval = self.config["schedule_interval"]  # 秒
        
        # 初始化数据队列
        self.raw_data_queue: List[Dict[str, Any]] = []
        self.cleaned_data_queue: List[Dict[str, Any]] = []
        
        # 初始化各个模块
        self.data_cleaner = DataCleaner()
        self.data_fuser = DataFuser()
        self.storage_manager = StorageManager()
        
        # 初始化采集器
        self.wearable_collector = WearableCollector(self._raw_data_callback)
        self.environment_collector = EnvironmentCollector(self._raw_data_callback)
        self.audio_collector = AudioCollector(self._raw_data_callback)
        
        # 调度线程
        self.schedule_thread = None
        self.running = False
        
        # 数字孪生体更新时间
        self.last_twin_update = datetime.now()
        
        self.logger.info("数据管道调度器初始化完成")
    
    def _raw_data_callback(self, data: Dict[str, Any]) -> None:
        """原始数据回调函数"""
        self.raw_data_queue.append(data)
        self.logger.debug(f"收到原始数据: {data.get('data_type')} - {data.get('timestamp')}")
    
    def _clean_data_task(self) -> None:
        """清洗数据任务"""
        if not self.raw_data_queue:
            return
        
        self.logger.info(f"开始清洗数据，队列大小: {len(self.raw_data_queue)}")
        
        # 批量清洗数据
        cleaned_data = []
        while self.raw_data_queue:
            data = self.raw_data_queue.pop(0)
            cleaned = self.data_cleaner.clean_data(data)
            cleaned_data.append(cleaned)
        
        # 将清洗后的数据加入队列
        self.cleaned_data_queue.extend(cleaned_data)
        self.logger.info(f"数据清洗完成，清洗后数据数量: {len(cleaned_data)}")
    
    def _fuse_and_store_data_task(self) -> None:
        """融合和存储数据任务"""
        if not self.cleaned_data_queue:
            return
        
        self.logger.info(f"开始融合数据，队列大小: {len(self.cleaned_data_queue)}")
        
        # 批量融合数据
        fused_data = self.data_fuser.fuse_data(self.cleaned_data_queue)
        self.logger.info(f"数据融合完成，融合后数据数量: {len(fused_data)}")
        
        # 批量存储数据
        store_result = self.storage_manager.store_batch_data(fused_data)
        if store_result:
            self.logger.info("数据存储完成")
            # 清空清洗后的数据队列
            self.cleaned_data_queue.clear()
        else:
            self.logger.error("数据存储失败")
    
    def _update_digital_twin_task(self) -> None:
        """更新数字孪生体任务"""
        self.logger.info("开始更新数字孪生体")
        
        try:
            # 获取最近5分钟的实时数据
            recent_data = self.storage_manager.get_real_time_data(count=1000)
            
            # 计算数字孪生体更新所需的特征
            twin_update_data = self._calculate_twin_features(recent_data)
            
            # 存储数字孪生体更新数据
            twin_update = {
                "data_type": "digital_twin",
                "timestamp": datetime.now().isoformat(),
                "update_data": twin_update_data,
                "protocol": "internal"
            }
            
            # 存储数字孪生体更新记录
            self.storage_manager.store_data(twin_update)
            
            self.last_twin_update = datetime.now()
            self.logger.info("数字孪生体更新完成")
            
        except Exception as e:
            self.logger.error(f"数字孪生体更新失败: {e}")
    
    def _calculate_twin_features(self, recent_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算数字孪生体更新所需的特征"""
        # 简单示例：计算各种数据的统计特征
        twin_features = {
            "wearable_stats": {},
            "environment_stats": {},
            "audio_stats": {},
            "update_time": datetime.now().isoformat()
        }
        
        # 按数据类型分组
        wearable_data = [d for d in recent_data if d.get("data_type") == "wearable"]
        environment_data = [d for d in recent_data if d.get("data_type") == "environment"]
        audio_data = [d for d in recent_data if d.get("data_type") == "audio"]
        
        # 计算可穿戴设备数据统计
        if wearable_data:
            heart_rates = [d.get("heart_rate", 0) for d in wearable_data if d.get("heart_rate") is not None]
            if heart_rates:
                twin_features["wearable_stats"]["avg_heart_rate"] = sum(heart_rates) / len(heart_rates)
                twin_features["wearable_stats"]["min_heart_rate"] = min(heart_rates)
                twin_features["wearable_stats"]["max_heart_rate"] = max(heart_rates)
            
            steps = [d.get("steps", 0) for d in wearable_data if d.get("steps") is not None]
            if steps:
                twin_features["wearable_stats"]["total_steps"] = sum(steps)
        
        # 计算环境数据统计
        if environment_data:
            temperatures = [d.get("temperature", 0) for d in environment_data if d.get("temperature") is not None]
            if temperatures:
                twin_features["environment_stats"]["avg_temperature"] = sum(temperatures) / len(temperatures)
            
            humidities = [d.get("humidity", 0) for d in environment_data if d.get("humidity") is not None]
            if humidities:
                twin_features["environment_stats"]["avg_humidity"] = sum(humidities) / len(humidities)
        
        # 计算音频数据统计
        if audio_data:
            twin_features["audio_stats"]["audio_sample_count"] = len(audio_data)
        
        return twin_features
    
    def _schedule_jobs(self) -> None:
        """调度任务"""
        # 每秒执行一次数据清洗
        schedule.every(1).seconds.do(self._clean_data_task)
        
        # 每30秒执行一次数据融合和存储
        schedule.every(30).seconds.do(self._fuse_and_store_data_task)
        
        # 每5分钟执行一次数字孪生体更新
        schedule.every(5).minutes.do(self._update_digital_twin_task)
        
        self.logger.info("任务调度已设置")
        self.logger.info(f"数据清洗间隔: 1秒")
        self.logger.info(f"数据融合和存储间隔: 30秒")
        self.logger.info(f"数字孪生体更新间隔: {self.schedule_interval}秒 ({self.schedule_interval/60}分钟)")
    
    def _run_scheduler(self) -> None:
        """运行调度器"""
        self.logger.info("启动调度器")
        while self.running:
            schedule.run_pending()
            time.sleep(0.1)
        self.logger.info("调度器已停止")
    
    def start(self) -> None:
        """启动数据管道"""
        self.logger.info("启动数据管道")
        
        # 设置运行标志
        self.running = True
        
        # 启动采集器
        self.wearable_collector.start()
        self.environment_collector.start()
        self.audio_collector.start()
        
        # 设置调度任务
        self._schedule_jobs()
        
        # 启动调度线程
        self.schedule_thread = threading.Thread(target=self._run_scheduler)
        self.schedule_thread.daemon = True
        self.schedule_thread.start()
        
        self.logger.info("数据管道启动完成")
    
    def stop(self) -> None:
        """停止数据管道"""
        self.logger.info("停止数据管道")
        
        # 设置运行标志
        self.running = False
        
        # 停止采集器
        self.wearable_collector.stop()
        self.environment_collector.stop()
        self.audio_collector.stop()
        
        # 等待调度线程结束
        if self.schedule_thread:
            self.schedule_thread.join(timeout=5.0)
        
        # 关闭存储连接
        self.storage_manager.close()
        
        self.logger.info("数据管道已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """获取数据管道状态"""
        return {
            "running": self.running,
            "raw_data_queue_size": len(self.raw_data_queue),
            "cleaned_data_queue_size": len(self.cleaned_data_queue),
            "last_twin_update": self.last_twin_update.isoformat(),
            "next_twin_update": (self.last_twin_update + timedelta(seconds=self.schedule_interval)).isoformat(),
            "collector_counts": {
                "wearable": self.wearable_collector.get_collector_count(),
                "environment": self.environment_collector.get_collector_count(),
                "audio": self.audio_collector.get_collector_count()
            }
        }
