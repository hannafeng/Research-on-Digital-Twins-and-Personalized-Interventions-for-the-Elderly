#!/usr/bin/env python3
"""
数字孪生体数据模型测试脚本
"""

import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.digital_twin.digital_twin import DigitalTwin
from src.digital_twin.twin_manager import TwinManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("TestDigitalTwin")

def test_digital_twin_basic():
    """测试数字孪生体基本功能"""
    logger.info("开始测试数字孪生体基本功能")
    
    # 创建数字孪生体实例
    user_id = "test_user_001"
    twin = DigitalTwin(user_id)
    
    # 测试获取完整孪生体数据
    full_twin = twin.get_full_twin()
    logger.info(f"完整数字孪生体数据: {full_twin}")
    
    # 测试更新动态状态
    test_data = {
        "data_type": "wearable",
        "user_id": user_id,
        "heart_rate": 75,
        "blood_pressure": [120, 80],
        "steps": 3000,
        "sleep": "good",
        "activity": "moderate",
        "timestamp": datetime.now().isoformat()
    }
    
    result = twin.update_dynamic_state(test_data)
    logger.info(f"更新动态状态结果: {result}")
    
    # 测试更新个性化基线
    result = twin.update_personalized_baseline()
    logger.info(f"更新个性化基线结果: {result}")
    
    # 测试检测异常
    anomalies = twin.detect_anomalies()
    logger.info(f"检测到的异常: {anomalies}")
    
    # 关闭数字孪生体
    twin.close()
    logger.info("数字孪生体基本功能测试完成")

def test_twin_manager():
    """测试数字孪生体管理器功能"""
    logger.info("开始测试数字孪生体管理器功能")
    
    # 创建数字孪生体管理器
    manager = TwinManager()
    
    # 获取或创建数字孪生体
    user_id1 = "test_user_001"
    user_id2 = "test_user_002"
    
    twin1 = manager.get_twin(user_id1)
    twin2 = manager.get_twin(user_id2)
    
    logger.info(f"创建了数字孪生体实例: {list(manager.twins.keys())}")
    
    # 测试更新所有基线
    manager.update_baselines()
    logger.info("已更新所有数字孪生体的基线")
    
    # 测试检测所有异常
    anomalies = manager.detect_all_anomalies()
    logger.info(f"所有数字孪生体的异常检测结果: {anomalies}")
    
    # 测试获取所有孪生体数据
    all_twins = manager.get_all_twins()
    logger.info(f"获取了 {len(all_twins)} 个数字孪生体的数据")
    
    # 测试移除数字孪生体
    result = manager.remove_twin(user_id1)
    logger.info(f"移除数字孪生体结果: {result}")
    logger.info(f"剩余数字孪生体实例: {list(manager.twins.keys())}")
    
    # 关闭所有数字孪生体
    manager.close_all()
    logger.info("数字孪生体管理器功能测试完成")

if __name__ == "__main__":
    try:
        test_digital_twin_basic()
        print("\n" + "="*50 + "\n")
        test_twin_manager()
        logger.info("所有测试完成")
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()