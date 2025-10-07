import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const authApi = {
    login: async (credentials) => {
        try {
            const response = await axios.post(`${API_BASE_URL}/auth/login`, {
                access_key: credentials.access_key,
                secret_key: credentials.secret_key,
            });

            return {
                success: true,
                data: response.data,
            };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || 'Login failed',
            };
        }
    },
};

export default authApi;