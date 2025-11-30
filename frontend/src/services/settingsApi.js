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
  },

  /**
   * Verify email with token (called when user clicks email link)
   */
  verifyEmail: async (token) => {
    try {
      const response = await apiClient.get(`/email/verify?token=${token}`);
      return {
        success: true,
        data: response.data,
        message: response.data.message
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to verify email. Token may be invalid or expired.'
      };
    }
  },

  /**
   * Get email verification status
   */
  getVerificationStatus: async () => {
    try {
      const response = await apiClient.get('/email/verification-status');
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to get verification status'
      };
    }
  },

  /**
   * Send verification email
   */
  sendVerificationEmail: async (awsAccountId) => {
    try {
      const response = await apiClient.post('/email/send-verification', {
        aws_account_id: awsAccountId
      });
      return {
        success: true,
        data: response.data,
        message: response.data.message
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to send verification email'
      };
    }
  },

  /**
   * Resend verification email
   */
  resendVerificationEmail: async (awsAccountId) => {
    try {
      const response = await apiClient.post('/email/resend-verification', {
        aws_account_id: awsAccountId
      });
      return {
        success: true,
        data: response.data,
        message: response.data.message
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to resend verification email'
      };
    }
  },

  /**
   * Update email address
   */
  updateEmail: async (email) => {
    try {
      const response = await apiClient.put('/email/update', {
        email: email
      });
      return {
        success: true,
        data: response.data,
        message: response.data.message
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to update email'
      };
    }
  },

  /**
   * Toggle notification preferences
   */
  toggleNotifications: async (enabled) => {
    try {
      const response = await apiClient.post('/email/notification', {
        enabled: enabled
      });
      return {
        success: true,
        data: response.data,
        message: response.data.message
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to toggle notifications'
      };
    }
  }
};

export default settingsApi;
