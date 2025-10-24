import React, { createContext, useContext, useState, useEffect } from 'react';
import authApi from '../services/authApi';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [error, setError] = useState(null);

  // Check if user is already logged in on app start
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');

    if (token && userData) {
      try {
        setUser(JSON.parse(userData));
        setIsAuthenticated(true);
      } catch (e) {
        console.error('Failed to parse user data:', e);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
      }
    }
  }, []);

  const login = async (credentials) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await authApi.login(credentials);

      if (result.success) {
        // ✅ Extract all data from backend response
        const {
          access_token,
          refresh_token,
          token_type,
          expires_in,
          aws_account_id,
          is_new_account,
          email,
          company_name
        } = result.data;

        // ✅ Store JWT token
        localStorage.setItem('access_token', access_token);

        // ✅ Store refresh token (for token refresh later)
        if (refresh_token) {
          localStorage.setItem('refresh_token', refresh_token);
        }

        // ✅ Create user data object with backend response
        const userData = {
          awsAccountId: aws_account_id,
          email: email || null,
          companyName: company_name,
          isNewAccount: is_new_account,
          loginTime: new Date().toISOString(),
          expiresIn: expires_in,
        };

        localStorage.setItem('user', JSON.stringify(userData));
        setUser(userData);
        setIsAuthenticated(true);

        console.log('✅ Login successful:', {
          awsAccountId: aws_account_id,
          email: email,
          companyName: company_name
        });

        return { success: true, data: userData };
      } else {
        setError(result.error);
        return { success: false, error: result.error };
      }
    } catch (error) {
      console.error('Login error:', error);
      const errorMessage = 'Network error. Please check your connection.';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
    setIsAuthenticated(false);
    setError(null);
  };

  const clearError = () => {
    setError(null);
  };

  const value = {
    user,
    isLoading,
    isAuthenticated,
    error,
    login,
    logout,
    clearError,
  };

  return (
      <AuthContext.Provider value={value}>
        {children}
      </AuthContext.Provider>
  );
};

export default AuthContext;