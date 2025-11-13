import apiClient from './api';

export const settingsApi = {
  /**
   * Get user settings
   */
  getSettings: async () => {
    try {
      const response = await apiClient.get('/settings');
      return { success: true, data: response.data.settings };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to load settings'
      };
    }
  },

  /**
   * Update user settings
   */
  updateSettings: async (settings) => {
    try {
      const response = await apiClient.put('/settings', settings);
      return {
        success: true,
        data: response.data.settings,
        message: response.data.message
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to save settings'
      };
    }
  },

  /**
   * Send test email
   */
  sendTestEmail: async () => {
    try {
      const response = await apiClient.post('/settings/test-email');
      return {
        success: true,
        message: response.data.message
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to send test email'
      };
    }
  }
};

export default settingsApi;
