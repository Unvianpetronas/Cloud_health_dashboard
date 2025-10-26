import apiClient from "./api";

export const guarddutyApi = {
    getStatus: async () => {
        try {
            const response = await apiClient.get('/guardduty/status');
            return {
                success: true,
                data: response.data
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || 'Failed to get GuardDuty status'
            };
        }
    },


    getFindings: async () => {
        try {
            const response = await apiClient.get('/guardduty/findings');
            return {
                success: true,
                data: response.data
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || 'Failed to get GuardDuty findings'
            };
        }
    },


    getCritical: async () => {
        try {
            const response = await apiClient.get('/guardduty/critical');
            return {
                success: true,
                data: response.data
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || 'Failed to get critical findings'
            };
        }
    },

    getSummary: async () => {
        try {
            const response = await apiClient.get('/guardduty/summary');
            return {
                success: true,
                data: response.data
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || 'Failed to get GuardDuty summary'
            };
        }
    }
};