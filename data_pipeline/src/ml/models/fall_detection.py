import os
import re
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np
import xgboost as xgb
import joblib
import httpx

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("FallDetection")

# ==================== 数据模型 ====================
class ActionPrediction:
    def __init__(self, user_id: str, activity_label: str, timestamp: datetime = None):
        self.user_id = user_id
        self.activity_label = activity_label
        self.timestamp = timestamp or datetime.now()

class UserReply:
    def __init__(self, user_id: str, reply_text: str, timestamp: datetime = None):
        self.user_id = user_id
        self.reply_text = reply_text
        self.timestamp = timestamp or datetime.now()

class SensorData:
    def __init__(self, user_id: str, features: list[float], timestamp: datetime = None):
        self.user_id = user_id
        self.features = features
        self.timestamp = timestamp or datetime.now()

# ==================== 服务层：状态管理 ====================
class UserState:
    def __init__(self):
        self.current_state = "normal"
        self.last_activity: Optional[str] = None
        self.activity_count: int = 0
        self.last_effective_activity: Optional[str] = None
        self.suspect_start_time: Optional[datetime] = None
        self.last_question: Optional[str] = None
        self.last_emergency_msg: Optional[str] = None

class StateManager:
    def __init__(self):
        self._states: Dict[str, UserState] = {}
        self._lock = asyncio.Lock()
        self.states_map = {
            "normal": "normal",
            "suspect_fall": "suspect_fall",
            "confirmed_fall": "confirmed_fall"
        }

    async def get_or_create(self, user_id: str) -> UserState:
        async with self._lock:
            if user_id not in self._states:
                self._states[user_id] = UserState()
                logger.info(f"初始化用户状态：{user_id}")
            return self._states[user_id]

    async def get_status(self, user_id: str) -> Optional[dict]:
        async with self._lock:
            if user_id in self._states:
                state = self._states[user_id]
                return {
                    "current_state": state.current_state,
                    "last_activity": state.last_activity,
                    "suspect_start_time": state.suspect_start_time.isoformat() if state.suspect_start_time else None,
                    "last_question": state.last_question,
                    "last_emergency_msg": state.last_emergency_msg
                }
            return None
    
    async def update_state(self, user_id: str, new_state: str, reset_suspect_time: bool = False):
        async with self._lock:
            if user_id in self._states:
                state = self._states[user_id]
                state.current_state = new_state
                if reset_suspect_time:
                    state.suspect_start_time = None
                logger.info(f"用户 {user_id} 状态更新为：{new_state}")

# ==================== 服务层：LLM 调用 ====================
class LLMService:
    def __init__(self, api_key: str, api_url: str, model: str):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.client.aclose()

    async def generate(self, prompt: str, system_message: str = "你是一个智能助手。") -> Optional[str]:
        if not self.api_key or self.api_key == "your-api-key-here":
            logger.warning("LLM API Key 未配置，跳过调用")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "input": {
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {"temperature": 0.7, "max_tokens": 150, "top_p": 0.8}
        }

        try:
            response = await self.client.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            text = ""
            if "output" in result and "text" in result["output"]:
                text = result["output"]["text"]
            elif "choices" in result and len(result["choices"]) > 0:
                text = result["choices"][0].get("message", {}).get("content", "")
            
            return text.strip() if text else None
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM HTTP 错误：{e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"LLM 调用异常：{e}")
            return None

# ==================== 服务层：模型管理 ====================
class ModelManager:
    def __init__(self, model_path: Path, encoder_path: Path, features_path: Path):
        self.model_path = model_path
        self.encoder_path = encoder_path
        self.features_path = features_path
        self.model: Optional[xgb.XGBClassifier] = None
        self.label_encoder: Optional[Any] = None
        self.feature_names: Optional[list] = None
        self.is_loaded = False

    def load(self):
        if not self.model_path.exists() or not self.encoder_path.exists():
            logger.warning("模型文件不存在，传感器预测功能将不可用")
            return

        try:
            self.model = xgb.XGBClassifier()
            self.model.load_model(str(self.model_path))
            self.label_encoder = joblib.load(str(self.encoder_path))
            if self.features_path.exists():
                self.feature_names = joblib.load(str(self.features_path))
            self.is_loaded = True
            logger.info(f"✅ 模型加载成功：{self.model_path}")
        except Exception as e:
            logger.error(f"❌ 模型加载失败：{e}", exc_info=True)

    def predict(self, features: list[float]) -> str:
        if not self.is_loaded or self.model is None or self.label_encoder is None:
            raise RuntimeError("模型未就绪")
        
        try:
            features_array = np.array(features).reshape(1, -1)
            logger.debug(f"输入特征维度：{features_array.shape}")
            
            pred_encoded = self.model.predict(features_array)[0]
            logger.debug(f"预测编码值：{pred_encoded}, 类型：{type(pred_encoded)}")
            
            # 处理 label_encoder 的兼容性问题
            if hasattr(self.label_encoder, 'inverse_transform'):
                activity = self.label_encoder.inverse_transform([pred_encoded])[0]
            elif hasattr(self.label_encoder, 'classes_'):
                if 0 <= int(pred_encoded) < len(self.label_encoder.classes_):
                    activity = self.label_encoder.classes_[int(pred_encoded)]
                else:
                    activity = f"UNKNOWN_{int(pred_encoded)}"
            else:
                activity = str(pred_encoded)
            
            # 确保返回 Python 原生字符串类型
            activity = str(activity)
            
            logger.debug(f"预测活动：{activity}, 类型：{type(activity)}")
            return activity
            
        except Exception as e:
            logger.error(f"模型预测异常：{e}", exc_info=True)
            raise RuntimeError(f"模型预测失败：{e}") 

