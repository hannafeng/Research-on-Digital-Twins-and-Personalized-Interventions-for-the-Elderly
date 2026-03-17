import { useState, useEffect } from 'react';
import { Card, Table, Button, Badge, Popconfirm, message, Alert } from 'antd';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 模拟数据
    const mockDevices = [
      {
        device_id: 'device_001',
        type: '可穿戴设备',
        status: 'online',
        battery: 85,
        last_data_time: new Date().toISOString(),
        location: '老人卧室'
      },
      {
        device_id: 'device_002',
        type: '环境传感器',
        status: 'online',
        battery: 72,
        last_data_time: new Date().toISOString(),
        location: '客厅'
      },
      {
        device_id: 'device_003',
        type: '音频设备',
        status: 'offline',
        battery: 45,
        last_data_time: new Date(Date.now() - 3600000).toISOString(),
        location: '老人卧室'
      },
      {
        device_id: 'device_004',
        type: '可穿戴设备',
        status: 'offline',
        battery: 20,
        last_data_time: new Date(Date.now() - 7200000).toISOString(),
        location: '老人浴室'
      },
      {
        device_id: 'device_005',
        type: '环境传感器',
        status: 'online',
        battery: 90,
        last_data_time: new Date().toISOString(),
        location: '厨房'
      }
    ];
    
    setDevices(mockDevices);
    setLoading(false);
  }, []);

  const handleRestartDevice = (deviceId) => {
    setDevices(prev => prev.map(device => 
      device.device_id === deviceId 
        ? { ...device, status: 'restarting' }
        : device
    ));
    message.info('设备重启指令已发送');
    
    // 模拟重启成功
    setTimeout(() => {
      setDevices(prev => prev.map(device => 
        device.device_id === deviceId 
          ? { ...device, status: 'online', last_data_time: new Date().toISOString() }
          : device
      ));
      message.success('设备重启成功');
    }, 2000);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'online': return 'green';
      case 'offline': return 'red';
      case 'restarting': return 'orange';
      default: return 'blue';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'online': return '在线';
      case 'offline': return '离线';
      case 'restarting': return '重启中';
      default: return '未知';
    }
  };

  const columns = [
    {
      title: '设备ID',
      dataIndex: 'device_id',
      key: 'device_id',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Badge color={getStatusColor(status)} text={getStatusText(status)} />
      ),
    },
    {
      title: '电池电量',
      dataIndex: 'battery',
      key: 'battery',
      render: (battery) => `${battery}%`,
    },
    {
      title: '最后数据时间',
      dataIndex: 'last_data_time',
      key: 'last_data_time',
      render: (time) => new Date(time).toLocaleString(),
    },
    {
      title: '位置',
      dataIndex: 'location',
      key: 'location',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Popconfirm
          title="确定重启设备？"
          onConfirm={() => handleRestartDevice(record.device_id)}
          okText="确定"
          cancelText="取消"
        >
          <Button 
            type="primary" 
            disabled={record.status !== 'offline'}
          >
            一键重启
          </Button>
        </Popconfirm>
      ),
    },
  ];

  const offlineDevices = devices.filter(device => device.status === 'offline');

  if (loading) {
    return <div>加载中...</div>;
  }

  return (
    <div className="admin-dashboard">
      <Card title="设备管理后台" className="main-card">
        {/* 离线设备告警 */}
        {offlineDevices.length > 0 && (
          <Alert
            message={`离线设备告警：${offlineDevices.length} 台设备离线`}
            description={`离线设备：${offlineDevices.map(device => device.device_id).join('、')}`}
            type="error"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}
        
        {/* 设备列表 */}
        <Table
          dataSource={devices}
          columns={columns}
          rowKey="device_id"
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
};

export default AdminDashboard;
