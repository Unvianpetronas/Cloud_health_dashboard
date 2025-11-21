import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Save, User, Bell, Shield, Palette, Mail, CheckCircle, XCircle, AlertCircle, Send } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/common/Header';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import {
  sendVerificationEmail,
  resendVerificationEmail,
  getVerificationStatus,
  updateEmail,
  getNotificationPreferences,
  updateNotificationPreferences,
  getUserProfile
} from '../services/emailApi';

const Settings = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [emailError, setEmailError] = useState('');
  const [emailSuccess, setEmailSuccess] = useState('');
  const [verificationStatus, setVerificationStatus] = useState({
    email: '',
    emailVerified: false,
    awsAccountId: ''
  });

  const [emailData, setEmailData] = useState({
    currentEmail: '',
    newEmail: '',
    isEditing: false
  });

  const [settings, setSettings] = useState({
    notifications: {
      email: true,
      push: false,
      critical: true,
      warning: true,
      info: false,
      critical_alerts: true,
      warning_alerts: false,
      cost_alerts: true,
      daily_summary: false
    },
    dashboard: {
      autoRefresh: true,
      refreshInterval: 300,
      theme: 'light',
      defaultTimeRange: '24h'
    },
    security: {
      sessionTimeout: 3600,
      requireReauth: false
    }
  });

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      setLoading(true);

      // Load verification status
      const status = await getVerificationStatus();
      setVerificationStatus({
        email: status.email || '',
        emailVerified: status.email_verified || false,
        awsAccountId: status.aws_account_id || ''
      });

      setEmailData(prev => ({
        ...prev,
        currentEmail: status.email || '',
        newEmail: status.email || ''
      }));

      // Load notification preferences
      try {
        const prefs = await getNotificationPreferences();
        if (prefs.success) {
          setSettings(prev => ({
            ...prev,
            notifications: {
              ...prev.notifications,
              ...prefs.preferences
            }
          }));
        }
      } catch (error) {
        console.error('Error loading notification preferences:', error);
      }

    } catch (error) {
      console.error('Error loading user data:', error);
      setEmailError('Failed to load user data');
    } finally {
      setLoading(false);
    }
  };

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleEmailUpdate = async () => {
    setEmailError('');
    setEmailSuccess('');

    if (!validateEmail(emailData.newEmail)) {
      setEmailError('Please enter a valid email address');
      return;
    }

    if (emailData.newEmail === emailData.currentEmail) {
      setEmailError('New email must be different from current email');
      return;
    }

    try {
      setSaving(true);
      const result = await updateEmail(emailData.newEmail);

      if (result.success) {
        setEmailSuccess('Email updated successfully! A verification email has been sent.');
        setEmailData(prev => ({
          ...prev,
          currentEmail: emailData.newEmail,
          isEditing: false
        }));
        setVerificationStatus(prev => ({
          ...prev,
          email: emailData.newEmail,
          emailVerified: false
        }));
      }
    } catch (error) {
      setEmailError(error.response?.data?.detail || 'Failed to update email');
    } finally {
      setSaving(false);
    }
  };

  const handleSendVerification = async () => {
    setEmailError('');
    setEmailSuccess('');

    if (!verificationStatus.email) {
      setEmailError('No email address found');
      return;
    }

    try {
      setSaving(true);
      const result = await sendVerificationEmail(verificationStatus.awsAccountId);

      if (result.success) {
        if (result.already_verified) {
          setEmailSuccess('Email is already verified!');
        } else {
          setEmailSuccess(`Verification email sent to ${result.email}`);
        }
      }
    } catch (error) {
      setEmailError(error.response?.data?.detail || 'Failed to send verification email');
    } finally {
      setSaving(false);
    }
  };

  const handleResendVerification = async () => {
    setEmailError('');
    setEmailSuccess('');

    try {
      setSaving(true);
      const result = await resendVerificationEmail(verificationStatus.awsAccountId);

      if (result.success) {
        setEmailSuccess('Verification email resent!');
      }
    } catch (error) {
      setEmailError(error.response?.data?.detail || 'Failed to resend verification email');
    } finally {
      setSaving(false);
    }
  };

  const handleSettingChange = (category, key, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
  };

  const handleSaveNotifications = async () => {
    setEmailError('');
    setEmailSuccess('');

    try {
      setSaving(true);
      const result = await updateNotificationPreferences(settings.notifications);

      if (result.success) {
        setEmailSuccess('Notification preferences updated successfully!');
      }
    } catch (error) {
      setEmailError(error.response?.data?.detail || 'Failed to update notification preferences');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header title="Settings" showNavigation={true} />
        <main className="p-6 max-w-4xl mx-auto">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading settings...</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header title="Settings" showNavigation={true} />

      <main className="p-6 max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Settings</h1>
          <p className="text-gray-600">Manage your dashboard preferences and account settings</p>
        </div>

        {/* Success/Error Messages */}
        {emailSuccess && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2 text-green-800">
            <CheckCircle size={20} />
            <span>{emailSuccess}</span>
          </div>
        )}

        {emailError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-800">
            <XCircle size={20} />
            <span>{emailError}</span>
          </div>
        )}

        <div className="space-y-6">
          {/* Email Settings */}
          <Card>
            <div className="flex items-center mb-4">
              <Mail className="h-5 w-5 text-gray-500 mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">Email Settings</h2>
            </div>

            <div className="space-y-4">
              {/* Email Address */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>

                {!emailData.isEditing ? (
                  <div className="flex items-center justify-between bg-gray-50 p-3 rounded-md border border-gray-200">
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-gray-900">{emailData.currentEmail || 'No email set'}</span>
                      {verificationStatus.emailVerified ? (
                        <span className="flex items-center gap-1 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                          <CheckCircle size={14} />
                          Verified
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">
                          <AlertCircle size={14} />
                          Not Verified
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => setEmailData(prev => ({ ...prev, isEditing: true }))}
                      className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                    >
                      Change Email
                    </button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <input
                      type="email"
                      value={emailData.newEmail}
                      onChange={(e) => setEmailData(prev => ({ ...prev, newEmail: e.target.value }))}
                      placeholder="Enter new email address"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <div className="flex gap-2">
                      <Button
                        onClick={handleEmailUpdate}
                        loading={saving}
                        variant="primary"
                        size="sm"
                      >
                        Update Email
                      </Button>
                      <Button
                        onClick={() => {
                          setEmailData(prev => ({
                            ...prev,
                            newEmail: prev.currentEmail,
                            isEditing: false
                          }));
                          setEmailError('');
                        }}
                        variant="secondary"
                        size="sm"
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}
              </div>

              {/* Email Verification */}
              {emailData.currentEmail && !emailData.isEditing && (
                <div className="border-t border-gray-200 pt-4">
                  {!verificationStatus.emailVerified ? (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <AlertCircle className="text-yellow-600 mt-0.5" size={20} />
                        <div className="flex-1">
                          <h3 className="text-sm font-semibold text-yellow-900 mb-1">
                            Email Verification Required
                          </h3>
                          <p className="text-sm text-yellow-800 mb-3">
                            Please verify your email to enable notifications and alerts.
                          </p>
                          <div className="flex gap-2">
                            <Button
                              onClick={handleSendVerification}
                              loading={saving}
                              variant="primary"
                              size="sm"
                              className="bg-yellow-600 hover:bg-yellow-700"
                            >
                              <Send size={14} className="mr-1" />
                              Send Verification Email
                            </Button>
                            <Button
                              onClick={handleResendVerification}
                              loading={saving}
                              variant="secondary"
                              size="sm"
                            >
                              Resend
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
                      <CheckCircle className="text-green-600" size={20} />
                      <div>
                        <h3 className="text-sm font-semibold text-green-900">Email Verified</h3>
                        <p className="text-sm text-green-700">Your email is verified and ready to receive notifications.</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </Card>

          {/* Account Information */}
          <Card>
            <div className="flex items-center mb-4">
              <User className="h-5 w-5 text-gray-500 mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">Account Information</h2>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  AWS Account ID
                </label>
                <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
                  {verificationStatus.awsAccountId || 'Not available'}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Last Login
                </label>
                <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
                  {user?.loginTime ? new Date(user.loginTime).toLocaleString() : 'Not available'}
                </div>
              </div>
            </div>
          </Card>

          {/* Notification Settings */}
          <Card>
            <div className="flex items-center mb-4">
              <Bell className="h-5 w-5 text-gray-500 mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">Notifications</h2>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Email Notifications</label>
                  <p className="text-sm text-gray-500">Receive alerts via email</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.notifications.email}
                  onChange={(e) => handleSettingChange('notifications', 'email', e.target.checked)}
                  disabled={!verificationStatus.emailVerified}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Critical Alerts</label>
                  <p className="text-sm text-gray-500">Always notify for critical issues</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.notifications.critical_alerts}
                  onChange={(e) => handleSettingChange('notifications', 'critical_alerts', e.target.checked)}
                  disabled={!verificationStatus.emailVerified}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Warning Alerts</label>
                  <p className="text-sm text-gray-500">Notify for warning level issues</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.notifications.warning_alerts}
                  onChange={(e) => handleSettingChange('notifications', 'warning_alerts', e.target.checked)}
                  disabled={!verificationStatus.emailVerified}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Cost Alerts</label>
                  <p className="text-sm text-gray-500">Get notified about cost anomalies</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.notifications.cost_alerts}
                  onChange={(e) => handleSettingChange('notifications', 'cost_alerts', e.target.checked)}
                  disabled={!verificationStatus.emailVerified}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Daily Summary</label>
                  <p className="text-sm text-gray-500">Receive daily security summary reports</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.notifications.daily_summary}
                  onChange={(e) => handleSettingChange('notifications', 'daily_summary', e.target.checked)}
                  disabled={!verificationStatus.emailVerified}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              {!verificationStatus.emailVerified && (
                <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800 flex items-center gap-2">
                    <AlertCircle size={16} />
                    Please verify your email to enable notification settings
                  </p>
                </div>
              )}
            </div>

            {/* Save Button for Notifications */}
            <div className="mt-6 pt-4 border-t border-gray-200">
              <Button
                onClick={handleSaveNotifications}
                loading={saving}
                variant="primary"
                size="md"
                disabled={!verificationStatus.emailVerified}
                className="flex items-center space-x-2"
              >
                <Save size={16} />
                <span>Save Notification Preferences</span>
              </Button>
            </div>
          </Card>

          {/* Dashboard Settings */}
          <Card>
            <div className="flex items-center mb-4">
              <Palette className="h-5 w-5 text-gray-500 mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">Dashboard</h2>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Auto Refresh</label>
                  <p className="text-sm text-gray-500">Automatically refresh dashboard data</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.dashboard.autoRefresh}
                  onChange={(e) => handleSettingChange('dashboard', 'autoRefresh', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Refresh Interval (seconds)
                </label>
                <select
                  value={settings.dashboard.refreshInterval}
                  onChange={(e) => handleSettingChange('dashboard', 'refreshInterval', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={60}>1 minute</option>
                  <option value={300}>5 minutes</option>
                  <option value={600}>10 minutes</option>
                  <option value={1800}>30 minutes</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Default Time Range
                </label>
                <select
                  value={settings.dashboard.defaultTimeRange}
                  onChange={(e) => handleSettingChange('dashboard', 'defaultTimeRange', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="1h">Last Hour</option>
                  <option value="24h">Last 24 Hours</option>
                  <option value="7d">Last 7 Days</option>
                  <option value="30d">Last 30 Days</option>
                </select>
              </div>
            </div>
          </Card>

          {/* Security Settings */}
          <Card>
            <div className="flex items-center mb-4">
              <Shield className="h-5 w-5 text-gray-500 mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">Security</h2>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Session Timeout (seconds)
                </label>
                <select
                  value={settings.security.sessionTimeout}
                  onChange={(e) => handleSettingChange('security', 'sessionTimeout', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={1800}>30 minutes</option>
                  <option value={3600}>1 hour</option>
                  <option value={7200}>2 hours</option>
                  <option value={14400}>4 hours</option>
                </select>
              </div>
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Settings;
