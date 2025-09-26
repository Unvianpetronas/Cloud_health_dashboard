import React, { useState } from 'react';
import { Settings as SettingsIcon, Save, User, Bell, Shield, Palette } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/common/Header';
import Card from '../components/common/Card';
import Button from '../components/common/Button';

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
      refreshInterval: 300, // 5 minutes
      theme: 'light',
      defaultTimeRange: '24h'
    },
    security: {
      sessionTimeout: 3600, // 1 hour
      requireReauth: false
    }
  });

  const [saving, setSaving] = useState(false);

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
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setSaving(false);
    // Show success message
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header title="Settings" showNavigation={true} />
      
      <main className="p-6 max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Settings</h1>
          <p className="text-gray-600">Manage your dashboard preferences and account settings</p>
        </div>

        <div className="space-y-6">
          {/* Account Information */}
          <Card>
            <div className="flex items-center mb-4">
              <User className="h-5 w-5 text-gray-500 mr-2" />
              <h2 className="text-lg font-semibold text-gray-900">Account Information</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  AWS Access Key ID
                </label>
                <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
                  {user?.accessKey ? `${user.accessKey.substring(0, 8)}...` : 'Not available'}
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
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Critical Alerts</label>
                  <p className="text-sm text-gray-500">Always notify for critical issues</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.notifications.critical}
                  onChange={(e) => handleSettingChange('notifications', 'critical', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">Warning Alerts</label>
                  <p className="text-sm text-gray-500">Notify for warning level issues</p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.notifications.warning}
                  onChange={(e) => handleSettingChange('notifications', 'warning', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </div>
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

          {/* Save Button */}
          <div className="flex justify-end">
            <Button
              onClick={handleSave}
              loading={saving}
              variant="primary"
              size="lg"
              className="flex items-center space-x-2"
            >
              <Save size={16} />
              <span>Save Settings</span>
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Settings;