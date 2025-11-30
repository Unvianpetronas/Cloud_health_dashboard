import apiClient from './api';
import logger from '../utils/logger';

export const s3Api = {
  /**
   * List all S3 buckets
   * @param {boolean} forceRefresh - Force fresh data collection
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  listBuckets: async (forceRefresh = false) => {
    try {
      const response = await apiClient.get('/s3/buckets', {
        params: { force_refresh: forceRefresh }
      });

      logger.info(`Retrieved ${response.data.total_buckets} S3 buckets`);
      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to list S3 buckets';
      logger.error('S3 buckets error:', errorMessage);
      return { success: false, error: errorMessage };
    }
  },

  /**
   * Get metrics for a specific S3 bucket
   * @param {string} bucketName - Name of the bucket
   * @param {string} region - AWS region of the bucket
   * @param {boolean} forceRefresh - Force fresh data collection
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  getBucketMetrics: async (bucketName, region, forceRefresh = false) => {
    try {
      const response = await apiClient.get('/s3/bucket/metrics', {
        params: {
          bucket_name: bucketName,
          region: region,
          force_refresh: forceRefresh
        }
      });

      logger.info(`Retrieved metrics for bucket ${bucketName}`);
      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || `Failed to get metrics for bucket ${bucketName}`;
      logger.error('S3 bucket metrics error:', errorMessage);
      return { success: false, error: errorMessage };
    }
  },

  /**
   * Get comprehensive S3 summary across all buckets
   * @param {boolean} forceRefresh - Force fresh data collection
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  getSummary: async (forceRefresh = false) => {
    try {
      const response = await apiClient.get('/s3/summary', {
        params: { force_refresh: forceRefresh }
      });

      logger.info('S3 summary retrieved successfully');
      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to get S3 summary';
      logger.error('S3 summary error:', errorMessage);
      return { success: false, error: errorMessage };
    }
  }
};

export default s3Api;
