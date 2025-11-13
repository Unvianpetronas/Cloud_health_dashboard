import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ec2Api } from '../services/ec2Api';
import { guarddutyApi } from '../services/guarddutyApi';
import logger from '../utils/logger';

const useDashboardData = (timeRange = '24h') => {
  const { isAuthenticated } = useAuth();
  const [data, setData] = useState({
    ec2Summary: null,
    ec2Instances: null,
    ec2Cost: null,
    guarddutyStatus: null,
    guarddutyFindings: null,
    guarddutyCritical: null,
    guarddutySummary: null,
    allFindings: null,
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
      logger.debug('Not authenticated, skipping API calls');
      return;
    }

    logger.info('Fetching dashboard data...');
    setLoading(true);
    setError(null);

    try {
      // Fetch REAL EC2 and GuardDuty data in parallel
      logger.debug('Calling EC2 and GuardDuty APIs...');
      const [
        summaryResult,
        costResult,
        allInstancesResult,
        gdStatusResult,
        gdFindingsResult,
        gdCriticalResult,
        gdSummaryResult
      ] = await Promise.all([
        ec2Api.getInstanceSummary(),
        ec2Api.getCostEstimate(),
        ec2Api.scanAllRegions(),
        guarddutyApi.getStatus(),
        guarddutyApi.getFindings(),
        guarddutyApi.getCritical(),
        guarddutyApi.getSummary()
      ]);

      logger.debug('EC2 Summary Result:', summaryResult);
      logger.debug('EC2 Cost Result:', costResult);
      logger.debug('EC2 All Instances Result:', allInstancesResult);
      logger.debug('GuardDuty Status Result:', gdStatusResult);
      logger.debug('GuardDuty Findings Result:', gdFindingsResult);
      logger.debug('GuardDuty Critical Result:', gdCriticalResult);
      logger.debug('GuardDuty Summary Result:', gdSummaryResult);

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
        logger.warn('GuardDuty status error:', gdStatusResult.error);
      }
      if (!gdFindingsResult.success) {
        logger.warn('GuardDuty findings error:', gdFindingsResult.error);
      }

      // Process EC2 instances - get from flat array and add region
      const ec2Instances = allInstancesResult.success && allInstancesResult.data?.instances
        ? allInstancesResult.data.instances.map(instance => {
            // Extract region from Placement.AvailabilityZone (e.g., "us-east-1a" -> "us-east-1")
            const az = instance.Placement?.AvailabilityZone || '';
            const region = az.slice(0, -1); // Remove last character (zone letter)

            return {
              ...instance,
              Region: region || 'unknown'  // Add region to each instance
            };
          })
        : [];

      logger.debug(`Processed ${ec2Instances.length} EC2 instances from all regions`);

      // Process GuardDuty findings - get from flat array
      const allFindings = gdFindingsResult.success && gdFindingsResult.data?.findings
        ? gdFindingsResult.data.findings.map(finding => ({
            ...finding,
            region: finding.region || 'unknown'
          }))
        : [];

      logger.debug(`Processed ${allFindings.length} GuardDuty findings from all regions`);

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
        ec2Instances,
        ec2Cost: costResult.data,
        guarddutyStatus,
        guarddutyFindings,
        guarddutyCritical,
        guarddutySummary,
        allFindings,
        performance: mockData.performance,
        serviceHealth: mockData.serviceHealth,
        alerts: allAlerts,
        serviceStatus
      });

      setLastUpdated(new Date());
      logger.info('Dashboard data loaded successfully');

    } catch (err) {
      const errorMessage = err.message || 'Failed to fetch dashboard data';
      setError(errorMessage);
      logger.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    logger.debug('useDashboardData mounted, isAuthenticated:', isAuthenticated);
    fetchDashboardData();
  }, [fetchDashboardData]);

  useEffect(() => {
    if (!isAuthenticated) return;

    logger.info('Setting up auto-refresh (5 min)');
    const interval = setInterval(() => {
      logger.info('Auto-refreshing dashboard...');
      fetchDashboardData();
    }, 5 * 60 * 1000);

    return () => {
      logger.debug('Cleaning up auto-refresh');
      clearInterval(interval);
    };
  }, [fetchDashboardData, isAuthenticated]);

  const refresh = useCallback(() => {
    logger.info('Manual refresh triggered');
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
