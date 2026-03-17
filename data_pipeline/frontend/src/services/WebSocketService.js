// 简化版 WebSocketService，避免使用 SockJS 和 Stomp
class WebSocketService {
  constructor() {
    this.subscriptions = {};
  }

  connect() {
    return new Promise((resolve) => {
      console.log('Simulating WebSocket connection for development');
      resolve();
    });
  }

  subscribe(topic, callback) {
    console.log(`Simulating subscription to ${topic}`);
    this.simulateData(topic, callback);
  }

  unsubscribe(topic) {
    if (this.subscriptions[topic]) {
      clearInterval(this.subscriptions[topic]);
      delete this.subscriptions[topic];
    }
  }

  disconnect() {
    console.log('Simulating WebSocket disconnection');
    // 清除所有订阅
    Object.values(this.subscriptions).forEach(interval => clearInterval(interval));
    this.subscriptions = {};
  }

  // 模拟数据推送
  simulateData(topic, callback) {
    if (topic === '/topic/alerts') {
      // 模拟风险预警数据
      const interval = setInterval(() => {
        const mockAlert = {
          alert_id: `alert_${Date.now()}`,
          user_id: `user_${Math.floor(Math.random() * 5) + 1}`,
          risk_level: Math.random() > 0.7 ? 'high' : 'medium',
          abnormal指标: Math.random() > 0.5 ? '心率异常' : '活动量过低',
          message: Math.random() > 0.5 ? '老人心率异常，请及时处理' : '老人活动量过低，建议提醒活动',
          timestamp: new Date().toISOString()
        };
        callback(mockAlert);
      }, 30000); // 每30秒发送一次
      this.subscriptions[topic] = interval;
    } else if (topic === '/topic/status') {
      // 模拟状态更新数据
      const interval = setInterval(() => {
        const mockStatus = {
          user_id: `user_${Math.floor(Math.random() * 5) + 1}`,
          health_metrics: {
            heart_rate: Math.floor(Math.random() * 30) + 60,
            blood_pressure: `${Math.floor(Math.random() * 20) + 110}/${Math.floor(Math.random() * 15) + 70}`,
            steps: Math.floor(Math.random() * 1000) + 3000
          },
          timestamp: new Date().toISOString()
        };
        callback(mockStatus);
      }, 15000); // 每15秒发送一次
      this.subscriptions[topic] = interval;
    } else if (topic === '/topic/devices') {
      // 模拟设备状态更新
      const interval = setInterval(() => {
        const mockDeviceUpdate = {
          device_id: `device_00${Math.floor(Math.random() * 5) + 1}`,
          status: Math.random() > 0.8 ? 'offline' : 'online',
          last_data_time: new Date().toISOString()
        };
        callback(mockDeviceUpdate);
      }, 45000); // 每45秒发送一次
      this.subscriptions[topic] = interval;
    }
  }
}

export default new WebSocketService();