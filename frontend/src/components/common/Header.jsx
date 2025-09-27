import React, { useState, useEffect } from 'react';
import { Cloud, RefreshCw, LogOut, User } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import Button from './Button';
import Navigation from './Navigation';

const Header = ({ 
  title = "AWS Cloud Health Dashboard",
  onRefresh,
  refreshing = false,
  selectedTimeRange = '24h',
  onTimeRangeChange,
  showNavigation = true
}) => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const { user, logout } = useAuth();

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const timeRangeOptions = [
    { value: '1h', label: 'Last Hour' },
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' }
  ];

  return (
    <div>
      <header className="navbar mx-6 mt-4 mb-2">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <div className="bg-gradient-to-r from-blue-500 to-blue-600 p-2 rounded-xl shadow-cosmic-glow">
              <Cloud size={28} className="text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-cosmic-txt-1">
                {title}
              </h1>
              <div className="badge mt-1 animate-fade-in">
                ✨ New Features Available
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {onTimeRangeChange && (
              <select
                value={selectedTimeRange}
                onChange={(e) => onTimeRangeChange?.(e.target.value)}
                className="px-3 py-2 border border-cosmic-border rounded-xl bg-cosmic-card text-cosmic-txt-1 text-sm focus-ring backdrop-blur-cosmic"
              >
                {timeRangeOptions.map(option => (
                  <option key={option.value} value={option.value} className="bg-cosmic-bg-1">
                    {option.label}
                  </option>
                ))}
              </select>
            )}

            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={refreshing}
                className="btn btn-primary flex items-center space-x-2 text-sm"
              >
                <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
                <span>Refresh</span>
              </button>
            )}

            {onRefresh && (
              <div className="text-sm text-cosmic-txt-2">
                Last updated: {currentTime.toLocaleTimeString()}
              </div>
            )}

            {/* User Menu */}
            <div className="flex items-center space-x-2 pl-4 border-l border-cosmic-border">
              <div className="flex items-center space-x-2">
                <User size={16} className="text-cosmic-muted" />
                <span className="text-sm text-cosmic-txt-2">
                  {user?.accessKey ? `${user.accessKey.substring(0, 8)}...` : 'User'}
                </span>
              </div>
              <button
                onClick={logout}
                className="btn btn-ghost flex items-center space-x-2 text-sm"
              >
                <LogOut size={16} />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>
      
      {showNavigation && <Navigation />}
    </div>
  );
};

export default Header;