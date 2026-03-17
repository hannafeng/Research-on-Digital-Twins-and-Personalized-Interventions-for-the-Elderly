from typing import Dict, Any
import logging
from .digital_twin import DigitalTwin

class TwinManager:
    """数字孪生体管理器"""
    
    def __init__(self):
        """初始化数字孪生体管理器"""
        self.logger = logging.getLogger("TwinManager")
        self.twins: Dict[str, DigitalTwin] = {}
        self.logger.info("数字孪生体管理器初始化完成")
    
    def get_twin(self, user_id: str) -> DigitalTwin:
        """获取或创建数字孪生体实例"""
        if user_id not in self.twins:
            # 创建新的数字孪生体实例
            self.twins[user_id] = DigitalTwin(user_id)
            self.logger.info(f"为用户 {user_id} 创建数字孪生体实例")
        return self.twins[user_id]
    
    def update_all_twins(self) -> None:
        """更新所有数字孪生体实例"""
        for user_id, twin in self.twins.items():
            try:
                # 更新动态状态（这里应该接收实时数据）
                # 实际应用中，应该从数据管道获取最新数据
                self.logger.debug(f"更新用户 {user_id} 的数字孪生体")
            except Exception as e:
                self.logger.error(f"更新用户 {user_id} 的数字孪生体失败: {e}")
    
    def update_baselines(self) -> None:
        """更新所有数字孪生体的个性化基线"""
        for user_id, twin in self.twins.items():
            try:
                twin.update_personalized_baseline()
                self.logger.debug(f"更新用户 {user_id} 的个性化基线")
            except Exception as e:
                self.logger.error(f"更新用户 {user_id} 的个性化基线失败: {e}")
    
    def detect_all_anomalies(self) -> Dict[str, Any]:
        """检测所有数字孪生体的异常情况"""
        all_anomalies = {}
        for user_id, twin in self.twins.items():
            try:
                anomalies = twin.detect_anomalies()
                if anomalies:
                    all_anomalies[user_id] = anomalies
                    self.logger.warning(f"用户 {user_id} 检测到异常: {anomalies}")
            except Exception as e:
                self.logger.error(f"检测用户 {user_id} 的异常失败: {e}")
        return all_anomalies
    
    def get_all_twins(self) -> Dict[str, Dict[str, Any]]:
        """获取所有数字孪生体的完整数据"""
        all_twins = {}
        for user_id, twin in self.twins.items():
            try:
                all_twins[user_id] = twin.get_full_twin()
            except Exception as e:
                self.logger.error(f"获取用户 {user_id} 的数字孪生体数据失败: {e}")
        return all_twins
    
    def remove_twin(self, user_id: str) -> bool:
        """移除数字孪生体实例"""
        if user_id in self.twins:
            try:
                self.twins[user_id].close()
                del self.twins[user_id]
                self.logger.info(f"移除用户 {user_id} 的数字孪生体实例")
                return True
            except Exception as e:
                self.logger.error(f"移除用户 {user_id} 的数字孪生体实例失败: {e}")
                return False
        return False
    
    def close_all(self) -> None:
        """关闭所有数字孪生体实例"""
        for user_id, twin in list(self.twins.items()):
            try:
                twin.close()
                del self.twins[user_id]
            except Exception as e:
                self.logger.error(f"关闭用户 {user_id} 的数字孪生体实例失败: {e}")
        self.logger.info("所有数字孪生体实例已关闭")