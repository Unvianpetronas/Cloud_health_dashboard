import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';
export const ec2Api = {
    // Scan all EC2 instances across regions
    scanAllRegions: async () => {
        try {
            const response = await axios.get('/ec2/scan-all-regions');
            return {
                success: true,
                data: response.data
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || 'Failed to scan EC2 instances'
            };
        }
    },

    // Get running instances
    getRunningInstances: async () => {
        try {
            const response = await axios.get('/ec2/running-instances');
            return {
                success: true,
                data: response.data
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || 'Failed to get running instances'
            };
        }
    },

    // Get cost estimate
    getCostEstimate: async () => {
        try {
            const response = await axios.get('/ec2/cost-estimate');
            return {
                success: true,
                data: response.data
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || 'Failed to get cost estimate'
            };
        }
    },

    // ADD THIS - Get instance summary
    getInstanceSummary: async () => {
        try {
            const response = await axios.get('/ec2/summary');
            return {
                success: true,
                data: response.data
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || 'Failed to get instance summary'
            };
        }
    }
};