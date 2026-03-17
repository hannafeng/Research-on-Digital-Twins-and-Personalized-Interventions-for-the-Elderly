import { useState, useEffect, useRef } from 'react';
import { Card, Button, Alert, Divider, Space, message } from 'antd';
import * as echarts from 'echarts';
import './FamilyDashboard.css';

const FamilyDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const trendChartRef = useRef(null);
  const trendChart = useRef(null);

  useEffect(() => {
    // 模拟数据
    const mockDashboardData = {
      "user_id": "user_001",
      "name": "张三",
      "todaySummary": {
        "activityStatus": "正常",
        "medicationCount": 2,
        "alertStatus": "无异常"
      },
      "healthTrends": {
        "heartRate": [75, 78, 72, 76, 74, 77, 75],
        "steps": [3500, 3200, 3800, 3600, 3400, 3700, 3500]
      },
      "lastUpdated": new Date().toISOString()
    };
    
    setDashboardData(mockDashboardData);
    setLoading(false);
  }, []);

  useEffect(() => {
    if (dashboardData && !loading) {
      initTrendChart();
    }
    
    return () => {
      if (trendChart.current) trendChart.current.dispose();
    };
  }, [dashboardData, loading]);

  const initTrendChart = () => {
    if (trendChartRef.current) {
      trendChart.current = echarts.init(trendChartRef.current);
      const option = {
        title: {
          text: '近7天健康趋势',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: ['心率', '步数'],
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
          data: ['1月25日', '1月26日', '1月27日', '1月28日', '1月29日', '1月30日', '1月31日']
        },
        yAxis: [
          {
            type: 'value',
            name: '心率 (BPM)',
            position: 'left',
            min: 60,
            max: 90
          },
          {
            type: 'value',
            name: '步数',
            position: 'right',
            min: 3000,
            max: 4000
          }
        ],
        series: [
          {
            name: '心率',
            type: 'line',
            data: dashboardData.healthTrends.heartRate,
            smooth: true,
            lineStyle: {
              color: '#1890ff'
            }
          },
          {
            name: '步数',
            type: 'line',
            yAxisIndex: 1,
            data: dashboardData.healthTrends.steps,
            smooth: true,
            lineStyle: {
              color: '#52c41a'
            }
          }
        ]
      };
      trendChart.current.setOption(option);
    }
  };

  const handleEmergencyContact = () => {
    message.info('紧急联系功能已触发，正在联系相关人员...');
    // 这里可以添加实际的紧急联系逻辑
  };

  if (loading) {
    return <div>加载中...</div>;
  }

  return (
    <div className="family-dashboard">
      <Card title="老人家属仪表盘" className="main-card">
        <div className="dashboard-header">
          <h2>{dashboardData.name} ({dashboardData.user_id})</h2>
          <Button 
            type="primary" 
            danger 
            size="large"
            onClick={handleEmergencyContact}
            className="emergency-button"
          >
            紧急联系
          </Button>
        </div>
        
        <Divider />
        
        {/* 今日状态摘要 */}
        <Card title="今日状态摘要" className="summary-card">
          <Alert
            message="状态正常"
            description={`活动量${dashboardData.todaySummary.activityStatus}，已服药 ${dashboardData.todaySummary.medicationCount} 次，${dashboardData.todaySummary.alertStatus}告警`}
            type="success"
            showIcon
          />
        </Card>
        
        <Divider />
        
        {/* 近7天健康趋势图 */}
        <Card title="健康趋势" className="trend-card">
          <div ref={trendChartRef} className="trend-chart"></div>
        </Card>
        
        <Divider />
        
        {/* 快速操作 */}
        <div className="quick-actions">
          <Space size="middle">
            <Button type="default">查看详细报告</Button>
            <Button type="default">设置通知规则</Button>
            <Button type="default">查看历史记录</Button>
          </Space>
        </div>
      </Card>
    </div>
  );
};

export default FamilyDashboard;
