import apiClient from './api';
import logger from '../utils/logger';

export const architectureApi = {
  /**
   * Get comprehensive architecture analysis
   * @param {boolean} forceRefresh - Force fresh data collection
   * @param {boolean} saveReport - Save analysis report to database
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  analyze: async (forceRefresh = false, saveReport = true) => {
    try {
      const response = await apiClient.get('/architecture/analyze', {
        params: { force_refresh: forceRefresh, save_report: saveReport }
      });

      logger.info('Architecture analysis retrieved successfully');
      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to analyze architecture';
      logger.error('Architecture analysis error:', errorMessage);
      return { success: false, error: errorMessage };
    }
  },

  /**
   * Get quick architecture health score
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  getScore: async () => {
    try {
      const response = await apiClient.get('/architecture/score');

      logger.info('Architecture score retrieved:', response.data.overall_score);
      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to get architecture score';
      logger.error('Architecture score error:', errorMessage);
      return { success: false, error: errorMessage };
    }
  },

  /**
   * Get architecture recommendations
   * @param {string} priority - Filter by priority (CRITICAL, HIGH, MEDIUM, LOW)
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  getRecommendations: async (priority = null) => {
    try {
      const params = priority ? { priority } : {};
      const response = await apiClient.get('/architecture/recommendations', { params });

      logger.info(`Retrieved ${response.data.total_recommendations} recommendations`);
      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to get recommendations';
      logger.error('Recommendations error:', errorMessage);
      return { success: false, error: errorMessage };
    }
  },

  /**
   * Get cost optimization analysis
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  getCostOptimization: async () => {
    try {
      const response = await apiClient.get('/architecture/cost-optimization');

      logger.info('Cost optimization analysis retrieved');
      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to get cost optimization';
      logger.error('Cost optimization error:', errorMessage);
      return { success: false, error: errorMessage };
    }
  },

  /**
   * Get AWS Well-Architected Framework scores
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  getWellArchitectedScores: async () => {
    try {
      const response = await apiClient.get('/architecture/well-architected');

      logger.info('Well-Architected scores retrieved');
      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to get Well-Architected scores';
      logger.error('Well-Architected scores error:', errorMessage);
      return { success: false, error: errorMessage };
    }
  }
};

export default architectureApi;
