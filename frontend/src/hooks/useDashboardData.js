import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

const useDashboardData = (timeRange = '24h') => {
  const { token, isAuthenticated } = useAuth();
  const [data, setData] = useState({
    metrics: null,
    costs: null,
    performance: null,
    serviceHealth: null,
    alerts: null,
    serviceStatus: null
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Mock data - trong thực tế sẽ fetch từ API
  const mockData = {
    metrics: [
      {
        title: "Total Monthly Cost",
        value: "$1,847",
        change: "8.2% from last month",
        changeType: "negative"
      },
      {
        title: "Active Resources", 
        value: "247",
        change: "94% healthy",
        changeType: "positive"
      },
      {
        title: "Active Alerts",
        value: "4",
        change: "1 critical",
        changeType: "negative"
      },
      {
        title: "Avg Response Time",
        value: "234ms",
        change: "12ms from avg",
        changeType: "positive"
      }
    ],
    costs: [
      { name: 'Jan', cost: 1200, budget: 1500 },
      { name: 'Feb', cost: 1350, budget: 1500 },
      { name: 'Mar', cost: 1100, budget: 1500 },
      { name: 'Apr', cost: 1400, budget: 1500 },
      { name: 'May', cost: 1250, budget: 1500 },
      { name: 'Jun', cost: 1600, budget: 1500 },
      { name: 'Jul', cost: 1800, budget: 1500 }
    ],
    performance: [
      { time: '00:00', cpu: 45, memory: 62, network: 23, storage: 78 },
      { time: '04:00', cpu: 52, memory: 58, network: 34, storage: 80 },
      { time: '08:00', cpu: 78, memory: 71, network: 67, storage: 82 },
      { time: '12:00', cpu: 85, memory: 76, network: 89, storage: 84 },
      { time: '16:00', cpu: 72, memory: 68, network: 45, storage: 86 },
      { time: '20:00', cpu: 58, memory: 64, network: 32, storage: 88 },
      { time: '24:00', cpu: 48, memory: 59, network: 28, storage: 90 }
    ],
    serviceHealth: [
      { name: 'Healthy', value: 84, color: '#10b981' },
      { name: 'Warning', value: 12, color: '#f59e0b' },
      { name: 'Critical', value: 3, color: '#ef4444' },
      { name: 'Unknown', value: 1, color: '#6b7280' }
    ],
    alerts: [
      {
        id: 1,
        severity: 'critical',
        service: 'EC2',
        message: 'High CPU utilization on instance i-1234567890abcdef0',
        timestamp: '2 minutes ago',
        region: 'us-east-1'
      },
      {
        id: 2,
        severity: 'warning',
        service: 'RDS',
        message: 'Database connection pool near capacity',
        timestamp: '15 minutes ago',
        region: 'us-west-2'
      },
      {
        id: 3,
        severity: 'info',
        service: 'S3',
        message: 'Scheduled maintenance completed successfully',
        timestamp: '1 hour ago',
        region: 'eu-west-1'
      }
    ],
    serviceStatus: [
      { name: 'EC2', status: 'healthy', instances: 24, region: 'us-east-1' },
      { name: 'RDS', status: 'warning', instances: 8, region: 'us-west-2' },
      { name: 'Lambda', status: 'healthy', instances: 156, region: 'global' },
      { name: 'S3', status: 'healthy', instances: 12, region: 'global' },
      { name: 'CloudFront', status: 'critical', instances: 3, region: 'global' },
      { name: 'ELB', status: 'healthy', instances: 15, region: 'us-east-1' }
    ]
  };

  const fetchDashboardData = useCallback(async () => {
    if (!isAuthenticated || !token) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // In real app, make actual API calls here
      // const response = await fetch(`/api/v1/dashboard?timeRange=${timeRange}`, {
      //   headers: {
      //     'Authorization': `Bearer ${token}`,
      //     'Content-Type': 'application/json'
      //   }
      // });
      
      // if (!response.ok) {
      //   throw new Error('Failed to fetch dashboard data');
      // }
      
      // const result = await response.json();
      
      // For now, use mock data
      setData(mockData);
      setLastUpdated(new Date());
      
    } catch (err) {
      setError(err.message);
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, token, timeRange]);

  // Fetch data on mount and when dependencies change
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Auto refresh every 5 minutes
  useEffect(() => {
    if (!isAuthenticated) return;

    const interval = setInterval(() => {
      fetchDashboardData();
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(interval);
  }, [fetchDashboardData, isAuthenticated]);

  const refresh = useCallback(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  return {
    data,
    loading,
    error,
    lastUpdated,
    refresh
  };
};

export default useDashboardData;