# ==================== 业务逻辑 ====================
PROMPT_SUSPECT_FALL = "检测到用户可能摔倒，请用一句简短的话询问用户是否安全，语气要温和。"
PROMPT_CONFIRMED_FALL = "用户已确认摔倒且长时间未起身，请生成一句紧急求助信息，包含时间和地点（假设地点为家中），用于通知紧急联系人。信息要简洁。"

async def process_activity_logic(user_id: str, activity: str, current_time: datetime, state_manager: StateManager, llm_service: LLMService, action_threshold: int = 3, suspect_timeout: int = 300):
    state = await state_manager.get_or_create(user_id)
    
    if activity == state.last_activity:
        state.activity_count += 1
    else:
        state.activity_count = 1
        state.last_activity = activity

    if state.activity_count >= action_threshold:
        effective_activity = activity
        fall_related = ["LAYING", "SITTING"]
        normal_activities = ["WALKING", "WALKING_UPSTAIRS", "WALKING_DOWNSTAIRS", "STANDING"]

        if state.current_state == "normal":
            if effective_activity in fall_related and state.last_effective_activity in normal_activities:
                state.current_state = "suspect_fall"
                state.suspect_start_time = current_time
                logger.info(f"[{current_time}] 用户 {user_id} 进入【疑似摔倒】状态")
                
                ask_phrase = await llm_service.generate(PROMPT_SUSPECT_FALL)
                state.last_question = ask_phrase if ask_phrase else "您还好吗？"

        elif state.current_state == "suspect_fall":
            if state.suspect_start_time:
                time_elapsed = (current_time - state.suspect_start_time).total_seconds()
                if effective_activity in fall_related and time_elapsed > suspect_timeout:
                    state.current_state = "confirmed_fall"
                    logger.info(f"[{current_time}] 用户 {user_id} 进入【确认摔倒】状态（持续 {time_elapsed:.0f} 秒）")
                    
                    emergency_msg = await llm_service.generate(PROMPT_CONFIRMED_FALL)
                    state.last_emergency_msg = emergency_msg if emergency_msg else "用户可能摔倒，请立即救援！"
                
                elif effective_activity not in fall_related:
                    state.current_state = "normal"
                    state.suspect_start_time = None
                    logger.info(f"[{current_time}] 用户 {user_id} 恢复【正常】状态")

        elif state.current_state == "confirmed_fall":
            if effective_activity not in fall_related:
                state.current_state = "normal"
                state.suspect_start_time = None
                logger.info(f"[{current_time}] 用户 {user_id} 从确认摔倒恢复【正常】状态")

        state.last_effective_activity = effective_activity

    logger.debug(f"用户 {user_id} | 动作：{activity} | 计数：{state.activity_count} | 状态：{state.current_state}")
    return state.current_state

async def handle_user_reply(user_id: str, reply_text: str, timestamp: datetime, state_manager: StateManager, llm_service: LLMService):
    state_obj = await state_manager.get_or_create(user_id)
    
    if state_obj.current_state not in ["suspect_fall", "confirmed_fall"]:
        return {"status": "ignored", "message": "当前状态不需要处理回复"}

    prompt = f"""
    用户回复了："{reply_text}"
    请判断用户当前的状态是需要救援还是安全了。
    如果你认为用户需要紧急救援，请回复数字 2；
    如果你认为用户已经安全或只是短暂不适，请回复数字 1。
    只回复数字，不要有其他文字。
    """
    
    intent_raw = await llm_service.generate(prompt, system_message="你是一个摔倒检测系统的意图识别模块。")
    intent_code = None
    
    if intent_raw:
        match = re.search(r'[12]', intent_raw)
        if match:
            intent_code = match.group()
    
    if intent_code == "2":
        if state_obj.current_state != "confirmed_fall":
            await state_manager.update_state(user_id, "confirmed_fall", reset_suspect_time=True)
            logger.info(f"[{timestamp}] 用户 {user_id} 根据回复确认为【确认摔倒】")
    elif intent_code == "1":
        await state_manager.update_state(user_id, "normal", reset_suspect_time=True)
        logger.info(f"[{timestamp}] 用户 {user_id} 根据回复恢复【正常】状态")
    else:
        logger.info(f"意图识别失败或未确定，保持原状态：{state_obj.current_state}")

    # 重新获取最新状态
    updated_state = await state_manager.get_or_create(user_id)

    return {
        "status": "processed",
        "intent": intent_code,
        "current_state": str(updated_state.current_state)
    }
