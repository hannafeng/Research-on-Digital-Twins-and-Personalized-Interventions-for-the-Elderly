import { useState, useEffect, useRef } from 'react';
import { Layout, Card, Button, Badge, Table, Alert, Divider, Space, Popconfirm, message } from 'antd';
import * as echarts from 'echarts';
import WebSocketService from '../services/WebSocketService';
import './CaregiverDashboard.css';

const { Header, Sider, Content } = Layout;

const CaregiverDashboard = ({ onLogout }) => {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [interventions, setInterventions] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // 图表实例引用
  const healthChartRef = useRef(null);
  const activityChartRef = useRef(null);
  const emotionChartRef = useRef(null);
  
  // 图表实例
  const healthChart = useRef(null);
  const activityChart = useRef(null);
  const emotionChart = useRef(null);

  useEffect(() => {
    // 模拟数据
    const mockUsers = [
      { id: '001', name: '张三', riskLevel: 'high', age: 78, gender: '男' },
      { id: '003', name: '李四', riskLevel: 'high', age: 82, gender: '女' },
      { id: '005', name: '王五', riskLevel: 'medium', age: 75, gender: '男' },
      { id: '002', name: '赵六', riskLevel: 'medium', age: 79, gender: '女' },
      { id: '004', name: '孙七', riskLevel: 'low', age: 72, gender: '男' },
    ];
    
    const mockInterventions = [
      {
        id: 'int_001',
        userId: '001',
        reason: '心率异常升高',
        confidence: 0.95,
        suggestion: '建议立即联系老人并安排医疗检查',
        status: 'pending'
      },
      {
        id: 'int_002',
        userId: '003',
        reason: '长时间无活动',
        confidence: 0.88,
        suggestion: '建议上门查看老人情况',
        status: 'pending'
      }
    ];
    
    setUsers(mockUsers);
    setInterventions(mockInterventions);
    setSelectedUser(mockUsers[0]);
    setLoading(false);
    
    // 连接 WebSocket 服务（添加错误处理）
    try {
      WebSocketService.connect().then(() => {
        // 订阅风险预警
        WebSocketService.subscribe('/topic/alerts', (alert) => {
          console.log('Received alert:', alert);
          // 处理新的预警
          message.warning(`新预警: ${alert.message}`);
        });
        
        // 订阅状态更新
        WebSocketService.subscribe('/topic/status', (status) => {
          console.log('Received status update:', status);
          // 处理状态更新
          if (selectedUser && status.user_id === selectedUser.id) {
            // 更新选中用户的状态
            initCharts();
          }
        });
      }).catch((error) => {
        console.error('WebSocket connection error:', error);
        // 即使 WebSocket 连接失败，组件也能正常显示
      });
    } catch (error) {
      console.error('WebSocket initialization error:', error);
      // 即使 WebSocket 初始化失败，组件也能正常显示
    }
    
    // 组件卸载时断开连接
    return () => {
      try {
        WebSocketService.disconnect();
      } catch (error) {
        console.error('WebSocket disconnect error:', error);
      }
    };
  }, [selectedUser]);

  useEffect(() => {
    if (selectedUser && !loading) {
      initCharts();
    }
    
    return () => {
      // 销毁图表实例
      if (healthChart.current) healthChart.current.dispose();
      if (activityChart.current) activityChart.current.dispose();
      if (emotionChart.current) emotionChart.current.dispose();
    };
  }, [selectedUser, loading]);

  const initCharts = () => {
    // 健康状态图表（心率/血压折线图）
    if (healthChartRef.current) {
      healthChart.current = echarts.init(healthChartRef.current);
      const healthOption = {
        title: {
          text: '健康状态',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: ['心率', '收缩压', '舒张压'],
          bottom: 0
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          top: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            name: '心率',
            type: 'line',
            data: [75, 72, 85, 90, 88, 76],
            smooth: true
          },
          {
            name: '收缩压',
            type: 'line',
            data: [120, 118, 130, 135, 132, 125],
            smooth: true
          },
          {
            name: '舒张压',
            type: 'line',
            data: [80, 78, 85, 88, 86, 82],
            smooth: true
          }
        ]
      };
      healthChart.current.setOption(healthOption);
    }
    
    // 行为状态图表（活动热力图）
    if (activityChartRef.current) {
      activityChart.current = echarts.init(activityChartRef.current);
      const activityOption = {
        title: {
          text: '近24小时活动热力图',
          left: 'center'
        },
        tooltip: {
          position: 'top'
        },
        grid: {
          height: '60%',
          top: '10%'
        },
        xAxis: {
          type: 'category',
          data: ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00'],
          splitArea: {
            show: true
          }
        },
        yAxis: {
          type: 'category',
          data: ['低活动', '中活动', '高活动'],
          splitArea: {
            show: true
          }
        },
        visualMap: {
          min: 0,
          max: 100,
          calculable: true,
          orient: 'horizontal',
          left: 'center',
          bottom: '5%'
        },
        series: [
          {
            name: '活动强度',
            type: 'heatmap',
            data: [
              [0, 0, 80], [0, 1, 20], [0, 2, 5],
              [1, 0, 90], [1, 1, 10], [1, 2, 0],
              [2, 0, 70], [2, 1, 30], [2, 2, 10],
              [3, 0, 30], [3, 1, 50], [3, 2, 40],
              [4, 0, 40], [4, 1, 45], [4, 2, 35],
              [5, 0, 35], [5, 1, 50], [5, 2, 45],
              [6, 0, 45], [6, 1, 40], [6, 2, 30],
              [7, 0, 60], [7, 1, 30], [7, 2, 10]
            ],
            label: {
              show: true
            },
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      };
      activityChart.current.setOption(activityOption);
    }
    
    // 情感状态图表（情感标签占比饼图）
    if (emotionChartRef.current) {
      emotionChart.current = echarts.init(emotionChartRef.current);
      const emotionOption = {
        title: {
          text: '近30分钟情感标签占比',
          left: 'center'
        },
        tooltip: {
          trigger: 'item'
        },
        legend: {
          orient: 'vertical',
          left: 'left'
        },
        series: [
          {
            name: '情感状态',
            type: 'pie',
            radius: '60%',
            data: [
              { value: 60, name: '平静' },
              { value: 20, name: '愉快' },
              { value: 10, name: '焦虑' },
              { value: 10, name: '其他' }
            ],
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      };
      emotionChart.current.setOption(emotionOption);
    }
  };

  const handleConfirmIntervention = (intervention) => {
    setInterventions(prev => prev.map(item => 
      item.id === intervention.id ? { ...item, status: 'confirmed' } : item
    ));
    message.success('干预建议已确认执行');
  };

  const handleRejectIntervention = (intervention) => {
    setInterventions(prev => prev.map(item => 
      item.id === intervention.id ? { ...item, status: 'rejected' } : item
    ));
    message.info('干预建议已驳回');
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'high': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'green';
      default: return 'blue';
    }
  };

  const getRiskText = (level) => {
    switch (level) {
      case 'high': return '高风险';
      case 'medium': return '中风险';
      case 'low': return '低风险';
      default: return '未知';
    }
  };

  const columns = [
    {
      title: '用户ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '年龄',
      dataIndex: 'age',
      key: 'age',
    },
    {
      title: '性别',
      dataIndex: 'gender',
      key: 'gender',
    },
    {
      title: '风险等级',
      dataIndex: 'riskLevel',
      key: 'riskLevel',
      render: (level) => (
        <Badge color={getRiskColor(level)} text={getRiskText(level)} />
      ),
    },
  ];

  if (loading) {
    return <div>加载中...</div>;
  }

  return (
    <Layout className="caregiver-dashboard">
      {/* 顶部风险预警栏 */}
      <Header className="header">
        <div className="header-content">
          <h1>社区护理人员控制台</h1>
          <div className="header-actions">
            <Alert
              message="高风险用户预警"
              description="高风险用户：001、003"
              type="error"
              showIcon
              action={
                <Button size="small" type="primary">
                  查看详情
                </Button>
              }
              className="alert-warning"
            />
            <Button 
              type="default" 
              onClick={onLogout}
              style={{ marginLeft: 16 }}
            >
              退出登录
            </Button>
          </div>
        </div>
      </Header>
      
      <Layout>
        {/* 左侧用户列表 */}
        <Sider width={300} className="sider">
          <Card title="用户列表" className="user-list-card">
            <Table
              dataSource={users}
              columns={columns}
              rowKey="id"
              onRow={(record) => ({
                onClick: () => setSelectedUser(record),
              })}
              pagination={false}
              rowClassName={(record) => record.id === selectedUser?.id ? 'selected-row' : ''}
            />
          </Card>
        </Sider>
        
        {/* 中间数字孪生状态面板 */}
        <Content className="content">
          <Card title={`${selectedUser?.name} (${selectedUser?.id}) 的数字孪生状态`} className="status-panel">
            <div className="chart-container">
              <div className="chart-item">
                <div ref={healthChartRef} className="chart"></div>
              </div>
              <div className="chart-item">
                <div ref={activityChartRef} className="chart"></div>
              </div>
              <div className="chart-item">
                <div ref={emotionChartRef} className="chart"></div>
              </div>
            </div>
          </Card>
        </Content>
        
        {/* 右侧干预建议区 */}
        <Sider width={350} className="sider">
          <Card title="干预建议" className="intervention-card">
            {interventions.length > 0 ? (
              interventions.map(intervention => (
                <div key={intervention.id} className="intervention-item">
                  <Divider orientation="left">用户 {intervention.userId}</Divider>
                  <p><strong>理由：</strong>{intervention.reason}</p>
                  <p><strong>置信度：</strong>{(intervention.confidence * 100).toFixed(0)}%</p>
                  <p><strong>建议：</strong>{intervention.suggestion}</p>
                  <Space style={{ marginTop: 16 }}>
                    <Popconfirm
                      title="确认执行干预建议？"
                      onConfirm={() => handleConfirmIntervention(intervention)}
                      okText="确认"
                      cancelText="取消"
                    >
                      <Button type="primary" disabled={intervention.status !== 'pending'}>
                        确认执行
                      </Button>
                    </Popconfirm>
                    <Popconfirm
                      title="确定驳回干预建议？"
                      onConfirm={() => handleRejectIntervention(intervention)}
                      okText="确认"
                      cancelText="取消"
                    >
                      <Button disabled={intervention.status !== 'pending'}>
                        驳回
                      </Button>
                    </Popconfirm>
                  </Space>
                  {intervention.status === 'confirmed' && (
                    <Badge status="success" text="已确认执行" style={{ marginTop: 8, display: 'inline-block' }} />
                  )}
                  {intervention.status === 'rejected' && (
                    <Badge status="default" text="已驳回" style={{ marginTop: 8, display: 'inline-block' }} />
                  )}
                </div>
              ))
            ) : (
              <p>暂无干预建议</p>
            )}
          </Card>
        </Sider>
      </Layout>
    </Layout>
  );
};

export default CaregiverDashboard;
