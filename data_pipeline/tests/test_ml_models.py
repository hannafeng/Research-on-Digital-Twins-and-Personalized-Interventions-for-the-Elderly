#!/usr/bin/env python3
"""
机器学习模型测试脚本
"""

import sys
import os
import logging
import numpy as np
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ml.models.activity_recognition import ActivityRecognitionModel
from src.ml.models.emotion_recognition import EmotionRecognitionModel
from src.ml.models.intervention_generator import InterventionGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("TestMLModels")

def test_activity_recognition_model():
    """测试行为识别模型"""
    logger.info("开始测试行为识别模型")
    
    # 创建模型实例
    model = ActivityRecognitionModel()
    
    # 构建模型
    model.build_model()
    
    # 生成测试数据（128个时间步，6个特征）
    test_data = np.random.rand(128, 6)
    
    # 预测
    result = model.predict([test_data])
    logger.info(f"行为识别预测结果: {result}")
    
    # 验证结果
    assert result is not None, "行为识别预测失败"
    assert len(result) == 1, "行为识别预测结果长度错误"
    assert "label" in result[0], "行为识别预测结果缺少label字段"
    assert "confidence" in result[0], "行为识别预测结果缺少confidence字段"
    
    logger.info("行为识别模型测试通过")

def test_emotion_recognition_model():
    """测试情感计算模型"""
    logger.info("开始测试情感计算模型")
    
    # 创建模型实例
    model = EmotionRecognitionModel()
    
    # 构建模型
    model.build_model()
    
    # 生成测试数据（MFCC特征）
    test_data = np.random.rand(40, 100)
    
    # 预测
    result = model.predict([test_data])
    logger.info(f"情感计算预测结果: {result}")
    
    # 验证结果
    assert result is not None, "情感计算预测失败"
    assert len(result) == 1, "情感计算预测结果长度错误"
    assert "label" in result[0], "情感计算预测结果缺少label字段"
    assert "confidence" in result[0], "情感计算预测结果缺少confidence字段"
    
    logger.info("情感计算模型测试通过")

def test_intervention_generator():
    """测试智能干预生成模型"""
    logger.info("开始测试智能干预生成模型")
    
    # 创建模型实例
    model = InterventionGenerator()
    
    # 生成测试数据（孪生体状态）
    test_state = {
        "health_status": {
            "heart_rate": 75,
            "steps": 500,
            "sleep_quality": "good",
            "fall_risk": "low"
        },
        "behavior_status": {
            "activity": "静坐",
            "sedentary_time": 60,
            "alone": True,
            "weather": "sunny"
        },
        "emotion_status": {
            "emotion": "平静"
        }
    }
    
    # 生成干预建议
    result = model.generate_intervention(test_state)
    logger.info(f"干预生成结果: {result}")
    
    # 验证结果
    assert result is not None, "干预生成失败"
    assert "action" in result, "干预生成结果缺少action字段"
    assert "explanation" in result, "干预生成结果缺少explanation字段"
    assert "confidence" in result, "干预生成结果缺少confidence字段"
    assert "timestamp" in result, "干预生成结果缺少timestamp字段"
    
    logger.info("智能干预生成模型测试通过")

def test_model_integration():
    """测试模型集成"""
    logger.info("开始测试模型集成")
    
    # 模拟孪生体状态
    twin_state = {
        "health_status": {
            "heart_rate": 85,
            "steps": 2000,
            "sleep_quality": "poor",
            "fall_risk": "high"
        },
        "behavior_status": {
            "activity": "静坐",
            "sedentary_time": 55,
            "alone": True,
            "weather": "sunny"
        },
        "emotion_status": {
            "emotion": "焦虑"
        }
    }
    
    # 测试干预生成
    generator = InterventionGenerator()
    intervention = generator.generate_intervention(twin_state)
    logger.info(f"集成测试干预结果: {intervention}")
    
    # 验证干预结果
    assert intervention is not None, "集成测试干预生成失败"
    assert "action" in intervention, "集成测试干预结果缺少action字段"
    assert "explanation" in intervention, "集成测试干预结果缺少explanation字段"
    
    logger.info("模型集成测试通过")

if __name__ == "__main__":
    try:
        test_activity_recognition_model()
        print("\n" + "="*50 + "\n")
        test_emotion_recognition_model()
        print("\n" + "="*50 + "\n")
        test_intervention_generator()
        print("\n" + "="*50 + "\n")
        test_model_integration()
        logger.info("所有机器学习模型测试通过")
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()