import time
import json
import random
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("TestDataPipeline")

def generate_wearable_data(user_id="test_user"):
    """生成模拟可穿戴设备数据"""
    return {
        "data_type": "wearable",
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "heart_rate": random.randint(60, 100),
        "steps": random.randint(0, 100),
        "blood_pressure": random.randint(110, 140),
        "temperature": round(random.uniform(36.0, 37.5), 1),
        "acceleration": round(random.uniform(-10, 10), 2),
        "device_id": f"wearable_{random.randint(1, 100)}",
        "protocol": "mqtt"
    }

def generate_environment_data():
    """生成模拟环境传感器数据"""
    return {
        "data_type": "environment",
        "timestamp": datetime.now().isoformat(),
        "temperature": round(random.uniform(20.0, 30.0), 1),
        "humidity": round(random.uniform(30, 70), 1),
        "light_intensity": random.randint(0, 1000),
        "co2_level": random.randint(300, 1000),
        "smoke_level": random.randint(0, 100),
        "device_id": f"env_{random.randint(1, 100)}",
        "protocol": "mqtt"
    }

def generate_audio_data(user_id="test_user"):
    """生成模拟音频数据"""
    # 模拟base64编码的音频数据
    audio_data = "VGhpcyBpcyBhIHNvbWUgYWZ0ZXIgZGF0YS4="  # "This is some after data."
    
    return {
        "data_type": "audio",
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "audio_data": audio_data,
        "encoding": "base64",
        "audio_format": "raw",
        "sampling_rate": 16000,
        "channels": 1,
        "sample_width": 2,
        "device_id": f"audio_{random.randint(1, 100)}",
        "protocol": "websocket"
    }

def test_data_pipeline():
    """测试数据管道"""
    logger.info("开始测试数据管道")
    
    try:
        # 导入数据管道模块
        from src.processing.cleaning.data_cleaner import DataCleaner
        from src.processing.fusion.data_fuser import DataFuser
        from src.storage.storage_manager import StorageManager
        
        # 初始化模块
        data_cleaner = DataCleaner()
        data_fuser = DataFuser()
        storage_manager = StorageManager()
        
        # 生成测试数据
        test_data = []
        for i in range(10):
            # 生成可穿戴设备数据
            wearable_data = generate_wearable_data()
            test_data.append(wearable_data)
            
            # 生成环境传感器数据
            env_data = generate_environment_data()
            test_data.append(env_data)
            
            # 生成音频数据
            audio_data = generate_audio_data()
            test_data.append(audio_data)
            
            time.sleep(0.5)  # 模拟数据采集间隔
        
        logger.info(f"生成了 {len(test_data)} 条测试数据")
        
        # 测试数据清洗
        logger.info("测试数据清洗模块")
        cleaned_data = []
        start_time = time.time()
        for data in test_data:
            cleaned = data_cleaner.clean_data(data)
            cleaned_data.append(cleaned)
        end_time = time.time()
        logger.info(f"数据清洗完成，共清洗 {len(cleaned_data)} 条数据，耗时 {end_time - start_time:.2f} 秒")
        
        # 测试数据融合
        logger.info("测试数据融合模块")
        start_time = time.time()
        fused_data = data_fuser.fuse_data(cleaned_data)
        end_time = time.time()
        logger.info(f"数据融合完成，共融合 {len(fused_data)} 条数据，耗时 {end_time - start_time:.2f} 秒")
        
        # 测试数据存储
        logger.info("测试数据存储模块")
        start_time = time.time()
        storage_result = storage_manager.store_batch_data(fused_data)
        end_time = time.time()
        logger.info(f"数据存储完成，结果: {storage_result}，耗时 {end_time - start_time:.2f} 秒")
        
        # 测试数据读取
        logger.info("测试数据读取模块")
        real_time_data = storage_manager.get_real_time_data(count=10)
        logger.info(f"从Redis读取了 {len(real_time_data)} 条实时数据")
        
        # 打印测试结果
        logger.info("\n=== 测试结果 ===")
        logger.info(f"生成测试数据: {len(test_data)} 条")
        logger.info(f"清洗后数据: {len(cleaned_data)} 条")
        logger.info(f"融合后数据: {len(fused_data)} 条")
        logger.info(f"存储结果: {'成功' if storage_result else '失败'}")
        logger.info(f"实时数据读取: {len(real_time_data)} 条")
        logger.info("=== 测试完成 ===")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    test_data_pipeline()
