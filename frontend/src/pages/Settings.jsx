import React, { useState, useEffect } from 'react';
import { Save, User, Bell, Shield, Palette, Mail } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/common/Header';
import Card from '../components/common/Card';
import Button from '../components/common/Button';
import Toast from '../components/common/Toast';
import { settingsApi } from '../services/settingsApi';
import logger from '../utils/logger';

const Settings = () => {
  const { user } = useAuth();
  const [settings, setSettings] = useState({
    notifications: {
      email: true,
      push: false,
      critical: true,
      warning: true,
      info: false
    },
    dashboard: {
      autoRefresh: true,
      refreshInterval: 300,
      theme: 'dark',
      defaultTimeRange: '24h'
    },
    security: {
      sessionTimeout: 3600,
      requireReauth: false
    }
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [sendingEmail, setSendingEmail] = useState(false);
  const [toast, setToast] = useState(null);

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    const result = await settingsApi.getSettings();

    if (result.success) {
      setSettings(result.data);
      logger.info('Settings loaded successfully');
    } else {
      showToast(result.error, 'error');
      logger.error('Failed to load settings:', result.error);
    }

    setLoading(false);
  };

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
  };

  const hideToast = () => {
    setToast(null);
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

  const handleSave = async () => {
    setSaving(true);

    const result = await settingsApi.updateSettings(settings);

    if (result.success) {
      showToast('Settings saved successfully!', 'success');
      logger.info('Settings saved');
    } else {
      showToast(result.error, 'error');
      logger.error('Failed to save settings:', result.error);
    }

    setSaving(false);
  };

  const handleSendTestEmail = async () => {
    setSendingEmail(true);

    const result = await settingsApi.sendTestEmail();

    if (result.success) {
      showToast(result.message, 'success');
      logger.info('Test email sent');
    } else {
      showToast(result.error, 'error');
      logger.error('Failed to send test email:', result.error);
    }

    setSendingEmail(false);
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

        {/* Toast Notifications */}
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

          {/* Notification Settings */}
          <Card className="animate-fade-in" style={{animationDelay: '0.1s'}}>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-purple-600 rounded-xl flex items-center justify-center mr-3 shadow-cosmic-glow">
                  <Bell className="h-5 w-5 text-white" />
                </div>
                <h2 className="text-xl font-semibold text-cosmic-txt-1">Notifications</h2>
              </div>
              <Button
                onClick={handleSendTestEmail}
                disabled={sendingEmail}
                variant="ghost"
                size="sm"
                className="flex items-center space-x-2"
              >
                {sendingEmail ? (
                  <>
                    <div className="animate-spin rounded-full h-3 w-3 border-2 border-blue-500 border-t-transparent"></div>
                    <span>Sending...</span>
                  </>
                ) : (
                  <>
                    <Mail size={14} />
                    <span>Send Test Email</span>
                  </>
                )}
              </Button>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-cosmic-bg-2 rounded-xl border border-cosmic-border hover:border-blue-500/50 transition-all">
                <div>
                  <label className="text-sm font-semibold text-cosmic-txt-1 block mb-1">Email Notifications</label>
                  <p className="text-sm text-cosmic-txt-2">Receive alerts via email</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.notifications.email}
                  onChange={(e) => handleSettingChange('notifications', 'email', e.target.checked)}
                  className="h-5 w-5 text-blue-500 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 bg-cosmic-bg-2 border-cosmic-border rounded cursor-pointer"
                />
              </div>

              <div className="flex items-center justify-between p-4 bg-cosmic-bg-2 rounded-xl border border-cosmic-border hover:border-red-500/50 transition-all">
                <div>
                  <label className="text-sm font-semibold text-cosmic-txt-1 block mb-1">Critical Alerts</label>
                  <p className="text-sm text-cosmic-txt-2">Always notify for critical issues</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.notifications.critical}
                  onChange={(e) => handleSettingChange('notifications', 'critical', e.target.checked)}
                  className="h-5 w-5 text-red-500 focus:ring-2 focus:ring-red-500 focus:ring-offset-0 bg-cosmic-bg-2 border-cosmic-border rounded cursor-pointer"
                />
              </div>

              <div className="flex items-center justify-between p-4 bg-cosmic-bg-2 rounded-xl border border-cosmic-border hover:border-yellow-500/50 transition-all">
                <div>
                  <label className="text-sm font-semibold text-cosmic-txt-1 block mb-1">Warning Alerts</label>
                  <p className="text-sm text-cosmic-txt-2">Notify for warning level issues</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.notifications.warning}
                  onChange={(e) => handleSettingChange('notifications', 'warning', e.target.checked)}
                  className="h-5 w-5 text-yellow-500 focus:ring-2 focus:ring-yellow-500 focus:ring-offset-0 bg-cosmic-bg-2 border-cosmic-border rounded cursor-pointer"
                />
              </div>
            </div>
          </Card>

          {/* Dashboard Settings */}
          <Card className="animate-fade-in" style={{animationDelay: '0.2s'}}>
            <div className="flex items-center mb-6">
              <div className="w-10 h-10 bg-gradient-to-r from-cyan-500 to-cyan-600 rounded-xl flex items-center justify-center mr-3 shadow-cosmic-glow">
                <Palette className="h-5 w-5 text-white" />
              </div>
              <h2 className="text-xl font-semibold text-cosmic-txt-1">Dashboard</h2>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-cosmic-bg-2 rounded-xl border border-cosmic-border hover:border-blue-500/50 transition-all">
                <div>
                  <label className="text-sm font-semibold text-cosmic-txt-1 block mb-1">Auto Refresh</label>
                  <p className="text-sm text-cosmic-txt-2">Automatically refresh dashboard data</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.dashboard.autoRefresh}
                  onChange={(e) => handleSettingChange('dashboard', 'autoRefresh', e.target.checked)}
                  className="h-5 w-5 text-blue-500 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 bg-cosmic-bg-2 border-cosmic-border rounded cursor-pointer"
                />
              </div>

              <div className="p-4 bg-cosmic-bg-2 rounded-xl border border-cosmic-border">
                <label className="block text-sm font-semibold text-cosmic-txt-1 mb-3">
                  Refresh Interval
                </label>
                <select
                  value={settings.dashboard.refreshInterval}
                  onChange={(e) => handleSettingChange('dashboard', 'refreshInterval', parseInt(e.target.value))}
                  className="w-full px-4 py-3 bg-cosmic-bg-1 border border-cosmic-border rounded-xl text-cosmic-txt-1 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all cursor-pointer"
                >
                  <option value={60}>1 minute</option>
                  <option value={300}>5 minutes</option>
                  <option value={600}>10 minutes</option>
                  <option value={1800}>30 minutes</option>
                </select>
              </div>

              <div className="p-4 bg-cosmic-bg-2 rounded-xl border border-cosmic-border">
                <label className="block text-sm font-semibold text-cosmic-txt-1 mb-3">
                  Default Time Range
                </label>
                <select
                  value={settings.dashboard.defaultTimeRange}
                  onChange={(e) => handleSettingChange('dashboard', 'defaultTimeRange', e.target.value)}
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

          {/* Security Settings */}
          <Card className="animate-fade-in" style={{animationDelay: '0.3s'}}>
            <div className="flex items-center mb-6">
              <div className="w-10 h-10 bg-gradient-to-r from-red-500 to-red-600 rounded-xl flex items-center justify-center mr-3 shadow-cosmic-glow">
                <Shield className="h-5 w-5 text-white" />
              </div>
              <h2 className="text-xl font-semibold text-cosmic-txt-1">Security</h2>
            </div>

            <div className="space-y-4">
              <div className="p-4 bg-cosmic-bg-2 rounded-xl border border-cosmic-border">
                <label className="block text-sm font-semibold text-cosmic-txt-1 mb-3">
                  Session Timeout
                </label>
                <select
                  value={settings.security.sessionTimeout}
                  onChange={(e) => handleSettingChange('security', 'sessionTimeout', parseInt(e.target.value))}
                  className="w-full px-4 py-3 bg-cosmic-bg-1 border border-cosmic-border rounded-xl text-cosmic-txt-1 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all cursor-pointer"
                >
                  <option value={1800}>30 minutes</option>
                  <option value={3600}>1 hour</option>
                  <option value={7200}>2 hours</option>
                  <option value={14400}>4 hours</option>
                </select>
              </div>
            </div>
          </Card>

          {/* Save Button */}
          <div className="flex justify-end animate-fade-in" style={{animationDelay: '0.4s'}}>
            <Button
              onClick={handleSave}
              loading={saving}
              disabled={saving}
              variant="primary"
              size="lg"
              className="flex items-center space-x-2 min-w-[180px] justify-center"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save size={18} />
                  <span>Save Settings</span>
                </>
              )}
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Settings;
