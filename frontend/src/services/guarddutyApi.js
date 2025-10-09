import apiClient from "./api";

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const guarddutyApi = {
    getStatus : async() => {
        try {
            const response = await apiClient.get('/guardduty/status')
            return {
                success: true,
                data: response.data
            };
        }catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || 'Failed to scan EC2 instances'
            };
        }
    },

    getFindings : async() => {
        try{
            const  response  = await apiClient.get('/guardduty/findings')
            return{
                success : true,
                data : response.data
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || 'Failed to scan EC2 instances'
            };
        }
    },

    getCritical : async() => {
        try{
            const response  = await apiClient.get('/guardduty/critical')
            return{
                success : true,
                data : response.data
            }
        }catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || 'Failed to scan EC2 instances'
            };
        }
    },

    getSumary : async() =>{
        try{
            const response = await  apiClient.get('/guardduty/summary')
            return{
                success : true,
                data : response.data
            }
        }catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || 'Failed to scan EC2 instances'
            };
        }
    }
};