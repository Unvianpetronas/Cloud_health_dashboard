import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CheckCircle, XCircle, Loader } from 'lucide-react';
import Button from '../components/common/Button';
import { verifyEmailToken } from '../services/emailApi';

const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('verifying'); // 'verifying', 'success', 'error'
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');

    if (!token) {
      setStatus('error');
      setMessage('Invalid verification link. No token provided.');
      return;
    }

    verifyEmail(token);
  }, [searchParams]);

  const verifyEmail = async (token) => {
    try {
      const result = await verifyEmailToken(token);

      if (result.success) {
        setStatus('success');
        setMessage(result.message || 'Email verified successfully!');
      } else {
        setStatus('error');
        setMessage(result.message || 'Verification failed. Please try again.');
      }
    } catch (error) {
      setStatus('error');
      setMessage(
        error.response?.data?.detail ||
        'Verification failed. The link may have expired or is invalid.'
      );
    }
  };

  const handleGoToSettings = () => {
    navigate('/settings');
  };

  const handleGoToDashboard = () => {
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 flex items-center justify-center p-6">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
                <span className="text-3xl">✉️</span>
              </div>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Email Verification
            </h1>
            <p className="text-gray-600 text-sm">
              AWS Cloud Health Dashboard
            </p>
          </div>

          {/* Content */}
          <div className="space-y-6">
            {/* Verifying State */}
            {status === 'verifying' && (
              <div className="text-center py-8">
                <div className="flex justify-center mb-4">
                  <Loader className="animate-spin text-blue-600" size={48} />
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Verifying your email...
                </h2>
                <p className="text-gray-600">
                  Please wait while we verify your email address.
                </p>
              </div>
            )}

            {/* Success State */}
            {status === 'success' && (
              <div className="text-center py-6">
                <div className="flex justify-center mb-4">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                    <CheckCircle className="text-green-600" size={32} />
                  </div>
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-3">
                  Email Verified!
                </h2>
                <p className="text-gray-600 mb-6">
                  {message}
                </p>

                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                  <p className="text-sm text-green-800">
                    ✅ Your email is now verified and you can receive notifications and alerts.
                  </p>
                </div>

                <div className="space-y-3">
                  <Button
                    onClick={handleGoToSettings}
                    variant="primary"
                    size="lg"
                    className="w-full"
                  >
                    Go to Settings
                  </Button>
                  <Button
                    onClick={handleGoToDashboard}
                    variant="secondary"
                    size="lg"
                    className="w-full"
                  >
                    Go to Dashboard
                  </Button>
                </div>
              </div>
            )}

            {/* Error State */}
            {status === 'error' && (
              <div className="text-center py-6">
                <div className="flex justify-center mb-4">
                  <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                    <XCircle className="text-red-600" size={32} />
                  </div>
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-3">
                  Verification Failed
                </h2>
                <p className="text-gray-600 mb-6">
                  {message}
                </p>

                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                  <p className="text-sm text-red-800 mb-2">
                    ❌ Unable to verify your email address.
                  </p>
                  <p className="text-xs text-red-700">
                    The verification link may have expired (links expire after 24 hours) or may have already been used.
                  </p>
                </div>

                <div className="space-y-3">
                  <Button
                    onClick={handleGoToSettings}
                    variant="primary"
                    size="lg"
                    className="w-full"
                  >
                    Go to Settings to Resend
                  </Button>
                  <Button
                    onClick={handleGoToDashboard}
                    variant="secondary"
                    size="lg"
                    className="w-full"
                  >
                    Go to Dashboard
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="mt-8 pt-6 border-t border-gray-200 text-center">
            <p className="text-xs text-gray-500">
              If you didn't request this verification, you can safely ignore this page.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VerifyEmail;
