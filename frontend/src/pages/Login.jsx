import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { Cloud, Eye, EyeOff, AlertCircle, Shield, Zap, XCircle } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import Toast from '../components/common/Toast';

const Login = () => {
  const { login, isAuthenticated, isLoading, error, clearError } = useAuth();
  const { isDark } = useTheme();

  const [formData, setFormData] = useState({
    aws_access_key: '',
    aws_secret_key: ''
  });

  const [showSecretKey, setShowSecretKey] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});
  const [toast, setToast] = useState(null);

  // Clear errors when component mounts
  useEffect(() => {
    clearError();
  }, [clearError]);

  // Show toast when auth error occurs
  useEffect(() => {
    if (error) {
      const { message, type } = getErrorMessage(error);
      showToast(message, type);
    }
  }, [error]);

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const showToast = (message, type = 'error') => {
    setToast({ message, type });
  };

  const hideToast = () => {
    setToast(null);
  };

  // Helper to get user-friendly error messages based on backend responses
  const getErrorMessage = (errorText) => {
    if (!errorText) {
      return {
        message: 'Authentication failed. Please check your credentials.',
        type: 'error'
      };
    }

    const lowerError = errorText.toLowerCase();

    // Backend: 401 - Invalid AWS credentials
    if (lowerError.includes('invalid aws credentials')) {
      return {
        message: '🔑 Invalid AWS credentials. Please verify your Access Key ID and Secret Access Key.',
        type: 'error'
      };
    }

    // Backend: 403 - Account suspended/inactive
    if (lowerError.includes('account is suspended')) {
      return {
        message: '⛔ Your account has been suspended. Please contact support.',
        type: 'error'
      };
    }

    if (lowerError.includes('account is inactive')) {
      return {
        message: ' Your account is inactive. Please contact support to reactivate.',
        type: 'warning'
      };
    }

    if (lowerError.includes('account is')) {
      return {
        message: ` ${errorText}. Please contact support.`,
        type: 'error'
      };
    }

    // Backend: 500 - Failed to create account
    if (lowerError.includes('failed to create account')) {
      return {
        message: ' Failed to create your account. Please try again later.',
        type: 'error'
      };
    }

    // Backend: 500 - Internal server error
    if (lowerError.includes('internal server error')) {
      return {
        message: '🔧 Server error. Our team has been notified. Please try again later.',
        type: 'error'
      };
    }

    // Backend: 401 - Invalid/expired refresh token
    if (lowerError.includes('invalid or expired refresh token')) {
      return {
        message: ' Your session has expired. Please log in again.',
        type: 'warning'
      };
    }

    // Backend: 401 - Client not found or inactive
    if (lowerError.includes('client not found')) {
      return {
        message: ' Account not found. Please check your credentials.',
        type: 'error'
      };
    }

    // Network/Connection errors
    if (lowerError.includes('network') || lowerError.includes('fetch') || lowerError.includes('connection')) {
      return {
        message: ' Network error. Please check your internet connection and try again.',
        type: 'error'
      };
    }

    if (lowerError.includes('timeout')) {
      return {
        message: '⏱ Connection timed out. Please try again.',
        type: 'warning'
      };
    }

    // AWS-specific errors
    if (lowerError.includes('expired')) {
      return {
        message: ' Your AWS credentials have expired. Please generate new keys in AWS Console.',
        type: 'error'
      };
    }

    if (lowerError.includes('permission') || lowerError.includes('denied') || lowerError.includes('accessdenied')) {
      return {
        message: ' Access denied. Your IAM user may lack required permissions.',
        type: 'error'
      };
    }

    if (lowerError.includes('throttl')) {
      return {
        message: '⚡ Too many requests. Please wait a moment and try again.',
        type: 'warning'
      };
    }

    // Default error
    return {
      message: ` ${errorText}`,
      type: 'error'
    };
  };

  const validateForm = () => {
    const errors = {};

    if (!formData.aws_access_key.trim()) {
      errors.aws_access_key = 'AWS Access Key is required';
    } else if (formData.aws_access_key.length < 16) {
      errors.aws_access_key = 'AWS Access Key must be at least 16 characters';
    }

    if (!formData.aws_secret_key.trim()) {
      errors.aws_secret_key = 'AWS Secret Key is required';
    } else if (formData.aws_secret_key.length < 32) {
      errors.aws_secret_key = 'AWS Secret Key must be at least 32 characters';
    }

    setValidationErrors(errors);

    // Show toast for validation errors
    if (Object.keys(errors).length > 0) {
      const errorCount = Object.keys(errors).length;
      showToast(
          ` Please fix ${errorCount} validation ${errorCount === 1 ? 'error' : 'errors'} before submitting`,
          'warning'
      );
    }

    return Object.keys(errors).length === 0;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear validation error for this field
    if (validationErrors[name]) {
      setValidationErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }

    // Clear auth error and toast
    if (error) {
      clearError();
    }
    if (toast) {
      hideToast();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    hideToast(); // Clear any existing toast

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const result = await login(formData);

      if (result.success) {
        showToast(
            result.is_new_account
                ? ' Welcome! Your account has been created successfully.'
                : ' Login successful! Redirecting to dashboard...',
            'success'
        );
      } else {
        // --- PHẦN BỔ SUNG QUAN TRỌNG ---
        // Xử lý khi API trả về success: false
        // Lấy thông báo lỗi từ result trả về
        const errorMsg = result.error || 'Login failed';

        // Format lỗi cho đẹp bằng helper có sẵn
        const { message, type } = getErrorMessage(errorMsg);

        // Hiển thị Toast thông báo lỗi
        showToast(message, type);
        // -------------------------------
      }

    } catch (err) {
      // Catch này chỉ chạy nếu có lỗi code (runtime error) hoặc lỗi mạng nghiêm trọng mà authApi không bắt được
      console.error('Login error:', err);
      showToast(' An unexpected error occurred. Please try again.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleSecretKeyVisibility = () => {
    setShowSecretKey(!showSecretKey);
  };

  if (isLoading) {
    return (
        <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
          <div className="hero absolute inset-0 -z-10"></div>

          <div className="text-center relative z-10 animate-fade-in">
            <div className="mb-8">
              <div className="bg-gradient-to-r from-blue-500 to-blue-600 p-6 rounded-2xl shadow-cosmic-glow mx-auto w-fit animate-float">
                <Cloud size={48} className="text-white" />
              </div>
            </div>
            <div className="relative mb-6">
              <div className="animate-spin rounded-full h-16 w-16 border-4 border-cosmic-border border-t-blue-500 mx-auto"></div>
              <div className="absolute inset-0 rounded-full border-4 border-blue-500/20 animate-pulse"></div>
            </div>
            <h2 className="text-2xl font-bold text-cosmic-txt-1 mb-2">AWS Cloud Health Dashboard</h2>
            <p className="text-cosmic-txt-2 animate-pulse">Initializing secure connection...</p>
          </div>
        </div>
    );
  }

  return (
      <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
        {/* Cosmic Hero Background */}
        <div className="hero absolute inset-0 -z-10"></div>

        {/* Toast Notification */}
        {toast && (
            <Toast
                message={toast.message}
                type={toast.type}
                onClose={hideToast}
            />
        )}

        <div className="max-w-md w-full space-y-8 relative z-10 animate-fade-in">
          {/* Cosmic Header */}
          <div className="text-center">
            <div className="flex justify-center mb-8">
              <div className="bg-gradient-to-r from-blue-500 to-blue-600 p-6 rounded-2xl shadow-cosmic-glow animate-float">
                <Cloud size={56} className="text-white" />
              </div>
            </div>
            <h1 className="text-4xl font-bold text-cosmic-txt-1 mb-3 tracking-tight">
              AWS Cloud Health Dashboard
            </h1>
            <p className="text-cosmic-txt-2 text-lg mb-6">
              Professional cloud infrastructure monitoring
            </p>
            <div className="flex justify-center items-center space-x-4 mb-8">
              <div className="badge flex items-center space-x-2 animate-fade-in" style={{animationDelay: '0.2s'}}>
                <Shield size={16} className="text-blue-400" />
                <span>Enterprise Security</span>
              </div>
              <div className="badge flex items-center space-x-2 animate-fade-in" style={{animationDelay: '0.4s'}}>
                <Zap size={16} className="text-blue-400" />
                <span>Real-time Monitoring</span>
              </div>
            </div>
          </div>

          {/* Cosmic Login Form */}
          <div className="card p-8 animate-slide-up">
            <div className="text-center mb-8">
              <h3 className="text-xl font-semibold text-cosmic-txt-1 mb-2">Welcome Back</h3>
              <p className="text-cosmic-txt-2">Enter your AWS credentials to continue</p>
            </div>
            <form className="space-y-6" onSubmit={handleSubmit}>
              {/* Inline Error Display */}
              {error && (
                  <div className="bg-red-900/20 border border-red-800/50 rounded-xl p-4 animate-scale-in backdrop-blur-sm">
                    <div className="flex items-start">
                      <div className="flex-shrink-0">
                        <XCircle className="h-5 w-5 text-red-400" />
                      </div>
                      <div className="ml-3 flex-1">
                        <h3 className="text-sm font-semibold text-red-300 mb-1">
                          Authentication Failed
                        </h3>
                        <p className="text-sm text-red-400 leading-relaxed">
                          {error}
                        </p>
                        {error.toLowerCase().includes('invalid aws credentials') && (
                            <div className="mt-3 text-xs text-red-300/80 space-y-1">
                              <p>💡 Common causes:</p>
                              <ul className="list-disc list-inside ml-2 space-y-0.5">
                                <li>Incorrect Access Key or Secret Key</li>
                                <li>Credentials have been rotated or revoked</li>
                                <li>Copy/paste included extra spaces</li>
                              </ul>
                            </div>
                        )}
                      </div>
                    </div>
                  </div>
              )}

              {/* AWS Access Key Input */}
              <div className="space-y-2">
                <label htmlFor="aws_access_key" className="block text-sm font-semibold text-cosmic-txt-1">
                <span className="flex items-center">
                  <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                  AWS Access Key ID
                </span>
                </label>
                <div className="relative group">
                  <input
                      id="aws_access_key"
                      name="aws_access_key"
                      type="text"
                      autoComplete="username"
                      required
                      value={formData.aws_access_key}
                      onChange={handleInputChange}
                      className={`appearance-none relative block w-full px-4 py-3 border ${
                          validationErrors.aws_access_key
                              ? 'border-red-600 bg-red-900/20'
                              : error
                                  ? 'border-red-600/50 bg-red-900/10'
                                  : 'border-cosmic-border bg-cosmic-card focus:border-blue-500'
                      } placeholder-cosmic-muted text-cosmic-txt-1 rounded-xl focus-ring backdrop-blur-sm transition-all duration-300 text-sm font-medium`}
                      placeholder="AKIAIOSFODNN7EXAMPLE"
                  />
                  {validationErrors.aws_access_key && (
                      <p className="mt-2 text-sm text-red-400 font-medium flex items-center">
                        <AlertCircle size={14} className="mr-1" />
                        {validationErrors.aws_access_key}
                      </p>
                  )}
                </div>
              </div>

              {/* AWS Secret Key Input */}
              <div className="space-y-2">
                <label htmlFor="aws_secret_key" className="block text-sm font-semibold text-cosmic-txt-1">
                <span className="flex items-center">
                  <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
                  AWS Secret Access Key
                </span>
                </label>
                <div className="relative group">
                  <input
                      id="aws_secret_key"
                      name="aws_secret_key"
                      type={showSecretKey ? 'text' : 'password'}
                      autoComplete="current-password"
                      required
                      value={formData.aws_secret_key}
                      onChange={handleInputChange}
                      className={`appearance-none relative block w-full px-4 py-3 pr-12 border ${
                          validationErrors.aws_secret_key
                              ? 'border-red-600 bg-red-900/20'
                              : error
                                  ? 'border-red-600/50 bg-red-900/10'
                                  : 'border-cosmic-border bg-cosmic-card focus:border-blue-500'
                      } placeholder-cosmic-muted text-cosmic-txt-1 rounded-xl focus-ring backdrop-blur-sm transition-all duration-300 text-sm font-medium`}
                      placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                  />
                  <button
                      type="button"
                      className="absolute inset-y-0 right-0 pr-3 flex items-center hover:bg-cosmic-bg-2 rounded-r-xl transition-all duration-200"
                      onClick={toggleSecretKeyVisibility}
                  >
                    {showSecretKey ? (
                        <EyeOff className="h-5 w-5 text-cosmic-muted hover:text-blue-400 transition-colors" />
                    ) : (
                        <Eye className="h-5 w-5 text-cosmic-muted hover:text-blue-400 transition-colors" />
                    )}
                  </button>
                  {validationErrors.aws_secret_key && (
                      <p className="mt-2 text-sm text-red-400 font-medium flex items-center">
                        <AlertCircle size={14} className="mr-1" />
                        {validationErrors.aws_secret_key}
                      </p>
                  )}
                </div>
              </div>

              {/* Cosmic Security Notice */}
              <div className="bg-blue-900/20 border border-blue-800/50 rounded-xl p-4 backdrop-blur-sm">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex items-center justify-center shadow-cosmic-glow">
                      <Shield size={16} className="text-white" />
                    </div>
                  </div>
                  <div className="text-sm">
                    <p className="font-semibold mb-2 text-blue-100">Security Notice</p>
                    <p className="text-blue-200 leading-relaxed">Your AWS credentials are encrypted and stored securely. We recommend using IAM users with limited permissions for monitoring purposes.</p>
                  </div>
                </div>
              </div>

              {/* Cosmic Submit Button */}
              <div className="pt-4">
                <button
                    type="submit"
                    disabled={isSubmitting}
                    className={`btn btn-primary w-full py-3 px-6 text-base font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 ${
                        error ? 'animate-pulse-once' : ''
                    }`}
                >
                  <div className="relative flex items-center justify-center">
                    {isSubmitting && (
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                    )}
                    {isSubmitting ? 'Verifying Credentials...' : 'Sign In to Dashboard'}
                  </div>
                </button>
              </div>
            </form>
          </div>

          {/* Cosmic Footer */}
          <div className="text-center">
            <div className="inline-flex items-center space-x-2 text-sm text-cosmic-txt-2 bg-cosmic-card px-6 py-3 rounded-full border border-cosmic-border backdrop-blur-sm">
              <span>Need help?</span>
            <a
              href="https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 transition-colors font-medium underline decoration-blue-400/50 hover:decoration-blue-400"
              >
              AWS IAM documentation
            </a>
          </div>
        </div>
      </div>
</div>
);
};

export default Login;