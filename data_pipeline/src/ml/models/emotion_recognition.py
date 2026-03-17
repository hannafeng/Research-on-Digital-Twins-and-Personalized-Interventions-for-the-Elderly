import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
import numpy as np
import logging
import librosa

class EmotionRecognitionModel:
    """情感计算模型"""
    
    def __init__(self, model_type="cnn"):
        """初始化情感计算模型"""
        self.logger = logging.getLogger("EmotionRecognitionModel")
        self.model_type = model_type  # "cnn" or "svm"
        self.model = None
        self.scaler = None
        self.class_labels = ["平静", "焦虑", "孤独", "开心", "悲伤"]
        self.input_shape = (40, 100, 1)  # MFCC特征形状
    
    def extract_mfcc(self, audio_file, n_mfcc=40, hop_length=512, n_fft=2048):
        """提取音频的MFCC特征"""
        try:
            # 加载音频文件
            y, sr = librosa.load(audio_file, sr=16000)
            
            # 提取MFCC特征
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc, hop_length=hop_length, n_fft=n_fft)
            
            # 标准化MFCC特征
            mfcc = (mfcc - np.mean(mfcc)) / np.std(mfcc)
            
            # 调整特征形状
            if mfcc.shape[1] < 100:
                # 填充到100个时间步
                mfcc = np.pad(mfcc, ((0, 0), (0, 100 - mfcc.shape[1])), mode='constant')
            else:
                # 截断到100个时间步
                mfcc = mfcc[:, :100]
            
            return mfcc
        except Exception as e:
            self.logger.error(f"提取MFCC特征失败: {e}")
            return None
    
    def build_model(self):
        """构建情感识别模型"""
        try:
            if self.model_type == "cnn":
                # 构建轻量级CNN模型
                self.model = Sequential([
                    Conv2D(32, (3, 3), activation='relu', input_shape=self.input_shape),
                    MaxPooling2D((2, 2)),
                    Dropout(0.2),
                    
                    Conv2D(64, (3, 3), activation='relu'),
                    MaxPooling2D((2, 2)),
                    Dropout(0.2),
                    
                    Flatten(),
                    Dense(128, activation='relu'),
                    Dropout(0.3),
                    Dense(len(self.class_labels), activation='softmax')
                ])
                
                self.model.compile(
                    optimizer='adam',
                    loss='categorical_crossentropy',
                    metrics=['accuracy']
                )
            elif self.model_type == "svm":
                # 使用SVM分类器
                self.model = SVC(kernel='rbf', probability=True)
                self.scaler = StandardScaler()
            
            self.logger.info(f"情感计算模型构建成功，模型类型: {self.model_type}")
            return self.model
        except Exception as e:
            self.logger.error(f"构建情感计算模型失败: {e}")
            return None
    
    def preprocess_data(self, data):
        """预处理数据"""
        try:
            if self.model_type == "cnn":
                # 重塑数据形状
                data = np.reshape(data, (-1, self.input_shape[0], self.input_shape[1], self.input_shape[2]))
            elif self.model_type == "svm":
                # 展平数据
                data = np.reshape(data, (-1, self.input_shape[0] * self.input_shape[1]))
                # 标准化数据
                if self.scaler:
                    data = self.scaler.transform(data)
            
            return data
        except Exception as e:
            self.logger.error(f"数据预处理失败: {e}")
            return None
    
    def train(self, X_train, y_train, X_val, y_val, epochs=50, batch_size=32):
        """训练模型"""
        try:
            if self.model_type == "cnn":
                # 转换标签为one-hot编码
                y_train = tf.keras.utils.to_categorical(y_train, num_classes=len(self.class_labels))
                y_val = tf.keras.utils.to_categorical(y_val, num_classes=len(self.class_labels))
                
                # 训练模型
                history = self.model.fit(
                    X_train, y_train,
                    validation_data=(X_val, y_val),
                    epochs=epochs,
                    batch_size=batch_size,
                    callbacks=[
                        tf.keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
                        tf.keras.callbacks.ModelCheckpoint('models/emotion_model.h5', save_best_only=True)
                    ]
                )
                
                self.logger.info("情感计算模型训练成功")
                return history
            elif self.model_type == "svm":
                # 标准化数据
                self.scaler.fit(X_train)
                X_train = self.scaler.transform(X_train)
                X_val = self.scaler.transform(X_val)
                
                # 训练SVM模型
                self.model.fit(X_train, y_train)
                
                # 评估模型
                accuracy = self.model.score(X_val, y_val)
                self.logger.info(f"SVM模型训练成功，验证准确率: {accuracy:.4f}")
                return accuracy
        except Exception as e:
            self.logger.error(f"训练情感计算模型失败: {e}")
            return None
    
    def predict(self, data):
        """预测情感"""
        try:
            # 预处理数据
            processed_data = self.preprocess_data(data)
            if processed_data is None:
                return None
            
            # 预测
            if self.model_type == "cnn":
                predictions = self.model.predict(processed_data)
            elif self.model_type == "svm":
                predictions = self.model.predict_proba(processed_data)
            
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
            self.logger.error(f"情感计算预测失败: {e}")
            return None
    
    def convert_to_tflite(self, model_path, output_path):
        """将模型转换为TensorFlow Lite格式"""
        try:
            if self.model_type == "cnn":
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
            else:
                self.logger.warning("SVM模型不支持转换为TFLite格式")
                return False
        except Exception as e:
            self.logger.error(f"转换模型到TFLite格式失败: {e}")
            return False
    
    def load_model(self, model_path):
        """加载模型"""
        try:
            if self.model_type == "cnn":
                self.model = tf.keras.models.load_model(model_path)
            elif self.model_type == "svm":
                import joblib
                self.model = joblib.load(model_path)
                # 加载scaler
                scaler_path = model_path.replace('.pkl', '_scaler.pkl')
                self.scaler = joblib.load(scaler_path)
            
            self.logger.info(f"模型加载成功: {model_path}")
            return True
        except Exception as e:
            self.logger.error(f"加载模型失败: {e}")
            return False