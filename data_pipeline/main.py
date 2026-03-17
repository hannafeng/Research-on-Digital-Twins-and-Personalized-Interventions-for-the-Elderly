#!/usr/bin/env python3
"""
AI社区养老数字孪生平台 - 数据管道主入口

使用说明：
1. 从项目根目录运行：python run_pipeline.py
2. 从data_pipeline目录运行：python main.py

注意：请勿直接运行子模块文件，如audio_collector.py，这会导致相对导入错误。
"""

import os
import sys
import logging
import time

# 确保脚本在正确的目录下运行
current_dir = os.path.dirname(os.path.abspath(__file__))

# 导入调度器、配置管理器和Spark处理器
from src.scheduling.scheduler import DataPipelineScheduler
from src.config.config_manager import config_manager
from src.processing.streaming.spark_processor import SparkProcessor
# 导入数字孪生体模块
from src.digital_twin.twin_manager import TwinManager

# 配置日志
logging.basicConfig(
    level=getattr(logging, config_manager.get_value("logging.level", "INFO")),
    format=config_manager.get_value("logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
    handlers=[
        logging.FileHandler(config_manager.get_value("logging.file", "logs/data_pipeline.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("DataPipelineMain")

def main():
    """主函数"""
    logger.info("启动AI社区养老数字孪生平台数据管道")
    
    # 初始化Spark处理器
    spark_processor = None
    # 初始化数字孪生体管理器
    twin_manager = TwinManager()
    
    try:
        # 初始化数据管道调度器
        scheduler = DataPipelineScheduler()
        
        # 初始化并启动Spark Streaming
        try:
            spark_processor = SparkProcessor()
            spark_processor.start()
            logger.info("Spark Streaming已启动")
        except Exception as e:
            logger.warning(f"Spark Streaming启动失败，将继续运行其他模块: {e}")
        
        # 启动数据管道
        scheduler.start()
        
        # 保持程序运行
        logger.info("数据管道已启动，按Ctrl+C停止")
        
        # 用于跟踪基线更新和异常检测的时间
        last_baseline_update = time.time()
        last_anomaly_detection = time.time()
        
        while True:
            # 每10秒打印一次状态
            time.sleep(10)
            status = scheduler.get_status()
            logger.info(f"数据管道状态: {status}")
            
            # 每小时更新一次个性化基线
            if time.time() - last_baseline_update >= 3600:
                logger.info("开始更新数字孪生体个性化基线")
                twin_manager.update_baselines()
                last_baseline_update = time.time()
            
            # 每5分钟检测一次异常
            if time.time() - last_anomaly_detection >= 300:
                logger.info("开始检测数字孪生体异常")
                anomalies = twin_manager.detect_all_anomalies()
                if anomalies:
                    logger.warning(f"检测到异常: {anomalies}")
                last_anomaly_detection = time.time()
            
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在停止数据管道...")
        # 停止Spark Streaming
        if spark_processor:
            spark_processor.stop()
        # 停止调度器
        scheduler.stop()
        # 关闭数字孪生体管理器
        twin_manager.close_all()
        logger.info("数据管道已停止")
    except Exception as e:
        logger.error(f"数据管道运行错误: {e}")
        # 停止Spark Streaming
        if spark_processor:
            spark_processor.stop()
        # 停止调度器
        scheduler.stop()
        # 关闭数字孪生体管理器
        twin_manager.close_all()

if __name__ == "__main__":
    main()
