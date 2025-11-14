import apiClient from './api';
import logger from '../utils/logger';

export const cloudwatchApi = {
  /**
   * Get CloudWatch metrics
   * @param {object} params - Query parameters
   * @param {string} params.namespace - CloudWatch namespace (e.g., "AWS/EC2")
   * @param {string} params.metricName - Metric name (e.g., "CPUUtilization")
   * @param {string} params.dimensions - Optional dimensions (format: "Name1:Value1,Name2:Value2")
   * @param {number} params.startMinutesAgo - Time range in minutes (default: 60)
   * @param {number} params.period - Period in seconds (default: 300)
   * @param {string} params.stat - Statistic type (default: "Average")
   * @param {boolean} params.forceRefresh - Force fresh data collection
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  getMetrics: async ({
    namespace,
    metricName,
    dimensions = null,
    startMinutesAgo = 60,
    period = 300,
    stat = 'Average',
    forceRefresh = false
  }) => {
    try {
      const params = {
        namespace,
        metric_name: metricName,
        start_minutes_ago: startMinutesAgo,
        period,
        stat,
        force_refresh: forceRefresh
      };

      if (dimensions) {
        params.dimensions = dimensions;
      }

      const response = await apiClient.get('/cloudwatch/metrics', { params });

      logger.info(`Retrieved CloudWatch metrics for ${namespace}/${metricName}`);
      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to get CloudWatch metrics';
      logger.error('CloudWatch metrics error:', errorMessage);
      return { success: false, error: errorMessage };
    }
  },

  /**
   * Get EC2 CPU metrics for a specific instance
   * @param {string} instanceId - EC2 instance ID
   * @param {number} startMinutesAgo - Time range in minutes
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  getEC2CPUMetrics: async (instanceId, startMinutesAgo = 60) => {
    return cloudwatchApi.getMetrics({
      namespace: 'AWS/EC2',
      metricName: 'CPUUtilization',
      dimensions: `InstanceId:${instanceId}`,
      startMinutesAgo
    });
  },

  /**
   * Get RDS metrics for a specific database
   * @param {string} dbInstanceId - RDS instance ID
   * @param {string} metricName - Metric name (e.g., "CPUUtilization", "DatabaseConnections")
   * @param {number} startMinutesAgo - Time range in minutes
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  getRDSMetrics: async (dbInstanceId, metricName = 'CPUUtilization', startMinutesAgo = 60) => {
    return cloudwatchApi.getMetrics({
      namespace: 'AWS/RDS',
      metricName,
      dimensions: `DBInstanceIdentifier:${dbInstanceId}`,
      startMinutesAgo
    });
  }
};

export default cloudwatchApi;
