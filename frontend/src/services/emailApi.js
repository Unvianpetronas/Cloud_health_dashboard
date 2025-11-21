import apiClient from './api';

/**
 * Email API Service
 * Handles email verification and notification settings
 */

/**
 * Send email verification link
 * @param {string} awsAccountId - AWS Account ID
 * @returns {Promise} API response
 */
export const sendVerificationEmail = async (awsAccountId) => {
    try {
        const response = await apiClient.post('/email/send-verification', {
            aws_account_id: awsAccountId
        });
        return response.data;
    } catch (error) {
        console.error('Error sending verification email:', error);
        throw error;
    }
};

/**
 * Resend email verification link
 * @param {string} awsAccountId - AWS Account ID
 * @returns {Promise} API response
 */
export const resendVerificationEmail = async (awsAccountId) => {
    try {
        const response = await apiClient.post('/email/resend-verification', {
            aws_account_id: awsAccountId
        });
        return response.data;
    } catch (error) {
        console.error('Error resending verification email:', error);
        throw error;
    }
};

/**
 * Get email verification status
 * @returns {Promise} Verification status
 */
export const getVerificationStatus = async () => {
    try {
        const response = await apiClient.get('/email/verification-status');
        return response.data;
    } catch (error) {
        console.error('Error getting verification status:', error);
        throw error;
    }
};

/**
 * Verify email with token (from email link)
 * @param {string} token - Verification token
 * @returns {Promise} Verification result
 */
export const verifyEmailToken = async (token) => {
    try {
        const response = await apiClient.get(`/email/verify?token=${token}`);
        return response.data;
    } catch (error) {
        console.error('Error verifying email token:', error);
        throw error;
    }
};

/**
 * Update user email address
 * @param {string} email - New email address
 * @returns {Promise} API response
 */
export const updateEmail = async (email) => {
    try {
        const response = await apiClient.put('/settings/email', { email });
        return response.data;
    } catch (error) {
        console.error('Error updating email:', error);
        throw error;
    }
};

/**
 * Get notification preferences
 * @returns {Promise} Notification preferences
 */
export const getNotificationPreferences = async () => {
    try {
        const response = await apiClient.get('/settings/notifications');
        return response.data;
    } catch (error) {
        console.error('Error getting notification preferences:', error);
        throw error;
    }
};

/**
 * Update notification preferences
 * @param {Object} preferences - Notification preferences
 * @returns {Promise} API response
 */
export const updateNotificationPreferences = async (preferences) => {
    try {
        const response = await apiClient.put('/settings/notifications', preferences);
        return response.data;
    } catch (error) {
        console.error('Error updating notification preferences:', error);
        throw error;
    }
};

/**
 * Get user profile
 * @returns {Promise} User profile data
 */
export const getUserProfile = async () => {
    try {
        const response = await apiClient.get('/settings/profile');
        return response.data;
    } catch (error) {
        console.error('Error getting user profile:', error);
        throw error;
    }
};
