import apiClient from './api';
import logger from '../utils/logger';

export const costExplorerApi = {
  /**
   * Get total cost for a date range
   * @param {string} startDate - Start date (YYYY-MM-DD)
   * @param {string} endDate - End date (YYYY-MM-DD)
   * @param {string} granularity - DAILY | MONTHLY | HOURLY (default: MONTHLY)
   * @param {boolean} forceRefresh - Force fresh data collection
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  getTotalCost: async (startDate, endDate, granularity = 'MONTHLY', forceRefresh = false) => {
    try {
      const response = await apiClient.get('/costexplorer/total-cost', {
        params: {
          start_date: startDate,
          end_date: endDate,
          granularity,
          force_refresh: forceRefresh
        }
      });

      logger.info('Total cost retrieved successfully');
      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to get total cost';
      logger.error('Total cost error:', errorMessage);
      return { success: false, error: errorMessage };
    }
  },

  /**
   * Get cost breakdown by service
   * @param {string} startDate - Start date (YYYY-MM-DD)
   * @param {string} endDate - End date (YYYY-MM-DD)
   * @param {string} granularity - DAILY | MONTHLY | HOURLY (default: MONTHLY)
   * @param {boolean} forceRefresh - Force fresh data collection
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  getCostByService: async (startDate, endDate, granularity = 'MONTHLY', forceRefresh = false) => {
    try {
      const response = await apiClient.get('/costexplorer/by-service', {
        params: {
          start_date: startDate,
          end_date: endDate,
          granularity,
          force_refresh: forceRefresh
        }
      });

      logger.info('Cost by service retrieved successfully');
      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to get cost by service';
      logger.error('Cost by service error:', errorMessage);
      return { success: false, error: errorMessage };
    }
  },

  /**
   * Get cost breakdown by account
   * @param {string} startDate - Start date (YYYY-MM-DD)
   * @param {string} endDate - End date (YYYY-MM-DD)
   * @param {string} granularity - DAILY | MONTHLY | HOURLY (default: MONTHLY)
   * @param {boolean} forceRefresh - Force fresh data collection
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  getCostByAccount: async (startDate, endDate, granularity = 'MONTHLY', forceRefresh = false) => {
    try {
      const response = await apiClient.get('/costexplorer/by-account', {
        params: {
          start_date: startDate,
          end_date: endDate,
          granularity,
          force_refresh: forceRefresh
        }
      });

      logger.info('Cost by account retrieved successfully');
      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to get cost by account';
      logger.error('Cost by account error:', errorMessage);
      return { success: false, error: errorMessage };
    }
  },

  /**
   * Get cost forecast
   * @param {number} daysAhead - Number of days to forecast (default: 30)
   * @param {string} metric - Metric type (default: UNBLENDED_COST)
   * @param {boolean} forceRefresh - Force fresh data collection
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  getForecast: async (daysAhead = 30, metric = 'UNBLENDED_COST', forceRefresh = false) => {
    try {
      const response = await apiClient.get('/costexplorer/forecast', {
        params: {
          days_ahead: daysAhead,
          metric,
          force_refresh: forceRefresh
        }
      });

      logger.info('Cost forecast retrieved successfully');
      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to get cost forecast';
      logger.error('Cost forecast error:', errorMessage);
      return { success: false, error: errorMessage };
    }
  },

  /**
   * Get rightsizing recommendations
   * @param {string} service - Service to get recommendations for (default: AmazonEC2)
   * @param {boolean} forceRefresh - Force fresh data collection
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  getRightsizing: async (service = 'AmazonEC2', forceRefresh = false) => {
    try {
      const response = await apiClient.get('/costexplorer/rightsizing', {
        params: {
          service,
          force_refresh: forceRefresh
        }
      });

      logger.info('Rightsizing recommendations retrieved successfully');
      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to get rightsizing recommendations';
      logger.error('Rightsizing error:', errorMessage);
      return { success: false, error: errorMessage };
    }
  },

  /**
   * Get comprehensive cost summary
   * @param {number} startDaysAgo - Number of days back to start (default: 30)
   * @param {string} granularity - DAILY | MONTHLY | HOURLY (default: MONTHLY)
   * @param {number} forecastDays - Number of days to forecast (default: 30)
   * @param {boolean} forceRefresh - Force fresh data collection
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  getSummary: async (startDaysAgo = 30, granularity = 'MONTHLY', forecastDays = 30, forceRefresh = false) => {
    try {
      const response = await apiClient.get('/costexplorer/summary', {
        params: {
          start_days_ago: startDaysAgo,
          granularity,
          forecast_days: forecastDays,
          force_refresh: forceRefresh
        }
      });

      logger.info('Cost summary retrieved successfully');
      return { success: true, data: response.data };
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to get cost summary';
      logger.error('Cost summary error:', errorMessage);
      return { success: false, error: errorMessage };
    }
  }
};

export default costExplorerApi;
