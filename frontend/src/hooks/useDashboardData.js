import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ec2Api } from '../services/ec2Api';

const useDashboardData = (timeRange = '24h') => {
  const { isAuthenticated } = useAuth();
  const [data, setData] = useState({
    ec2Summary: null,
    ec2Cost: null,
    performance: null,
    serviceHealth: null,
    alerts: null,
    serviceStatus: null
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Mock data
  const mockData = {
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
    // ✅ Only check isAuthenticated
    if (!isAuthenticated) {
      console.log('⚠️ Not authenticated, skipping API calls');
      return;
    }

    console.log('🔄 Fetching dashboard data...');
    setLoading(true);
    setError(null);

    try {
      // Fetch REAL EC2 data
      console.log('📡 Calling EC2 APIs...');
      const [summaryResult, costResult] = await Promise.all([
        ec2Api.getInstanceSummary(),
        ec2Api.getCostEstimate()
      ]);

      console.log('📊 Summary Result:', summaryResult);
      console.log('💰 Cost Result:', costResult);

      if (!summaryResult.success) {
        throw new Error(summaryResult.error);
      }
      if (!costResult.success) {
        throw new Error(costResult.error);
      }

      setData({
        ec2Summary: summaryResult.data,
        ec2Cost: costResult.data,
        performance: mockData.performance,
        serviceHealth: mockData.serviceHealth,
        alerts: mockData.alerts,
        serviceStatus: mockData.serviceStatus
      });

      setLastUpdated(new Date());
      console.log('✅ Dashboard data loaded successfully');

    } catch (err) {
      const errorMessage = err.message || 'Failed to fetch dashboard data';
      setError(errorMessage);
      console.error('❌ Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, timeRange]); // ✅ Removed token dependency

  useEffect(() => {
    console.log('🎯 useDashboardData mounted, isAuthenticated:', isAuthenticated);
    fetchDashboardData();
  }, [fetchDashboardData]);

  useEffect(() => {
    if (!isAuthenticated) return;

    console.log('⏰ Setting up auto-refresh (5 min)');
    const interval = setInterval(() => {
      console.log('🔄 Auto-refreshing dashboard...');
      fetchDashboardData();
    }, 5 * 60 * 1000);

    return () => {
      console.log('🛑 Cleaning up auto-refresh');
      clearInterval(interval);
    };
  }, [fetchDashboardData, isAuthenticated]);

  const refresh = useCallback(() => {
    console.log('🔄 Manual refresh triggered');
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