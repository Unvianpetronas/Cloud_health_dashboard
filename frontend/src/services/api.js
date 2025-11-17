import axios from 'axios';
import logger from '../utils/logger';

//const API_BASE_URL =   'http://localhost:8000/api/v1';  # To host local please command bellow code
const API_BASE_URL = process.env.REACT_APP_BASE_URL || 'http://localhost:8000/api/v1' ;

logger.info('API Base URL:', API_BASE_URL);

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000, // 30 seconds - sufficient since worker now starts in background
});

// Request interceptor
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers = config.headers || {};
            config.headers.Authorization = `Bearer ${token}`;
        }
        logger.api(config.method, config.url);
        return config;
    },
    (error) => {
        logger.error('Request Error:', error);
        return Promise.reject(error);
    }
);

// Response interceptor
apiClient.interceptors.response.use(
    (response) => {
        logger.api(response.config.method, response.config.url, response.status);
        return response;
    },
    async (error) => {
        logger.error('API Error:', {
            status: error.response?.status,
            url: error.config?.url,
            message: error.message,
            data: error.response?.data
        });

        if (error.response?.status === 401) {
            logger.warn('Unauthorized - clearing tokens and redirecting to login');
            
            // Try to refresh token first
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken && !error.config._retry) {
                error.config._retry = true;
                
                try {
                    const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                        refresh_token: refreshToken
                    });
                    
                    if (response.data.access_token) {
                        localStorage.setItem('access_token', response.data.access_token);
                        localStorage.setItem('refresh_token', response.data.refresh_token);
                        
                        // Retry the original request with new token
                        error.config.headers['Authorization'] = `Bearer ${response.data.access_token}`;
                        return apiClient(error.config);
                    }
                } catch (refreshError) {
                    logger.error('Token refresh failed:', refreshError);
                    // Clear tokens and redirect to login
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    localStorage.removeItem('user');
                    window.location.href = '/login';
                }
            } else {
                // No refresh token or retry already attempted
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user');
                window.location.href = '/login';
            }
        }

        return Promise.reject(error);
    }
);

export default apiClient;
