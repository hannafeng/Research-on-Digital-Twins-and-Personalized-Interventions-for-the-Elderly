import { useState, useEffect, useRef } from 'react';
import './ElderlyDashboard.css';

const ElderlyDashboard = () => {
  const [commands, setCommands] = useState([]);
  const [callStatus, setCallStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const speechRef = useRef(null);

  useEffect(() => {
    // 使用模拟数据
    const mockCommands = [
      {
        "command_id": "cmd_001",
        "type": "medication",
        "content": "该吃药了",
        "timestamp": "08:00"
      },
      {
        "command_id": "cmd_002",
        "type": "activity",
        "content": "该活动一下了",
        "timestamp": "10:30"
      },
      {
        "command_id": "cmd_003",
        "type": "entertainment",
        "content": "播放怀旧音乐",
        "timestamp": "15:00"
      }
    ];
    
    setCommands(mockCommands);
    // 自动播报第一条指令
    if (mockCommands.length > 0) {
      speakCommand(mockCommands[0].content);
    }
    setLoading(false);
  }, []);

  const speakCommand = (text) => {
    if ('speechSynthesis' in window) {
      const speech = new SpeechSynthesisUtterance(text);
      speech.lang = 'zh-CN';
      speech.volume = 1;
      speech.rate = 0.9;
      speech.pitch = 1;
      window.speechSynthesis.speak(speech);
    }
  };

  const handleCall = async (callType) => {
    try {
      setCallStatus({ status: 'calling', callType });
      const response = await fetch('/api/elderly/call', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: 'user_001',
          call_type: callType
        })
      });

      const result = await response.json();
      setCallStatus(result);
      
      // 模拟通话结束
      setTimeout(() => {
        setCallStatus(null);
      }, 5000);
    } catch (error) {
      console.error('一键呼叫失败:', error);
      setCallStatus({ status: 'failed', callType });
      // 模拟失败后重置
      setTimeout(() => {
        setCallStatus(null);
      }, 3000);
    }
  };

  if (loading) {
    return <div>加载中...</div>;
  }

  return (
    <div className="elderly-dashboard">
      <h1>智能助手</h1>

      {/* 日常指令 */}
      <section className="commands-section">
        <h2>今日计划</h2>
        <div className="commands-list">
          {commands.map(command => (
            <div key={command.command_id} className="command-card">
              <div className="command-time">{command.timestamp}</div>
              <div className="command-content">{command.content}</div>
              <button 
                className="play-button"
                onClick={() => speakCommand(command.content)}
              >
                播放
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* 一键呼叫 */}
      <section className="call-section">
        <h2>紧急求助</h2>
        <div className="call-buttons">
          <button 
            className="emergency-button"
            onClick={() => handleCall('emergency')}
            disabled={callStatus !== null}
          >
            {callStatus && callStatus.callType === 'emergency' ? (
              callStatus.status === 'calling' ? '呼叫中...' :
              callStatus.status === 'connected' ? '已接通' : '呼叫失败'
            ) : '紧急求助'}
          </button>
          <button 
            className="daily-button"
            onClick={() => handleCall('daily')}
            disabled={callStatus !== null}
          >
            {callStatus && callStatus.callType === 'daily' ? (
              callStatus.status === 'calling' ? '呼叫中...' :
              callStatus.status === 'connected' ? '已接通' : '呼叫失败'
            ) : '日常需求'}
          </button>
        </div>
      </section>

      {/* 语音提示 */}
      <section className="voice-section">
        <h2>语音助手</h2>
        <div className="voice-control">
          <button 
            className="voice-button"
            onClick={() => speakCommand('您好，我是您的智能助手，有什么可以帮您的吗？')}
          >
            语音助手
          </button>
        </div>
      </section>
    </div>
  );
};

export default ElderlyDashboard;
