import numpy as np
import logging
import json
from datetime import datetime

class InterventionGenerator:
    """智能干预生成模型"""
    
    def __init__(self):
        """初始化干预生成模型"""
        self.logger = logging.getLogger("InterventionGenerator")
        self.rule_base = self._build_rule_base()
        self.q_table = self._initialize_q_table()
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.exploration_rate = 0.1
    
    def _build_rule_base(self):
        """构建规则库"""
        return [
            {
                "condition": lambda state: state.get("fall_risk") == "high" and state.get("alone") == True,
                "action": "紧急呼叫护理人员",
                "explanation": "由于跌倒风险高且无人陪同，需要紧急呼叫护理人员"
            },
            {
                "condition": lambda state: state.get("sedentary_time") > 50,
                "action": "提醒老人活动",
                "explanation": "因近1小时静止时长超50分钟，跌倒风险升高，建议提醒老人活动"
            },
            {
                "condition": lambda state: state.get("sleep_quality") == "poor" and state.get("emotion") == "焦虑",
                "action": "播放舒缓音乐",
                "explanation": "由于睡眠质量差且情绪焦虑，建议播放舒缓音乐帮助放松"
            },
            {
                "condition": lambda state: state.get("heart_rate") > 100 and state.get("activity") == "resting",
                "action": "监测心率变化",
                "explanation": "静息心率过高，需要密切监测心率变化"
            },
            {
                "condition": lambda state: state.get("steps") < 1000 and state.get("weather") == "sunny",
                "action": "鼓励户外活动",
                "explanation": "今日天气晴朗，建议鼓励老人进行户外活动"
            }
        ]
    
    def _initialize_q_table(self):
        """初始化Q表"""
        # 状态空间：简化为5个状态维度
        state_space = [
            "fall_risk_high_alone",
            "sedentary_long",
            "poor_sleep_anxious",
            "high_heart_rate",
            "low_activity_sunny"
        ]
        
        # 动作空间
        action_space = [
            "紧急呼叫护理人员",
            "提醒老人活动",
            "播放舒缓音乐",
            "监测心率变化",
            "鼓励户外活动"
        ]
        
        # 初始化Q表
        q_table = {}
        for state in state_space:
            q_table[state] = {}
            for action in action_space:
                q_table[state][action] = 0.0
        
        return q_table
    
    def _extract_state_features(self, twin_state):
        """从孪生体状态中提取特征"""
        features = {
            "fall_risk": "high" if twin_state.get("health_status", {}).get("fall_risk") == "high" else "low",
            "alone": twin_state.get("behavior_status", {}).get("alone", True),
            "sedentary_time": twin_state.get("behavior_status", {}).get("sedentary_time", 0),
            "sleep_quality": twin_state.get("health_status", {}).get("sleep_quality", "good"),
            "emotion": twin_state.get("emotion_status", {}).get("emotion", "平静"),
            "heart_rate": twin_state.get("health_status", {}).get("heart_rate", 75),
            "activity": twin_state.get("behavior_status", {}).get("activity", "resting"),
            "steps": twin_state.get("health_status", {}).get("steps", 0),
            "weather": twin_state.get("behavior_status", {}).get("weather", "sunny")
        }
        return features
    
    def _get_state_key(self, features):
        """获取状态键"""
        if features["fall_risk"] == "high" and features["alone"]:
            return "fall_risk_high_alone"
        elif features["sedentary_time"] > 50:
            return "sedentary_long"
        elif features["sleep_quality"] == "poor" and features["emotion"] == "焦虑":
            return "poor_sleep_anxious"
        elif features["heart_rate"] > 100 and features["activity"] == "resting":
            return "high_heart_rate"
        elif features["steps"] < 1000 and features["weather"] == "sunny":
            return "low_activity_sunny"
        else:
            return "normal"
    
    def _calculate_reward(self, action, state, outcome):
        """计算奖励"""
        # 基础奖励
        base_reward = 0
        
        # 根据动作和结果计算奖励
        if action == "紧急呼叫护理人员" and outcome == "risk_reduced":
            base_reward = 10
        elif action == "提醒老人活动" and outcome == "activity_increased":
            base_reward = 8
        elif action == "播放舒缓音乐" and outcome == "emotion_improved":
            base_reward = 6
        elif action == "监测心率变化" and outcome == "heart_rate_normalized":
            base_reward = 7
        elif action == "鼓励户外活动" and outcome == "steps_increased":
            base_reward = 5
        
        # 惩罚项
        if outcome == "no_change":
            base_reward = -2
        elif outcome == "worsened":
            base_reward = -5
        
        return base_reward
    
    def generate_intervention(self, twin_state):
        """生成干预建议"""
        try:
            # 提取状态特征
            features = self._extract_state_features(twin_state)
            state_key = self._get_state_key(features)
            
            # 首先尝试规则引擎
            for rule in self.rule_base:
                if rule["condition"](features):
                    self.logger.info(f"规则引擎触发: {rule['action']}")
                    return {
                        "action": rule["action"],
                        "explanation": rule["explanation"],
                        "confidence": "high",
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 如果规则引擎未触发，使用强化学习
            if state_key in self.q_table:
                # 探索或利用
                if np.random.random() < self.exploration_rate:
                    # 探索：随机选择动作
                    actions = list(self.q_table[state_key].keys())
                    action = np.random.choice(actions)
                else:
                    # 利用：选择Q值最高的动作
                    action = max(self.q_table[state_key], key=self.q_table[state_key].get)
                
                # 生成解释
                explanation = self._generate_explanation(action, features)
                
                self.logger.info(f"强化学习触发: {action}")
                return {
                    "action": action,
                    "explanation": explanation,
                    "confidence": "medium",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # 默认干预
                self.logger.info("默认干预: 监测状态")
                return {
                    "action": "监测状态",
                    "explanation": "当前状态正常，继续监测",
                    "confidence": "low",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            self.logger.error(f"生成干预建议失败: {e}")
            return {
                "action": "监测状态",
                "explanation": "生成干预建议时发生错误，继续监测",
                "confidence": "low",
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_explanation(self, action, features):
        """生成干预解释"""
        explanations = {
            "紧急呼叫护理人员": "由于跌倒风险高且无人陪同，需要紧急呼叫护理人员",
            "提醒老人活动": f"因近1小时静止时长{features['sedentary_time']}分钟，跌倒风险升高，建议提醒老人活动",
            "播放舒缓音乐": "由于睡眠质量差且情绪焦虑，建议播放舒缓音乐帮助放松",
            "监测心率变化": f"静息心率{features['heart_rate']}过高，需要密切监测心率变化",
            "鼓励户外活动": "今日天气晴朗，建议鼓励老人进行户外活动"
        }
        return explanations.get(action, "根据当前状态生成的干预建议")
    
    def update_q_table(self, state, action, reward, next_state):
        """更新Q表"""
        try:
            state_key = self._get_state_key(state)
            next_state_key = self._get_state_key(next_state)
            
            if state_key in self.q_table and next_state_key in self.q_table:
                # Q-learning更新公式
                current_q = self.q_table[state_key][action]
                max_next_q = max(self.q_table[next_state_key].values())
                new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
                self.q_table[state_key][action] = new_q
                
                self.logger.info(f"Q表更新: {state_key} -> {action} = {new_q}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"更新Q表失败: {e}")
            return False
    
    def save_q_table(self, file_path):
        """保存Q表"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.q_table, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Q表已保存到: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存Q表失败: {e}")
            return False
    
    def load_q_table(self, file_path):
        """加载Q表"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.q_table = json.load(f)
            self.logger.info(f"Q表已从: {file_path} 加载")
            return True
        except Exception as e:
            self.logger.error(f"加载Q表失败: {e}")
            return False