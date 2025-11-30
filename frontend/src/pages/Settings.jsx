import React, { useState, useEffect } from 'react';
import { User, Bell, Palette, Mail, CheckCircle, AlertCircle, Send, Edit2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/common/Header';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Toast from '../components/common/Toast';
import { settingsApi } from '../services/settingsApi';
import logger from '../utils/logger';

// LocalStorage keys
const STORAGE_KEYS = {
  AUTO_REFRESH: 'dashboard_autoRefresh',
  REFRESH_INTERVAL: 'dashboard_refreshInterval',
  DEFAULT_TIME_RANGE: 'dashboard_defaultTimeRange'
};

const Settings = () => {
  const { user } = useAuth();

  // Dashboard settings (frontend-only, stored in localStorage)
  const [dashboardSettings, setDashboardSettings] = useState({
    autoRefresh: true,
    refreshInterval: 300, // seconds (5 minutes default)
    defaultTimeRange: '24h'
  });

  const [emailData, setEmailData] = useState({
    email: '',
    emailVerified: false,
    notificationsEnabled: false
  });

  const [isEditingEmail, setIsEditingEmail] = useState(false);
  const [newEmail, setNewEmail] = useState('');

  const [loading, setLoading] = useState(true);
  const [sendingEmail, setSendingEmail] = useState(false);
  const [updatingEmail, setUpdatingEmail] = useState(false);
  const [togglingNotification, setTogglingNotification] = useState(false);
  const [toast, setToast] = useState(null);

  // Load settings from localStorage and email status on mount
  useEffect(() => {
    loadDashboardSettings();
    loadEmailStatus();
  }, []);

  // Load dashboard settings from localStorage
  const loadDashboardSettings = () => {
    const autoRefresh = localStorage.getItem(STORAGE_KEYS.AUTO_REFRESH);
    const refreshInterval = localStorage.getItem(STORAGE_KEYS.REFRESH_INTERVAL);
    const defaultTimeRange = localStorage.getItem(STORAGE_KEYS.DEFAULT_TIME_RANGE);

    setDashboardSettings({
      autoRefresh: autoRefresh !== null ? autoRefresh === 'true' : true,
      refreshInterval: refreshInterval !== null ? parseInt(refreshInterval) : 300,
      defaultTimeRange: defaultTimeRange || '24h'
    });

    logger.info('Dashboard settings loaded from localStorage');
  };

  // Save a dashboard setting to localStorage
  const handleDashboardSettingChange = (key, value) => {
    setDashboardSettings(prev => ({
      ...prev,
      [key]: value
    }));

    // Save to localStorage immediately
    switch (key) {
      case 'autoRefresh':
        localStorage.setItem(STORAGE_KEYS.AUTO_REFRESH, value.toString());
        break;
      case 'refreshInterval':
        localStorage.setItem(STORAGE_KEYS.REFRESH_INTERVAL, value.toString());
        break;
      case 'defaultTimeRange':
        localStorage.setItem(STORAGE_KEYS.DEFAULT_TIME_RANGE, value);
        break;
      default:
        break;
    }

    showToast('Setting saved!', 'success');
    logger.info(`Dashboard setting updated: ${key} = ${value}`);
  };

  const loadEmailStatus = async () => {
    setLoading(true);
    const result = await settingsApi.getVerificationStatus();

    if (result.success) {
      setEmailData({
        email: result.data.email || '',
        emailVerified: result.data.email_verified || false,
        notificationsEnabled: result.data.notification_preferences || false
      });
      setNewEmail(result.data.email || '');
      logger.info('Email status loaded');
    } else {
      logger.error('Failed to load email status:', result.error);
    }

    setLoading(false);
  };

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
  };

  const hideToast = () => {
    setToast(null);
  };

  const handleSendVerificationEmail = async () => {
    setSendingEmail(true);

    const result = await settingsApi.sendVerificationEmail(user?.awsAccountId);

    if (result.success) {
      if (result.data.already_verified) {
        showToast('Email is already verified!', 'info');
      } else {
        showToast(result.message || 'Verification email sent! Please check your inbox.', 'success');
      }
      await loadEmailStatus();
    } else {
      showToast(result.error, 'error');
    }

    setSendingEmail(false);
  };

  const handleUpdateEmail = async () => {
    if (!newEmail || !newEmail.includes('@')) {
      showToast('Please enter a valid email address', 'error');
      return;
    }

    setUpdatingEmail(true);

    const result = await settingsApi.updateEmail(newEmail);

    if (result.success) {
      showToast('Email updated successfully! Please verify your new email.', 'success');
      setIsEditingEmail(false);
      await loadEmailStatus();

      setTimeout(() => {
        handleSendVerificationEmail();
      }, 1000);
    } else {
      showToast(result.error, 'error');
    }

    setUpdatingEmail(false);
  };

  const handleToggleNotifications = async (enabled) => {
    if (!emailData.emailVerified) {
      showToast('Please verify your email before enabling notifications', 'warning');
      return;
    }

    setTogglingNotification(true);

    const previousState = emailData.notificationsEnabled;
    setEmailData(prev => ({
      ...prev,
      notificationsEnabled: enabled
    }));

    const result = await settingsApi.toggleNotifications(enabled);

    if (result.success) {
      showToast(`Email notifications ${enabled ? 'enabled' : 'disabled'} successfully`, 'success');
    } else {
      setEmailData(prev => ({
        ...prev,
        notificationsEnabled: previousState
      }));
      showToast(result.error, 'error');
    }

    setTogglingNotification(false);
  };

  if (loading) {
    return (
        <div className="min-h-screen bg-cosmic-bg-0">
          <Header title="Settings" showNavigation={true} />
          <main className="p-6 max-w-4xl mx-auto">
            <div className="flex items-center justify-center h-96">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
            </div>
          </main>
        </div>
    );
  }

  return (
      <div className="min-h-screen bg-cosmic-bg-0">
        <Header title="Settings" showNavigation={true} />

        <main className="p-6 max-w-4xl mx-auto">
          <div className="mb-8 animate-fade-in">
            <h1 className="text-3xl font-bold text-cosmic-txt-1 mb-2">Settings</h1>
            <p className="text-cosmic-txt-2">Manage your dashboard preferences and account settings</p>
          </div>

          {toast && (
              <Toast
                  message={toast.message}
                  type={toast.type}
                  onClose={hideToast}
              />
          )}

          <div className="space-y-6">
            {/* Account Information */}
            <Card className="animate-fade-in">
              <div className="flex items-center mb-6">
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center mr-3 shadow-cosmic-glow">
                  <User className="h-5 w-5 text-white" />
                </div>
                <h2 className="text-xl font-semibold text-cosmic-txt-1">Account Information</h2>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-cosmic-txt-1 mb-2">
                    AWS Account ID
                  </label>
                  <div className="text-sm text-cosmic-txt-2 bg-cosmic-bg-2 p-4 rounded-xl border border-cosmic-border">
                    {user?.awsAccountId || 'Not available'}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-cosmic-txt-1 mb-2">
                    Company Name
                  </label>
                  <div className="text-sm text-cosmic-txt-2 bg-cosmic-bg-2 p-4 rounded-xl border border-cosmic-border">
                    {user?.companyName || 'Not available'}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-cosmic-txt-1 mb-2">
                    Last Login
                  </label>
                  <div className="text-sm text-cosmic-txt-2 bg-cosmic-bg-2 p-4 rounded-xl border border-cosmic-border">
                    {user?.loginTime ? new Date(user.loginTime).toLocaleString() : 'Not available'}
                  </div>
                </div>
              </div>
            </Card>

            {/* Email Management Section */}
            <Card className="animate-fade-in" style={{animationDelay: '0.1s'}}>
              <div className="flex items-center mb-6">
                <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-green-600 rounded-xl flex items-center justify-center mr-3 shadow-cosmic-glow">
                  <Mail className="h-5 w-5 text-white" />
                </div>
                <h2 className="text-xl font-semibold text-cosmic-txt-1">Email Management</h2>
              </div>

              <div className="space-y-4">
                <div className="p-4 bg-cosmic-bg-2 rounded-xl border border-cosmic-border">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-semibold text-cosmic-txt-1">Email Address</label>
                    {!isEditingEmail && (
                        <button
                            onClick={() => setIsEditingEmail(true)}
                            className="text-blue-500 hover:text-blue-400 transition-colors flex items-center gap-1 text-sm"
                        >
                          <Edit2 size={14} />
                          <span>Edit</span>
                        </button>
                    )}
                  </div>

                  {isEditingEmail ? (
                      <div className="space-y-3">
                        <input
                            type="email"
                            value={newEmail}
                            onChange={(e) => setNewEmail(e.target.value)}
                            placeholder="Enter your email"
                            className="w-full px-4 py-3 bg-cosmic-bg-1 border border-cosmic-border rounded-xl text-cosmic-txt-1 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                        />
                        <div className="flex gap-2">
                          <Button
                              onClick={handleUpdateEmail}
                              loading={updatingEmail}
                              disabled={updatingEmail || !newEmail}
                              size="sm"
                              variant="primary"
                              className="flex-1"
                          >
                            {updatingEmail ? 'Updating...' : 'Update Email'}
                          </Button>
                          <Button
                              onClick={() => {
                                setIsEditingEmail(false);
                                setNewEmail(emailData.email);
                              }}
                              size="sm"
                              variant="ghost"
                              className="flex-1"
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                  ) : (
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-cosmic-txt-2">{emailData.email || 'No email set'}</span>
                          {emailData.emailVerified && (
                              <span className="flex items-center gap-1 text-green-500 text-sm">
                          <CheckCircle size={16} />
                          <span>Verified</span>
                        </span>
                          )}
                        </div>
                      </div>
                  )}
                </div>

                {!emailData.emailVerified && emailData.email && (
                    <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
                      <div className="flex items-start gap-3">
                        <AlertCircle className="text-yellow-500 flex-shrink-0 mt-0.5" size={20} />
                        <div className="flex-1">
                          <p className="text-sm font-semibold text-yellow-500 mb-1">Email Not Verified</p>
                          <p className="text-sm text-cosmic-txt-2 mb-3">
                            Please verify your email to enable notifications and receive important alerts.
                          </p>
                          <Button
                              onClick={handleSendVerificationEmail}
                              loading={sendingEmail}
                              disabled={sendingEmail}
                              size="sm"
                              variant="primary"
                              className="flex items-center gap-2"
                          >
                            {sendingEmail ? (
                                <>
                                  <div className="animate-spin rounded-full h-3 w-3 border-2 border-white border-t-transparent"></div>
                                  <span>Sending...</span>
                                </>
                            ) : (
                                <>
                                  <Send size={14} />
                                  <span>Send Verification Email</span>
                                </>
                            )}
                          </Button>
                        </div>
                      </div>
                    </div>
                )}

                {emailData.emailVerified && (
                    <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-xl">
                      <div className="flex items-center gap-3">
                        <CheckCircle className="text-green-500 flex-shrink-0" size={20} />
                        <div>
                          <p className="text-sm font-semibold text-green-500 mb-1">Email Verified</p>
                          <p className="text-sm text-cosmic-txt-2">
                            Your email has been verified. You can now enable notifications below.
                          </p>
                        </div>
                      </div>
                    </div>
                )}
              </div>
            </Card>

            {/* Notification Settings */}
            <Card className="animate-fade-in" style={{animationDelay: '0.2s'}}>
              <div className="flex items-center mb-6">
                <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-purple-600 rounded-xl flex items-center justify-center mr-3 shadow-cosmic-glow">
                  <Bell className="h-5 w-5 text-white" />
                </div>
                <h2 className="text-xl font-semibold text-cosmic-txt-1">Email Notifications</h2>
              </div>

              <div className="space-y-4">
                <div className="p-4 bg-cosmic-bg-2 rounded-xl border border-cosmic-border hover:border-blue-500/50 transition-all">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <label className="text-sm font-semibold text-cosmic-txt-1 block mb-1">
                        Enable Email Notifications
                      </label>
                      <p className="text-sm text-cosmic-txt-2">
                        {emailData.emailVerified
                            ? 'Receive security alerts and updates via email'
                            : 'Please verify your email first to enable notifications'}
                      </p>
                    </div>
                    <div className="ml-4">
                      <label className={`inline-flex items-center cursor-pointer ${
                          !emailData.emailVerified || togglingNotification ? 'opacity-50 cursor-not-allowed' : ''
                      }`}>
                        <input
                            type="checkbox"
                            className="sr-only peer"
                            checked={emailData.notificationsEnabled}
                            disabled={!emailData.emailVerified || togglingNotification}
                            onChange={(e) => handleToggleNotifications(e.target.checked)}
                        />
                        <div className="relative w-11 h-6 bg-gray-600 rounded-full peer
                        peer-focus:ring-4 peer-focus:ring-blue-800
                        peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full
                        peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px]
                        after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full
                        after:h-5 after:w-5 after:transition-all
                        peer-checked:bg-blue-600">
                        </div>
                        <span className="select-none ms-3 text-sm font-medium text-cosmic-txt-1">
                        {emailData.notificationsEnabled ? 'On' : 'Off'}
                      </span>
                      </label>
                    </div>
                  </div>
                </div>

                {emailData.notificationsEnabled && emailData.emailVerified && (
                    <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl">
                      <p className="text-sm font-semibold text-blue-500 mb-2">Active Notifications</p>
                      <ul className="text-sm text-cosmic-txt-2 space-y-1 ml-4">
                        <li className="list-disc">Critical security alerts (GuardDuty findings)</li>
                        <li className="list-disc">Daily health summaries</li>
                        <li className="list-disc">Cost anomalies and threshold alerts</li>
                        <li className="list-disc">Resource status changes</li>
                      </ul>
                    </div>
                )}
              </div>
            </Card>

            {/* Dashboard Settings - Frontend Only */}
            <Card className="animate-fade-in" style={{animationDelay: '0.3s'}}>
              <div className="flex items-center mb-6">
                <div className="w-10 h-10 bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-xl flex items-center justify-center mr-3 shadow-cosmic-glow">
                  <Palette className="h-5 w-5 text-white" />
                </div>
                <h2 className="text-xl font-semibold text-cosmic-txt-1">Dashboard</h2>
              </div>

              <div className="space-y-4">
                {/* Auto Refresh Toggle */}
                <div className="p-4 bg-cosmic-bg-2 rounded-xl border border-cosmic-border hover:border-blue-500/50 transition-all">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-semibold text-cosmic-txt-1 block mb-1">
                        Auto Refresh
                      </label>
                      <p className="text-sm text-cosmic-txt-2">
                        Automatically refresh dashboard data
                      </p>
                    </div>
                    <div className="ml-4">
                      <label className="inline-flex items-center cursor-pointer">
                        <input
                            type="checkbox"
                            className="sr-only peer"
                            checked={dashboardSettings.autoRefresh}
                            onChange={(e) => handleDashboardSettingChange('autoRefresh', e.target.checked)}
                        />
                        <div className="relative w-11 h-6 bg-gray-600 rounded-full peer
                        peer-focus:ring-4 peer-focus:ring-blue-800
                        peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full
                        peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px]
                        after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full
                        after:h-5 after:w-5 after:transition-all
                        peer-checked:bg-blue-600">
                        </div>
                        <span className="select-none ms-3 text-sm font-medium text-cosmic-txt-1">
                        {dashboardSettings.autoRefresh ? 'On' : 'Off'}
                      </span>
                      </label>
                    </div>
                  </div>
                </div>

                {/* Refresh Interval - Only show when autoRefresh is enabled */}
                {dashboardSettings.autoRefresh && (
                    <div className="p-4 bg-cosmic-bg-2 rounded-xl border border-cosmic-border">
                      <label className="block text-sm font-semibold text-cosmic-txt-1 mb-3">
                        Refresh Interval
                      </label>
                      <select
                          value={dashboardSettings.refreshInterval}
                          onChange={(e) => handleDashboardSettingChange('refreshInterval', parseInt(e.target.value))}
                          className="w-full px-4 py-3 bg-cosmic-bg-1 border border-cosmic-border rounded-xl text-cosmic-txt-1 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all cursor-pointer"
                      >
                        <option value={60}>1 minute</option>
                        <option value={120}>2 minutes</option>
                        <option value={300}>5 minutes</option>
                        <option value={600}>10 minutes</option>
                        <option value={900}>15 minutes</option>
                        <option value={1800}>30 minutes</option>
                      </select>
                    </div>
                )}

                {/* Default Time Range */}
                <div className="p-4 bg-cosmic-bg-2 rounded-xl border border-cosmic-border">
                  <label className="block text-sm font-semibold text-cosmic-txt-1 mb-3">
                    Default Time Range
                  </label>
                  <select
                      value={dashboardSettings.defaultTimeRange}
                      onChange={(e) => handleDashboardSettingChange('defaultTimeRange', e.target.value)}
                      className="w-full px-4 py-3 bg-cosmic-bg-1 border border-cosmic-border rounded-xl text-cosmic-txt-1 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all cursor-pointer"
                  >
                    <option value="1h">Last Hour</option>
                    <option value="24h">Last 24 Hours</option>
                    <option value="7d">Last 7 Days</option>
                    <option value="30d">Last 30 Days</option>
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