import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, LSTM, Dense, Dropout, Flatten
from tensorflow.keras.utils import to_categorical
import numpy as np
import logging

class ActivityRecognitionModel:
    """行为识别模型（CNN-LSTM混合架构）"""
    
    def __init__(self):
        """初始化行为识别模型"""
        self.logger = logging.getLogger("ActivityRecognitionModel")
        self.model = None
        self.class_labels = ["静坐", "行走", "跌倒", "站立", "躺下"]
        self.input_shape = (128, 6)  # 128个时间步，6个特征（加速度x/y/z，陀螺仪x/y/z）
    
    def build_model(self):
        """构建CNN-LSTM模型"""
        try:
            self.model = Sequential([
                # CNN层用于特征提取
                Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=self.input_shape),
                MaxPooling1D(pool_size=2),
                Dropout(0.2),
                
                Conv1D(filters=128, kernel_size=3, activation='relu'),
                MaxPooling1D(pool_size=2),
                Dropout(0.2),
                
                # LSTM层用于序列建模
                LSTM(128, return_sequences=True),
                LSTM(64),
                Dropout(0.3),
                
                # 分类层
                Dense(64, activation='relu'),
                Dense(len(self.class_labels), activation='softmax')
            ])
            
            self.model.compile(
                optimizer='adam',
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            
            self.logger.info("行为识别模型构建成功")
            return self.model
        except Exception as e:
            self.logger.error(f"构建行为识别模型失败: {e}")
            return None
    
    def preprocess_data(self, data):
        """预处理数据"""
        try:
            # 数据标准化
            mean = np.mean(data, axis=0)
            std = np.std(data, axis=0)
            data = (data - mean) / std
            
            # 重塑数据形状
            data = np.reshape(data, (-1, self.input_shape[0], self.input_shape[1]))
            
            return data
        except Exception as e:
            self.logger.error(f"数据预处理失败: {e}")
            return None
    
    def train(self, X_train, y_train, X_val, y_val, epochs=50, batch_size=32):
        """训练模型"""
        try:
            # 转换标签为one-hot编码
            y_train = to_categorical(y_train, num_classes=len(self.class_labels))
            y_val = to_categorical(y_val, num_classes=len(self.class_labels))
            
            # 训练模型
            history = self.model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=epochs,
                batch_size=batch_size,
                callbacks=[
                    tf.keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
                    tf.keras.callbacks.ModelCheckpoint('models/activity_model.h5', save_best_only=True)
                ]
            )
            
            self.logger.info("行为识别模型训练成功")
            return history
        except Exception as e:
            self.logger.error(f"训练行为识别模型失败: {e}")
            return None
    
    def predict(self, data):
        """预测行为"""
        try:
            # 预处理数据
            processed_data = self.preprocess_data(data)
            if processed_data is None:
                return None
            
            # 预测
            predictions = self.model.predict(processed_data)
            
            # 获取预测结果和置信度
            results = []
            for pred in predictions:
                class_idx = np.argmax(pred)
                confidence = float(pred[class_idx]) * 100
                results.append({
                    "label": self.class_labels[class_idx],
                    "confidence": f"{confidence:.1f}%"
                })
            
            return results
        except Exception as e:
            self.logger.error(f"行为识别预测失败: {e}")
            return None
    
    def convert_to_tflite(self, model_path, output_path):
        """将模型转换为TensorFlow Lite格式"""
        try:
            # 加载模型
            model = tf.keras.models.load_model(model_path)
            
            # 转换为TFLite格式
            converter = tf.lite.TFLiteConverter.from_keras_model(model)
            tflite_model = converter.convert()
            
            # 保存TFLite模型
            with open(output_path, 'wb') as f:
                f.write(tflite_model)
            
            self.logger.info(f"模型已转换为TFLite格式并保存到: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"转换模型到TFLite格式失败: {e}")
            return False
    
    def load_model(self, model_path):
        """加载模型"""
        try:
            self.model = tf.keras.models.load_model(model_path)
            self.logger.info(f"模型加载成功: {model_path}")
            return True
        except Exception as e:
            self.logger.error(f"加载模型失败: {e}")
            return False