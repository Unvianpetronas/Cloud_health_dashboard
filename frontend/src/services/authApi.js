import apiClient from './api';

const authApi = {
    login: async (credentials) => {
        try {
            // Don't use auth token for login
            const response = await apiClient.post('/auth/login', {
                access_key: credentials.access_key,
                secret_key: credentials.secret_key,
            }, {
                // Skip auth interceptor for login
                headers: {
                    'Authorization': undefined
                }
            });

            return {
                success: true,
                data: response.data,
            };
        } catch (error) {
            console.error('Login error:', error);
            return {
                success: false,
                error: error.response?.data?.detail || error.message || 'Login failed',
            };
        }
    },
};

export default authApi;