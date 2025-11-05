import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ec2Api } from '../services/ec2Api';
import { guarddutyApi } from '../services/guarddutyApi';

const useDashboardData = (timeRange = '24h') => {
  const { isAuthenticated } = useAuth();
  const [data, setData] = useState({
    ec2Summary: null,
    ec2Instances: null,  // NEW: All EC2 instances for table
    ec2Cost: null,
    guarddutyStatus: null,
    guarddutyFindings: null,
    guarddutyCritical: null,
    guarddutySummary: null,
    allFindings: null,  // NEW: Flattened GuardDuty findings for table
    performance: null,
    serviceHealth: null,
    alerts: null,
    serviceStatus: null
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Mock data for performance and service health
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
    ]
  };

  const fetchDashboardData = useCallback(async () => {
    if (!isAuthenticated) {
      console.log('️ Not authenticated, skipping API calls');
      return;
    }

    console.log(' Fetching dashboard data...');
    setLoading(true);
    setError(null);

    try {
      // Fetch REAL EC2 and GuardDuty data in parallel
      console.log(' Calling EC2 and GuardDuty APIs...');
      const [
        summaryResult,
        costResult,
        allInstancesResult,  // NEW: Fetch all EC2 instances
        gdStatusResult,
        gdFindingsResult,
        gdCriticalResult,
        gdSummaryResult
      ] = await Promise.all([
        ec2Api.getInstanceSummary(),
        ec2Api.getCostEstimate(),
        ec2Api.scanAllRegions(),  // NEW: Scan all regions for EC2 instances
        guarddutyApi.getStatus(),
        guarddutyApi.getFindings(),
        guarddutyApi.getCritical(),
        guarddutyApi.getSummary()
      ]);

      console.log(' EC2 Summary Result:', summaryResult);
      console.log(' EC2 Cost Result:', costResult);
      console.log(' EC2 All Instances Result:', allInstancesResult);
      console.log(' GuardDuty Status Result:', gdStatusResult);
      console.log(' GuardDuty Findings Result:', gdFindingsResult);
      console.log('GuardDuty Critical Result:', gdCriticalResult);
      console.log(' GuardDuty Summary Result:', gdSummaryResult);

      // Check for critical errors (EC2)
      if (!summaryResult.success) {
        throw new Error(summaryResult.error);
      }
      if (!costResult.success) {
        throw new Error(costResult.error);
      }

      // GuardDuty errors are non-critical - log but don't fail
      const guarddutyStatus = gdStatusResult.success ? gdStatusResult.data : null;
      const guarddutyFindings = gdFindingsResult.success ? gdFindingsResult.data : null;
      const guarddutyCritical = gdCriticalResult.success ? gdCriticalResult.data : null;
      const guarddutySummary = gdSummaryResult.success ? gdSummaryResult.data : null;

      if (!gdStatusResult.success) {
        console.warn(' GuardDuty status error:', gdStatusResult.error);
      }
      if (!gdFindingsResult.success) {
        console.warn(' GuardDuty findings error:', gdFindingsResult.error);
      }

      // 🆕 NEW: Process EC2 instances - flatten from all regions into single array
      const ec2Instances = allInstancesResult.success && allInstancesResult.data?.regions
        ? allInstancesResult.data.regions.flatMap(regionData =>
            (regionData.instances || []).map(instance => ({
              ...instance,
              Region: regionData.region  // Add region to each instance
            }))
          )
        : [];

      console.log(` Processed ${ec2Instances.length} EC2 instances from all regions`);

      // 🆕 NEW: Process GuardDuty findings - flatten from all regions into single array
      const allFindings = gdFindingsResult.success && gdFindingsResult.data?.regions
        ? gdFindingsResult.data.regions.flatMap(regionData =>
            (regionData.findings || []).map(finding => ({
              ...finding,
              region: regionData.region  // Add region to each finding
            }))
          )
        : [];

      console.log(` Processed ${allFindings.length} GuardDuty findings from all regions`);

      // Create alerts array from GuardDuty critical findings
      const guarddutyAlerts = guarddutyCritical?.findings?.map((finding, index) => ({
        id: `gd-${index}`,
        severity: finding.severity?.toLowerCase() || 'critical',
        service: 'GuardDuty',
        message: finding.title || finding.description || 'Security finding detected',
        timestamp: new Date(finding.updatedAt || finding.createdAt).toLocaleString(),
        region: finding.region || 'unknown'
      })) || [];

      // Mock alerts for demo (you can remove these later)
      const mockAlerts = [
        {
          id: 1,
          severity: 'warning',
          service: 'EC2',
          message: 'High CPU utilization detected on instance',
          timestamp: '5 minutes ago',
          region: 'us-east-1'
        }
      ];

      // Combine alerts
      const allAlerts = [...guarddutyAlerts, ...mockAlerts];

      // Mock service status (you can update this with real data later)
      const serviceStatus = [
        {
          name: 'EC2',
          status: summaryResult.data?.has_instances ? 'healthy' : 'unknown',
          instances: summaryResult.data?.total_instances || 0,
          region: 'multi-region'
        },
        {
          name: 'GuardDuty',
          status: guarddutyStatus?.enabled ? 'healthy' : 'warning',
          instances: guarddutySummary?.total_findings || 0,
          region: 'multi-region'
        }
      ];

      setData({
        ec2Summary: summaryResult.data,
        ec2Instances,  // NEW: Flattened EC2 instances for table
        ec2Cost: costResult.data,
        guarddutyStatus,
        guarddutyFindings,
        guarddutyCritical,
        guarddutySummary,
        allFindings,  // NEW: Flattened GuardDuty findings for table
        performance: mockData.performance,
        serviceHealth: mockData.serviceHealth,
        alerts: allAlerts,
        serviceStatus
      });

      setLastUpdated(new Date());
      console.log(' Dashboard data loaded successfully');

    } catch (err) {
      const errorMessage = err.message || 'Failed to fetch dashboard data';
      setError(errorMessage);
      console.error(' Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, timeRange]);

  useEffect(() => {
    console.log(' useDashboardData mounted, isAuthenticated:', isAuthenticated);
    fetchDashboardData();
  }, [fetchDashboardData]);

  useEffect(() => {
    if (!isAuthenticated) return;

    console.log(' Setting up auto-refresh (5 min)');
    const interval = setInterval(() => {
      console.log(' Auto-refreshing dashboard...');
      fetchDashboardData();
    }, 5 * 60 * 1000);

    return () => {
      console.log(' Cleaning up auto-refresh');
      clearInterval(interval);
    };
  }, [fetchDashboardData, isAuthenticated]);

  const refresh = useCallback(() => {
    console.log(' Manual refresh triggered');
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