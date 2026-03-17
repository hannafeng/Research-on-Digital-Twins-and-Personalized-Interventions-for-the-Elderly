#!/usr/bin/env python3
"""
AI社区养老数字孪生平台 - 数据管道运行脚本

使用说明：
1. 从项目根目录运行：python run_pipeline.py
2. 或从data_pipeline目录运行：python main.py

此脚本提供了一种简单的方式来运行数据管道，无需复杂的命令或路径设置。
"""

import sys
import os

# 获取项目根目录和data_pipeline目录
root_dir = os.path.dirname(os.path.abspath(__file__))
data_pipeline_dir = os.path.join(root_dir, 'data_pipeline')

# 添加data_pipeline目录到Python路径，以便找到src模块
sys.path.insert(0, data_pipeline_dir)
sys.path.insert(0, root_dir)

try:
    # 导入并运行主应用
    from main import main
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"导入错误: {e}")
    print("\n请确保您的Python环境已安装所有依赖：")
    print("python -m pip install -r data_pipeline/requirements.txt")
    sys.exit(1)

except Exception as e:
    print(f"运行错误: {e}")
    sys.exit(1)
